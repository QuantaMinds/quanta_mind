"""Reading a request body safely: exactly the declared length, and three distinct refusals.

WHAT: `read_body(handler)` returns `(body, reason)` — the bytes `Content-Length` declares, or
      `None` with which of three faults it was.
WHY:  **IT LEFT `serve/listener.py` WHEN THAT FILE HIT THE 200-LINE CAP AND THE SIGN-IN ROUTES HAD
      NOWHERE TO GO.** Shaving a comment for each new route is how a file's explanation erodes one
      line at a time; the plumbing is a separate concern from deciding what a path means, so it
      moved. `AGENTS.md` rule 4.

      **IT IS SHARED, NOT WEB-ONLY.** The webhook uses it too. This sub-package is the HTTP surface
      — how bytes become a request and a response — while `listener.py` keeps the socket and the
      routing decisions.
IMPORTS: stdlib only.
CONSUMED BY: `serve/listener.py`.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler

MAX_BODY_BYTES = 1_000_000
"""Ceiling on a declared body. A webhook payload is kilobytes; anything near this is not one."""


def read_body(handler: BaseHTTPRequestHandler) -> tuple[bytes | None, str]:
    """(body, reason). Exactly `Content-Length` bytes, or None with WHICH of three faults it was.

    Reading to EOF would hang on a client that never closes, and reading a different number of
    bytes than the signature covers turns an authentic delivery into a rejected one.

    **The three refusals are distinct values, not one.** An absent header, an unparseable one and
    an oversized one need different responses from whoever is debugging the 411 -- a
    misconfigured proxy, a malformed client and an attack look nothing alike, and collapsing them
    into a single message makes the endpoint answer the same way for all three.
    """
    raw = handler.headers.get("Content-Length")
    if raw is None:
        return None, "no Content-Length header; the body length must be declared"
    try:
        length = int(raw)
    except ValueError:
        return None, f"Content-Length {raw!r} is not an integer"
    if length < 0:
        return None, f"Content-Length {length} is negative"
    if length > MAX_BODY_BYTES:
        return None, f"Content-Length {length} exceeds the {MAX_BODY_BYTES}-byte ceiling"
    return handler.rfile.read(length), ""
