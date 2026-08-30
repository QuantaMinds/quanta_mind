"""Bind a server: the address it listens on, and the refusal when it cannot verify anything.

WHAT: `build(settings, secret, work, port, host)` returns a `ThreadingHTTPServer` ready for
      `serve_forever()`, and `LOOPBACK`, the default address.
WHY:  Split from `serve/listener.py`, which decides what a REQUEST means -- routes, signatures,
      replay refusal. Binding an address is a different concern and the file was one line under the
      200 cap, so adding a `host` parameter to it had nowhere to go. Trimming the comments already
      there to make room would have traded a recorded lesson for a feature.
IMPORTS: stdlib, plus the handler and secret error from `serve.listener`. Same layer, public
      surface only.
CONSUMED BY: `serve/commands/run_endpoint.py`.
"""

from __future__ import annotations

from http.server import ThreadingHTTPServer
from typing import Any

from quantamind.serve.listener import Work, _Handler
from quantamind.serve.webhook_github import MisconfiguredSecret

# The default bind. Inside a container LOOPBACK is the container, so the image asks for 0.0.0.0
# explicitly; defaulting to it would expose a developer's endpoint to their network unasked.
LOOPBACK = "127.0.0.1"


def build(
    settings: Any, secret: str, work: Work, port: int = 7331, host: str = LOOPBACK
) -> ThreadingHTTPServer:
    """A server ready for `serve_forever()`. Binds immediately, so a port clash fails here.

    `work` is injected rather than imported: the socket layer can then be exercised without running
    a ranking, and it never reaches rightward into a pipeline it has no business knowing about.

    `host` defaults to loopback and must be asked for to leave it -- see `LOOPBACK`.
    """
    if not secret.strip():
        raise MisconfiguredSecret(
            "no webhook secret: refusing to bind. An endpoint that verifies nothing is an open "
            "command channel, and it would pass every test that supplies a secret."
        )
    # **`staticmethod`, and it is not decoration.** A plain function stored as a class attribute is
    # a descriptor: Python binds it and `self.work(review)` arrives as `work(self, review)`. The
    # first version failed exactly that way against `serve/cli.py` while the unit tests passed --
    # they injected `list.append`, a BUILTIN bound method, which is not a descriptor and so was
    # never re-bound. **The test agreed for a reason unrelated to the property.**
    bound = type(
        "_Bound",
        (_Handler,),
        {"settings": settings, "secret": secret, "work": staticmethod(work)},
    )
    return ThreadingHTTPServer((host, port), bound)
