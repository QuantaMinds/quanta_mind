"""What the endpoint does when something is wrong with US, not with the caller.

WHAT: Three properties the response table in `docs/engineering/CLI.md` claims and nothing else
      asserted: an unroutable delivery answers `ignored` rather than erroring, a fault inside the
      handler answers 500 rather than dropping the socket, and `build()` refuses every secret
      `verify()` would raise on.
WHY:  **The last one replaces an UNREACHABLE branch.** `_post` used to catch `MisconfiguredSecret`
      from `verify()` and answer 500. It could never run: `verify()` raises only on an empty
      secret, and `build()` refuses `not secret.strip()`, which is strictly stronger. A handler
      guarding a state that cannot be reached returns the same thing whether or not it works --
      rule 14's defect exactly -- and the CLI reference documented a status code no request could
      produce. The invariant that made it unreachable is asserted here instead, so a future widening
      of `verify()`'s raise condition fails a test rather than silently reopening the hole.

      **The 500 case is tested through a real fault, not a patched method.** The store path is a
      directory, which is what a deploy pointed at the wrong place produces; sqlite raises inside
      the handler. Left uncaught the stdlib closes the socket with NO response, which GitHub
      records as a failed delivery with no status -- the least diagnosable outcome there is.
IMPORTS: quantamind.serve.{listener,webhook_github}; the fixtures from `test_listener`.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import http.client
import json
from pathlib import Path

import pytest

# `server` is re-exported so pytest collects it as a fixture here; the `x as x` form is what
# tells ruff the import is deliberate, and the parameter below shadowing the name is how every
# pytest fixture looks.
from test_listener import PAYLOAD, SECRET, _headers, _post, _Server, _Settings
from test_listener import server as server

from quantamind.serve import listener
from quantamind.serve.http import bind
from quantamind.serve.webhook_github import MisconfiguredSecret, sign, verify


def test_an_unactionable_delivery_is_ignored_with_a_reason_not_an_error(server: _Server) -> None:
    """A ping and a label change are normal traffic; erroring on them fills a log nobody reads."""
    body = json.dumps({"zen": "keep it logically awesome"}).encode()
    headers = _headers(body, "guid-ping")
    headers["X-GitHub-Event"] = "ping"

    status, answer = _post(server.port, body, headers)

    assert status == 200, f"an authentic ping was not answered 200: {answer}"
    assert "ignored" in answer, f"a ping must say why it was ignored, not merely succeed: {answer}"
    assert server.seen == [], "a ping reached the work callback"


def test_a_fault_inside_the_handler_answers_500_rather_than_dropping_the_socket(
    tmp_path: Path,
) -> None:
    """An unhandled exception closes the connection with no status at all. That must not happen."""
    import threading

    # **A FILE where the store ROOT should be**, which is what a deploy pointed at the wrong path
    # produces. This used to pass a DIRECTORY, because `database_path` was once a single database
    # file -- and once each repository got its own store the directory became CORRECT, so the test
    # provoked no fault at all and asserted 500 against a healthy 202. The fault has to be
    # something the current contract still rejects: `<file>/deliveries.db` cannot be opened.
    wrong = tmp_path / "not-a-directory"
    wrong.write_text("")
    built = bind.build(_Settings(str(wrong)), SECRET, lambda _r: None, port=0)
    thread = threading.Thread(target=built.serve_forever, daemon=True)
    thread.start()
    try:
        status, answer = _post(built.server_address[1], PAYLOAD, _headers(PAYLOAD, "guid-fault"))
    finally:
        built.shutdown()
        built.server_close()

    assert status == 500, f"a fault in the handler did not answer 500: {status} {answer}"
    assert "error" in answer, f"a 500 must name the fault, not answer empty: {answer}"


@pytest.mark.parametrize("secret", ["", " ", "\t\n", "   "])
def test_build_refuses_every_secret_verify_would_raise_on(secret: str, tmp_path: Path) -> None:
    """The invariant that made the handler's `MisconfiguredSecret` branch unreachable.

    Asserted from both sides: `verify()` raises on it, AND `build()` refuses it. If someone widens
    `verify()` to raise on a secret `build()` accepts, the second half of this fails and the gap is
    visible before it ships, rather than becoming a dropped socket in production.
    """
    with pytest.raises(MisconfiguredSecret):
        # `verify()` raises on an empty secret; `.strip()` is what makes whitespace one too.
        verify(secret.strip(), b"{}", sign("k", b"{}"))
    with pytest.raises(MisconfiguredSecret) as refused:
        bind.build(_Settings(str(tmp_path)), secret, lambda _r: None, port=0)

    assert "open command channel" in str(refused.value)


def test_a_get_that_raises_answers_500_rather_than_dropping_the_connection(
    server: _Server, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`do_POST` had this guard and `do_GET` did not, so a browser got no status at all.

    Visiting `/` before any account store existed raised `sqlite3.OperationalError` into the
    stdlib handler, which closes the socket silently. A visitor cannot report that and an operator
    cannot see it — the least diagnosable outcome available, and the reasoning was already written
    on `do_POST` and simply never applied here.
    """

    def _explode(*_: object, **__: object) -> object:
        raise RuntimeError("the route blew up")

    monkeypatch.setattr(listener.routes, "get", _explode)

    conn = http.client.HTTPConnection("127.0.0.1", server.port, timeout=10)
    conn.request("GET", "/")
    response = conn.getresponse()
    status, body = response.status, response.read()
    conn.close()

    assert status == 500, f"a raising GET must still answer, got {status}"
    assert b"RuntimeError" in body, f"the answer must name the fault, got {body!r}"
