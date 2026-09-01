"""The `/health` route's WIRING: that it reads the verdict, not merely that it answers something.

WHAT: Binds the real server on two roots -- one healthy, one holding a tenant store that is not a
      database -- and asserts the exact status and body each returns. The pair is the point: one
      status alone is satisfied by a route that ignores the verdict and hardcodes that status.
WHY:  **THE VERDICT WAS COVERED AND THE WIRING WAS NOT.** `test_serve_health.py` proves `health()`
      decides correctly. Nothing proved the endpoint consults it. Verified by sabotage in both
      directions: rewriting the route to `self._say(503, ...)` and to `self._say(200, ...)` each
      left all 690 unit tests passing. An orchestrator reads this endpoint to decide whether an
      instance stays in rotation, so a route hardcoding 200 keeps a store with a schema mismatch
      serving reviews -- silently, which is the one failure mode this codebase refuses.

      **THE ASSERTION THIS REPLACES ACCEPTED BOTH ANSWERS.** `status in (200, 503)` cannot fail:
      those are the only two statuses the route can emit. Ask what a check prints when the thing it
      checks is broken; if the answer is "the same thing", it is not a check.
IMPORTS: quantamind.serve.listener, quantamind.serve.http.bind, quantamind.store.tenancy; stdlib
      http.client, json, threading. Nothing to the right of `serve`.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import contextlib
import http.client
import json
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from quantamind.serve import listener
from quantamind.serve.http import bind
from quantamind.serve.webhook_github import Review
from quantamind.store import tenancy

SECRET = "a-real-secret"


@dataclass
class _Settings:
    database_path: str


def _idle(review: Review) -> None:
    """A plain function, not a builtin method -- see the note in `test_listener.py`'s fixture."""


@contextlib.contextmanager
def _serving(root: Path) -> Iterator[int]:
    """The real `ThreadingHTTPServer` on an ephemeral port, over `root`. Yields the port."""
    built = bind.build(_Settings(str(root)), SECRET, _idle, port=0)
    thread = threading.Thread(target=built.serve_forever, daemon=True)
    thread.start()
    try:
        yield int(built.server_address[1])
    finally:
        built.shutdown()
        built.server_close()


def _health(port: int) -> tuple[int, dict[str, object]]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("GET", listener.HEALTH_PATH)
    response = conn.getresponse()
    status, raw = response.status, response.read()
    conn.close()
    parsed = json.loads(raw)
    assert isinstance(parsed, dict), f"health must answer a JSON object, got {parsed!r}"
    return status, parsed


def test_a_writable_root_with_no_tenants_answers_exactly_200(tmp_path: Path) -> None:
    with _serving(tmp_path) as port:
        status, body = _health(port)

    assert status == 200, f"a writable root with no tenants is healthy, got {status}: {body}"
    assert body["ok"] is True, f"the body must agree with the status, got {body}"
    assert "no tenants yet" in str(body["detail"]), f"the detail must say why, got {body}"


def test_a_tenant_store_that_is_not_a_database_answers_exactly_503(tmp_path: Path) -> None:
    """The half that makes the pair load-bearing: the route must read `verdict.ok` to answer this.

    The junk sits where a TENANT store lives, not at the root -- `tenancy.tenants()` globs
    `<root>/<owner>/*.db` and never looks at the root, so a file written there reads as "no tenants,
    healthy" and this test would pass against a broken route for the wrong reason.
    """
    tenancy.store_for(tmp_path, "acme", "junk").write_bytes(b"this is not sqlite")

    with _serving(tmp_path) as port:
        status, body = _health(port)

    assert status == 503, f"a tenant store that will not open is not healthy, got {status}: {body}"
    assert body["ok"] is False, f"the body must agree with the status, got {body}"
    assert "acme/junk" in str(body["detail"]), (
        f"the detail must name the tenant an operator has to fix, got {body}"
    )
