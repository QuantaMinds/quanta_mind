"""One Checkout Session, carrying the GitHub account through to every event it will produce.

WHAT: `Session` is what we got back; `open_session(...)` creates one for an account, a price and a
      seat count, and returns where to send the browser.
WHY:  **STRIPE HAS NEVER HEARD OF A GITHUB LOGIN, SO THE LINK HAS TO BE PUT THERE ON PURPOSE.**
      Stripe knows a customer id. We know `octocat`. If the session does not carry the account,
      a completed payment arrives at our webhook attached to nobody, and the only repair is a human
      reading two dashboards side by side.

      **AND IT IS CARRIED TWICE, WHICH IS NOT BELT-AND-BRACES BUT TWO DIFFERENT EVENTS.**
      `client_reference_id` appears on `checkout.session.completed` and on nothing else.
      Every later event -- the renewal, the failed card, the cancellation -- is about the
      SUBSCRIPTION, which has no reference id at all. So the account also goes into
      `subscription_data[metadata][account]`, where it lands on the subscription object itself and
      travels with every event for the life of it. Setting only the first would attribute the
      signup and lose every event after it, and the gap would open a month later on the first
      renewal, not on the day this ships.

      **THE SEAT COUNT IS WHAT THE CALLER ASKED FOR, NOT WHAT WE COUNTED.** `docs/product/
      pricing.md` bills per developer who opened a pull request, and this product does not yet
      measure that at checkout time. Sending a number we derived would make the invoice a claim
      about their team that we cannot support. Whatever is sent is recorded and shows up in the
      subscription row.

      **NOTHING HERE DECIDES A TIER.** The price id is configuration, handed in. A module that
      mapped tier names to price ids would be a second place the pricing lives, and the first one
      to drift.
IMPORTS: stdlib dataclasses, and `ingest/payments/stripe_api.py`. Same layer, public surface only.
CONSUMED BY: `serve/web/billing_route.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from quantamind.ingest.payments.stripe_api import PaymentsFailed, call

SESSIONS = "v1/checkout/sessions"
MODE = "subscription"


@dataclass(frozen=True, slots=True)
class Session:
    """A created Checkout Session. `url` is where the browser goes; nothing is paid yet."""

    session_id: str
    url: str
    account: str
    price_id: str
    seats: int

    def sentence(self) -> str:
        return (
            f"checkout {self.session_id} for {self.account}: {self.seats} seat(s) "
            f"on {self.price_id}"
        )


def open_session(
    *,
    api_key: str,
    account: str,
    price_id: str,
    seats: int,
    success_url: str,
    cancel_url: str,
    idempotency_key: str | None = None,
) -> Session:
    """Create one session, or raise. **Every argument is required and none is defaulted here.**

    A default `seats=1` or a fallback price id would each be a number we invented appearing on
    somebody's card statement. The caller has the request in front of it and is the only thing
    that knows what was asked for.
    """
    if not account.strip():
        raise PaymentsFailed(
            "POST",
            SESSIONS,
            "no account was named. A session without one produces a payment attached to nobody, "
            "and the only repair is a human reading two dashboards side by side",
        )
    if seats < 1:
        raise PaymentsFailed("POST", SESSIONS, f"{seats} seats; a subscription bills at least one")
    if not price_id.strip():
        raise PaymentsFailed(
            "POST", SESSIONS, "no price id; it is configuration and this build has none set"
        )

    answered = call(
        SESSIONS,
        api_key=api_key,
        params={
            "mode": MODE,
            "line_items": [{"price": price_id, "quantity": seats}],
            "client_reference_id": account,
            # Lands on the SUBSCRIPTION, so every later event carries it. See the module docstring.
            "subscription_data": {"metadata": {"account": account}},
            "success_url": success_url,
            "cancel_url": cancel_url,
        },
        idempotency_key=idempotency_key,
    )

    url = str(answered.get("url") or "")
    session_id = str(answered.get("id") or "")
    if not url or not session_id:
        # **A 2XX WITH NO URL IS A FAILURE, NOT AN EMPTY SESSION.** Returning one would send a
        # caller to redirect a browser to "", which renders as the caller's own page and looks
        # like the customer changed their mind.
        raise PaymentsFailed(
            "POST", SESSIONS, f"Stripe returned a session with no url: {sorted(answered)}"
        )
    return Session(session_id=session_id, url=url, account=account, price_id=price_id, seats=seats)
