"""Resource limits on the socket: what the endpoint refuses before it reads anything.

WHAT: Declares a Content-Length past the ceiling and asserts the refusal, without sending the
      bytes.
WHY:  Split from `test_listener.py` at the 200-line cap, and it is the right seam: everything
      there is about AUTHENTICATION -- who may be believed -- and this is about what may be
      consumed by someone who has not been believed yet. **Content-Length is attacker-controlled**,
      so a read with no ceiling is memory exhaustion handed to anyone who can reach the port, and
      the refusal must come BEFORE the body is read rather than after.
IMPORTS: quantamind.serve.listener; the fixtures from `test_listener`.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import http.client
import json

# `server` is imported for pytest to collect as a fixture; the parameter below shadows the name,
# which is how pytest fixtures always look and what F811 cannot distinguish.
from test_listener import PAYLOAD, _headers, _Server
from test_listener import server as server

from quantamind.serve import listener


def test_an_oversized_content_length_is_refused_before_the_body_is_read(server: _Server) -> None:
    """A read with no ceiling is memory exhaustion for anyone who can reach the port."""
    headers = _headers(PAYLOAD, "guid-big")
    headers["Content-Length"] = str(listener.MAX_BODY_BYTES + 1)

    conn = http.client.HTTPConnection("127.0.0.1", server.port, timeout=10)
    conn.putrequest("POST", listener.WEBHOOK_PATH)
    for key, value in headers.items():
        conn.putheader(key, value)
    conn.endheaders()
    conn.send(PAYLOAD)  # deliberately fewer bytes than we claimed
    status = conn.getresponse().status
    conn.close()

    assert status == 411, f"an oversized Content-Length was not refused: {status}"


def test_the_three_unusable_content_lengths_get_three_different_answers(server: _Server) -> None:
    """Absent, unparseable and oversized are three faults, and collapsing them costs the debugger.

    A missing header is a misconfigured proxy, a non-integer one is a malformed client and an
    oversized one may be an attack. `docs/engineering/CLI.md` claims the endpoint tells them apart;
    this is what holds that claim up. The distinctness is the assertion -- three 411s carrying one
    message would satisfy a status-code-only test while telling whoever reads the log nothing.
    """
    reasons = {}
    for label, declared in (("absent", None), ("unparseable", "twelve"), ("negative", "-1")):
        headers = _headers(PAYLOAD, f"guid-{label}")
        if declared is None:
            headers.pop("Content-Length")
        else:
            headers["Content-Length"] = declared

        conn = http.client.HTTPConnection("127.0.0.1", server.port, timeout=10)
        conn.putrequest("POST", listener.WEBHOOK_PATH, skip_accept_encoding=True)
        for key, value in headers.items():
            conn.putheader(key, value)
        conn.endheaders()
        response = conn.getresponse()
        status, raw = response.status, response.read()
        conn.close()

        assert status == 411, f"a {label} Content-Length was not refused: {status}"
        reasons[label] = json.loads(raw)["error"]

    assert len(set(reasons.values())) == 3, (
        f"the three refusals answer with fewer than three distinct reasons: {reasons}"
    )
