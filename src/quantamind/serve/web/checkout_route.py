"""`POST /billing/checkout` — turn a signed-in session into a Stripe Checkout URL.

WHAT: `answer(body, cookies, ...)` returns `(status, payload)`. On success the payload carries the
      URL to send the browser to. `for_request(handler)` reads one POST off the wire and calls it.
WHY:  **THE ACCOUNT COMES FROM THE SESSION COOKIE AND NEVER FROM THE BODY.** A route that billed
      whichever account the request named would let anyone create a checkout in somebody else's
      name -- which does not steal money, but does attach a subscription to the wrong login, and
      the repair is a human reading two dashboards. The signed-in login is the only account this
      route will ever put on a session.

      **THE SEAT COUNT DOES COME FROM THE BODY, AND THAT IS DELIBERATE.**
      `docs/product/pricing.md` bills per developer who opened a pull request, and nothing in this
      product measures that at checkout time. A number we derived would put a claim about their
      team on their card statement. What they ask for is what is charged, and it is recorded.

      **NOT SIGNED IN IS 401 AND SAYS NOTHING ELSE.** `serve/web/routes.py` makes the same call for
      the same reason: "expired" and "no such session" differ to us and not to a visitor.

      **AN UNCONFIGURED PRICE OR KEY REFUSES THE ROUTE RATHER THAN OPENING IT.** Same shape as
      `serve/web/provision_route.py`: "not configured" and "no payment required" must not be the
      same code path. A 503 naming the missing variable is the only answer that cannot become a
      free subscription.

      **THE IDEMPOTENCY KEY IS THE SESSION TOKEN HASH PLUS THE SEAT COUNT, NOT A FRESH VALUE.** A
      double-clicked upgrade button is one request repeated; a key this route invented per call
      would differ each time, which is the same as having none. Changing the seat count is a
      different intent and gets a different key.
IMPORTS: ingest.payments.checkout, store.{accounts,schema,tenancy}, serve.web.{http_io,signin}.
      Leftward only.
CONSUMED BY: `serve/listener.py`.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from quantamind.ingest.payments.checkout import open_session
from quantamind.ingest.payments.stripe_api import PaymentsFailed
from quantamind.serve.web import signin
from quantamind.serve.web.http_io import read_body
from quantamind.store import accounts, tenancy
from quantamind.store.schema import open_store

PATH = "/billing/checkout"
MAX_SEATS = 5_000
"""A ceiling on one request. **Chosen, not measured** -- it bounds what a single POST can put on a
card, and a typo of 30000 for 3 is the failure it is here for."""

NOT_CONFIGURED = (
    "billing is not configured on this deployment: {missing} is unset. The route refuses rather "
    "than opening, because 'not configured' and 'no payment required' must not be the same answer."
)


def _seats(body: bytes) -> int | str:
    """The seat count, or one sentence saying why the body does not carry one."""
    try:
        raw: Any = json.loads(body or b"{}")
    except json.JSONDecodeError as exc:
        return f"body is not JSON: {exc}"
    if not isinstance(raw, dict):
        return f"body is {type(raw).__name__}, not an object"
    asked = raw.get("seats")
    if not isinstance(asked, int) or isinstance(asked, bool):
        return f"seats must be an integer, got {type(asked).__name__}"
    if asked < 1:
        return f"{asked} seats; a subscription bills at least one developer"
    if asked > MAX_SEATS:
        return f"{asked} seats is above the {MAX_SEATS} ceiling for one request"
    return asked


def answer(
    body: bytes,
    cookies: str,
    *,
    api_key: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
    settings: Any,
    at: int | None = None,
) -> tuple[int, dict[str, Any]]:
    """Create one Checkout Session for the signed-in account. Never raises to the socket.

    Every credential is a parameter. `types/settings.py` refuses to hold the webhook secret for a
    stated reason -- *"a credential in a settings object reaches a log or a config dump the first
    time anybody prints one"* -- and a Stripe API key is no different.
    """
    moment = int(time.time()) if at is None else at
    missing = [
        name
        for name, value in (
            ("QUANTAMIND_STRIPE_API_KEY", api_key),
            ("QUANTAMIND_STRIPE_PRICE_ID", price_id),
        )
        if not value.strip()
    ]
    if missing:
        return 503, {"error": NOT_CONFIGURED.format(missing=" and ".join(missing))}

    token = signin.token_in(cookies)
    conn = open_store(tenancy.shared(Path(settings.database_path), tenancy.ACCOUNTS))
    try:
        session = accounts.whose(conn, token, at=moment)
    finally:
        conn.close()
    if not session.signed_in:
        return 401, {"error": "sign in first"}

    seats = _seats(body)
    if isinstance(seats, str):
        return 400, {"error": seats}

    # Same intent, same key: a double-clicked button must not buy two subscriptions.
    key = hashlib.sha256(f"{token}:{price_id}:{seats}".encode()).hexdigest()
    try:
        made = open_session(
            api_key=api_key,
            account=session.login,
            price_id=price_id,
            seats=seats,
            success_url=success_url,
            cancel_url=cancel_url,
            idempotency_key=key,
        )
    except PaymentsFailed as refused:
        # **STRIPE'S OWN SENTENCE IS NOT ECHOED TO THE BROWSER.** It can name a price id and an
        # account, and this response is reached by anyone who can sign in. The operator gets it
        # in the log; the caller gets a stage.
        print(f"[billing] checkout failed for {session.login}: {refused}", flush=True)
        return 502, {"error": "Stripe refused to create the session", "stage": refused.path}

    print(f"[billing] {made.sentence()}", flush=True)
    return 200, {
        "url": made.url,
        "session_id": made.session_id,
        "account": made.account,
        "seats": made.seats,
        # **NOTHING IS PAID YET AND THE REPLY SAYS SO.** A caller that treated a created session as
        # a completed payment would grant access to a customer who closed the tab.
        "paid": False,
        "note": "a session was created. Nothing is charged until the customer completes it, and "
        "entitlement changes only when the subscription webhook arrives.",
    }


def for_request(handler: Any) -> tuple[int, dict[str, Any]]:
    """Read one POST off the wire and answer it. Mirrors `provision_route.for_request`."""
    given, why = read_body(handler)
    if given is None:
        return 411, {"error": why}
    return answer(
        given,
        handler.headers.get("Cookie", ""),
        api_key=str(getattr(handler, "stripe_api_key", "")),
        price_id=str(getattr(handler, "stripe_price_id", "")),
        success_url=str(getattr(handler, "billing_success_url", "")),
        cancel_url=str(getattr(handler, "billing_cancel_url", "")),
        settings=handler.settings,
    )
