"""Which POST route a path is, and nothing about what any of them does.

WHAT: `route(handler)` returns `(status, payload)` for the three POST routes that are not the
      GitHub webhook, and `None` when the path is not one of them.
WHY:  **`serve/listener.py` SITS AT THE 200-LINE CAP AND THE THIRD ROUTE HAD NOWHERE TO GO.**
      `AGENTS.md` rule 4: split by concern, do not raise the cap. The concern split out is
      *which route is this*, which is genuinely separate from the socket work the listener does --
      reading a body by `Content-Length`, answering inside ten seconds, claiming a delivery.

      **THE GITHUB WEBHOOK IS DELIBERATELY NOT HERE.** It is the only POST that has to be
      authenticated, claimed against a replay ledger, answered, and only THEN worked -- the
      acknowledge-then-work shape `serve/listener.py` exists to hold. Moving it into a table of
      request-to-reply functions would flatten that ordering into a return value.

      **EACH ROUTE MATCHES EXACTLY AND THEY DO NOT SHARE A PREFIX BRANCH.** Checkout authenticates
      a signed-in browser by cookie; the Stripe webhook authenticates Stripe by HMAC over the body;
      provisioning authenticates a machine by bearer token. Three different proofs of who is
      calling, so one `/billing/` branch guarding two of them would use the wrong proof for one.
IMPORTS: serve.web.{checkout_route,provision_route,stripe_hook}. Same layer, public surface only.
CONSUMED BY: `serve/listener.py`.
"""

from __future__ import annotations

from typing import Any

from quantamind.serve.web import checkout_route, provision_route, stripe_hook

PROVISION_PREFIX = provision_route.PREFIX
CHECKOUT_PATH = checkout_route.PATH
STRIPE_HOOK_PATH = stripe_hook.PATH


def route(handler: Any) -> tuple[int, dict[str, Any]] | None:
    """The reply for this POST, or None when the listener should handle it.

    **None MEANS "NOT MINE", NOT "NOT FOUND".** The listener still owns `/webhook` and still
    answers 404 for everything else; a 404 returned from here would swallow the GitHub path.
    """
    if handler.path.startswith(PROVISION_PREFIX):
        return provision_route.for_request(handler)
    if handler.path == CHECKOUT_PATH:
        return checkout_route.for_request(handler)
    if handler.path == STRIPE_HOOK_PATH:
        return stripe_hook.for_request(handler)
    return None
