"""What a GET answers — including `/health`, which was the one GET that bypassed the reply shape.

WHAT: `reply_for(path, cookies, settings)` returns a `routes.Reply` for every GET this endpoint
      serves. The socket layer writes it; nothing here touches one.
WHY:  **`serve/listener.py` REACHED THE 200-LINE CAP AGAIN AND THIS IS THE RIGHT SEAM.**
      `AGENTS.md` rule 4: split by concern, do not raise the cap. The concern is *what a GET
      answers*, which `serve/web/routes.py` already owns for every path except one.

      **`/health` WAS THAT ONE, AND FOLDING IT IN IS A REAL FIX RATHER THAN A LINE COUNT.** Every
      other GET produced a `Reply` -- status, headers, body -- that a test can assert on without a
      socket. Health alone wrote itself through the handler's own JSON helper, so the only way to
      exercise it was to bind a port. It now returns the same shape as everything else and is
      testable the same way.

      **THE BYTES DO NOT CHANGE.** Same status, same `{"ok": ..., "detail": ...}` body, same
      `application/json`. This is a move, and a move that altered a health check's output would be
      the kind of silent change the endpoint exists to report.
IMPORTS: serve.{health,web.routes}. Same layer, public surface only.
CONSUMED BY: `serve/listener.py`.
"""

from __future__ import annotations

import json

from quantamind.serve.health import health
from quantamind.serve.web.routes import JSON, Reply, get
from quantamind.types.settings import Settings

HEALTH_PATH = "/health"


def reply_for(path: str, cookies: str, settings: Settings) -> Reply:
    """The reply for one GET. Never raises: a browser gets a page, not a stack trace."""
    if path == HEALTH_PATH:
        verdict = health(settings.database_path)
        return Reply(
            200 if verdict.ok else 503,
            json.dumps({"ok": verdict.ok, "detail": verdict.detail}),
            kind=JSON,
        )
    return get(path, cookies, settings)
