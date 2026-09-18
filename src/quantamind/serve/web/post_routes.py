"""Which POST route a path is, and nothing about what any of them does.

WHAT: `route(handler)` returns `(status, payload)` for the two POST routes that are not the
      GitHub webhook, and `None` when the path is not one of them.
WHY:  **`serve/listener.py` SITS AT THE 200-LINE CAP AND THE THIRD ROUTE HAD NOWHERE TO GO.**
      `AGENTS.md` rule 4: split by concern, do not raise the cap. The concern split out is
      *which route is this*, which is genuinely separate from the socket work the listener does --
      reading a body by `Content-Length`, answering inside ten seconds, claiming a delivery.

      **THE GITHUB WEBHOOK IS DELIBERATELY NOT HERE.** It is the only POST that has to be
      authenticated, claimed against a replay ledger, answered, and only THEN worked -- the
      acknowledge-then-work shape `serve/listener.py` exists to hold. Moving it into a table of
      request-to-reply functions would flatten that ordering into a return value.

      **EACH ROUTE MATCHES EXACTLY AND THEY DO NOT SHARE A PREFIX BRANCH.** Provisioning
      authenticates a machine by bearer token; `/entitlement` authenticates the billing service by
      a DIFFERENT bearer, rotated separately. Two different proofs of who is calling, so one
      `/billing/` branch guarding both would use the wrong proof for one.

      **STRIPE USED TO BE ROUTED HERE AND IS NOT ANY MORE.** `checkout_route` and `stripe_hook`
      were removed when the billing service took ownership of the Stripe relationship; this
      service is told what an account holds over `/entitlement` and never speaks to a payment
      processor. See `docs/engineering/STRIPE.md`.
IMPORTS: serve.web.{entitlement_route,provision_route}. Same layer, public surface only.
CONSUMED BY: `serve/listener.py`.
"""

from __future__ import annotations

from typing import Any

from quantamind.serve.web import entitlement_route, provision_route

PROVISION_PREFIX = provision_route.PREFIX
ENTITLEMENT_PATH = entitlement_route.PATH


def route(handler: Any) -> tuple[int, dict[str, Any]] | None:
    """The reply for this POST, or None when the listener should handle it.

    **None MEANS "NOT MINE", NOT "NOT FOUND".** The listener still owns `/webhook` and still
    answers 404 for everything else; a 404 returned from here would swallow the GitHub path.
    """
    if handler.path.startswith(PROVISION_PREFIX):
        return provision_route.for_request(handler)
    # **THE QUERY STRING IS STRIPPED FOR THIS ONE AND NOT FOR PROVISIONING.** Provisioning is
    # reached from our own code; this one is reached by another service through whatever proxy
    # sits in front of it, and an appended `?` would turn a correct push into a 404 that reads as
    # "the reviewer does not have that route".
    if handler.path.partition("?")[0] == ENTITLEMENT_PATH:
        return entitlement_route.for_request(handler)
    return None
