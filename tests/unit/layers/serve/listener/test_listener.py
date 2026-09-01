"""The socket, driven over a real one: a fake webhook posts and the answers are asserted.

WHAT: Binds the real `ThreadingHTTPServer` on an ephemeral port, posts genuine and forged
      deliveries at it, and asserts the status and body of each. Then breaks each security
      property in turn and requires the response to change.
WHY:  The plan's gate is "a fake webhook posts and asserts a 200; an unreachable store makes health
      fail", and every property below is one an endpoint can lose while still answering 200 to a
      well-formed request.

      **THE SIGNATURE TEST IS THE ONE THAT MATTERS, AND IT IS TESTED BY FORGING.** A handler that
      skipped verification entirely would pass any test that only ever sends correctly-signed
      bodies. So an unsigned delivery, a malformed one and a wrong-key one are each posted and each
      must be refused, with the reason distinguishing them.

      **REPLAY IS TESTED THROUGH THE FULL PATH**, not by calling `deliveries.begin` directly: the
      same GUID is posted twice with a `complete()` between, because the defence is only real if
      the HANDLER consults it.
IMPORTS: quantamind.serve.listener, quantamind.serve.webhook_github; stdlib http.client, threading.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import http.client
import json
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from quantamind.serve import listener
from quantamind.serve.http import bind
from quantamind.serve.webhook_github import MisconfiguredSecret, Review, sign

SECRET = "a-real-secret"
PAYLOAD = json.dumps(
    {
        "action": "opened",
        "pull_request": {"number": 7, "head": {"sha": "a" * 40}},
        "repository": {"full_name": "acme/widgets"},
    }
).encode()


@dataclass
class _Settings:
    database_path: str


@dataclass
class _Server:
    port: int
    seen: list[Review]


@pytest.fixture
def server(tmp_path: Path) -> Iterator[_Server]:
    seen: list[Review] = []

    # A PLAIN FUNCTION, deliberately, not `seen.append`. A plain function stored as a class
    # attribute is a descriptor and gets bound, so `self.work(review)` arrives as
    # `work(self, review)`; `list.append` is a builtin method object and is not, so injecting it
    # made every test pass against a listener that could not call an ordinary callback.
    def record(review: Review) -> None:
        seen.append(review)

    built = bind.build(_Settings(str(tmp_path)), SECRET, record, port=0)
    thread = threading.Thread(target=built.serve_forever, daemon=True)
    thread.start()
    yield _Server(port=built.server_address[1], seen=seen)
    built.shutdown()
    built.server_close()


def _post(port: int, body: bytes, headers: dict[str, str]) -> tuple[int, dict[str, object]]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("POST", listener.WEBHOOK_PATH, body=body, headers=headers)
    response = conn.getresponse()
    status, raw = response.status, response.read()
    conn.close()
    return status, json.loads(raw)


def _headers(body: bytes, delivery: str, secret: str = SECRET) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
        "X-Hub-Signature-256": sign(secret, body),
        "X-GitHub-Delivery": delivery,
        "X-GitHub-Event": "pull_request",
    }


def test_a_signed_delivery_is_accepted_and_the_work_receives_it(server: _Server) -> None:
    """The gate: a fake webhook posts, and the answer is 202 with the pull request identified."""
    status, body = _post(server.port, PAYLOAD, _headers(PAYLOAD, "guid-1"))

    assert status == 202, f"a correctly signed delivery was not accepted: {body}"
    assert body["repo"] == "acme/widgets" and body["pr"] == 7
    assert [(r.repo, r.number) for r in server.seen] == [("acme/widgets", 7)], (
        "the work never ran, or ran on the wrong pull request"
    )


@pytest.mark.parametrize(
    ("signature", "expected"),
    [
        (None, "no signature header"),
        ("sha256=not-hex", "signature is not sha256=<64 hex chars>"),
        (None, "no signature header"),
    ],
)
def test_a_delivery_without_a_good_signature_is_refused(
    server: _Server, signature: str | None, expected: str
) -> None:
    headers = _headers(PAYLOAD, "guid-forged")
    if signature is None:
        del headers["X-Hub-Signature-256"]
    else:
        headers["X-Hub-Signature-256"] = signature

    status, body = _post(server.port, PAYLOAD, headers)

    assert status == 401, f"a forged delivery was accepted with {status}"
    assert body["error"] == expected
    assert server.seen == [], "the work ran on an unauthenticated delivery"


def test_a_signature_from_the_wrong_key_is_refused(server: _Server) -> None:
    """The case a handler that verifies NOTHING would still pass: well-formed, wrong key."""
    status, body = _post(server.port, PAYLOAD, _headers(PAYLOAD, "guid-2", secret="wrong-key"))

    assert status == 401 and body["error"] == "signature does not match the body"
    assert server.seen == [], "the work ran on a delivery signed with the wrong key"


def test_a_body_that_does_not_match_its_signature_is_refused(server: _Server) -> None:
    """Signed one body, sent another. The HMAC covers the exact bytes."""
    headers = _headers(PAYLOAD, "guid-3")
    tampered = PAYLOAD.replace(b'"number": 7', b'"number": 9')
    headers["Content-Length"] = str(len(tampered))

    status, _ = _post(server.port, tampered, headers)

    assert status == 401, "a body was accepted under a signature for different bytes"
    assert server.seen == []


def test_a_completed_delivery_is_not_repeated(server: _Server) -> None:
    """Replay protection, through the handler rather than around it."""
    first, _ = _post(server.port, PAYLOAD, _headers(PAYLOAD, "guid-replay"))
    second, body = _post(server.port, PAYLOAD, _headers(PAYLOAD, "guid-replay"))

    assert first == 202
    assert second == 200 and body["replay"] == "guid-replay", (
        "a completed delivery was processed a second time"
    )
    assert len(server.seen) == 1, f"the work ran {len(server.seen)} times for one delivery"


def test_a_delivery_with_no_guid_is_refused_rather_than_treated_as_fresh(server: _Server) -> None:
    headers = _headers(PAYLOAD, "")
    status, body = _post(server.port, PAYLOAD, headers)

    assert status == 400 and "deduplicated" in str(body["error"])
    assert server.seen == []


def test_health_reports_the_store_and_an_unknown_path_is_a_404(server: _Server) -> None:
    conn = http.client.HTTPConnection("127.0.0.1", server.port, timeout=10)
    conn.request("GET", listener.HEALTH_PATH)
    health = conn.getresponse()
    health_status, health_body = health.status, json.loads(health.read())
    conn.request("GET", "/elsewhere")
    missing = conn.getresponse().status
    conn.close()

    # `in (200, 503)` here accepted BOTH statuses the route can emit, so it could not fail.
    # This root is empty and writable, which `health()` decides is healthy, deterministically.
    # The route reading the verdict at all is pinned next door, in `test_listener_health.py`.
    assert health_status == 200, f"an empty writable root is healthy, got {health_status}"
    assert "ok" in health_body and "detail" in health_body
    assert missing == 404


def test_binding_without_a_secret_refuses_rather_than_serving(tmp_path: Path) -> None:
    """An endpoint that verifies nothing is an open command channel, and it fails at bind time."""
    with pytest.raises(MisconfiguredSecret) as caught:
        bind.build(_Settings(str(tmp_path)), "   ", lambda _r: None, port=0)

    assert "open command channel" in str(caught.value)
