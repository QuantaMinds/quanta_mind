"""Read an AUTHENTICATED Stripe delivery, and say what it means for one account.

WHAT: `interpret(body)` returns a `types/billing.Subscription` for the events that change what an
      account is entitled to, and an `Ignore` carrying a reason for everything else.
WHY:  **IT IS A SEPARATE MODULE FROM `serve/webhook_stripe.py` ON PURPOSE.** That one proves bytes
      came from Stripe; this one believes them. Keeping deserialisation out of the module that
      authenticates removes the standing invitation to parse before verifying -- the HMAC covers
      exact bytes, and re-serialising to check a signature is how an authentic delivery starts
      failing. `serve/webhook_github.py` holds both because it predates the split; this does not.

      **AN `Ignore` IS THE NORMAL CASE, NOT AN ERROR.** A healthy Stripe account emits dozens of
      event types an hour -- invoices, payment intents, charges. Raising on them would fill a log
      with things nobody should read, so every one returns a sentence saying why it was dropped.

      **A SUBSCRIPTION WITH NO `metadata.account` IS UNMATCHED, AND THAT IS A STATED OUTCOME.**
      Stripe knows a customer id and has never heard of a GitHub login;
      `ingest/payments/checkout.py` puts the account into `subscription_data[metadata]` for exactly
      this read. One created by hand in the Dashboard has none. Answering non-2xx would make Stripe
      retry for three days something that will never match, and dropping it silently would lose a
      payment we took -- so it is named, and the caller logs it and answers 200.

      **`current_period_end` IS READ OFF THE SUBSCRIPTION ITEM FIRST.** Stripe moved it from the
      subscription onto its items, and the version pinned in `ingest/payments/stripe_api.py` is on
      the far side of that move. The top level is a fallback, and the absence of both is 0 -- which
      `types/billing.py` documents as "no period", rather than a date this module invented.

      **AN UNKNOWN `status` BECOMES AN `Ignore`, NOT A GUESS.** `types/billing.standing()` raises on
      a status this build does not have, and that refusal is carried into the reason rather than
      defaulted to unpaid. A new Stripe status must not cut off a paying customer on the day it
      ships.
IMPORTS: stdlib (json), and `types/billing.py`. Leftward only.
CONSUMED BY: `serve/web/billing_route.py`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from quantamind.types.billing import NotAStanding, Subscription, standing

SUBSCRIPTION_EVENTS = (
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
)
"""The only events that change what an account is entitled to.

**`checkout.session.completed` IS DELIBERATELY NOT HERE.** It fires once, at signup, and Stripe
emits `customer.subscription.created` for the same moment carrying the full state -- status, price,
quantity, period. Acting on both would write the same row twice from two shapes, and the session
object does not carry the status at all, so it could only ever produce a guess."""


@dataclass(frozen=True, slots=True)
class Ignore:
    """An authenticated delivery that is not ours to act on. Carries why, for the log."""

    reason: str


def _period_end(subscription: dict[str, Any]) -> int:
    """When the paid period ends. **Read off the ITEM first; Stripe moved it there.**"""
    items = (subscription.get("items") or {}).get("data") or []
    if items and isinstance(items[0], dict) and items[0].get("current_period_end"):
        return int(items[0]["current_period_end"])
    return int(subscription.get("current_period_end") or 0)


def _subscription(event: dict[str, Any], payload: dict[str, Any]) -> Subscription | Ignore:
    """One `customer.subscription.*` object as a `Subscription`, or why it could not be read."""
    account = str((event.get("metadata") or {}).get("account") or "")
    if not account:
        # **UNMATCHED IS A STATED OUTCOME, NOT AN ERROR.** A subscription created by hand in the
        # Dashboard carries no account, and answering non-2xx would make Stripe retry for three
        # days something that will never match.
        return Ignore(
            f"subscription {event.get('id')} carries no metadata.account, so it belongs to no "
            f"GitHub login we know. It was created outside checkout, or without subscription_data"
        )
    items = (event.get("items") or {}).get("data") or []
    first = items[0] if items and isinstance(items[0], dict) else {}
    price = first.get("price") or {}
    try:
        where = standing(str(event.get("status") or ""))
    except NotAStanding as unknown:
        return Ignore(str(unknown))
    return Subscription(
        account=account,
        subscription_id=str(event.get("id") or ""),
        customer_id=str(event.get("customer") or ""),
        price_id=str(price.get("id") or ""),
        standing=where,
        seats=int(first.get("quantity") or 1),
        amount_cents=int(price.get("unit_amount") or 0),
        currency=str(event.get("currency") or price.get("currency") or "usd"),
        current_period_end=_period_end(event),
        event_at=int(payload.get("created") or 0),
    )


def interpret(body: bytes) -> Subscription | Ignore:
    """What an AUTHENTICATED delivery means. Never called before `verify()` returns None.

    Returns `Ignore` with a reason rather than raising: Stripe sends dozens of event types a
    healthy account produces, and an endpoint that errors on them fills a log nobody should read.
    """
    try:
        payload: Any = json.loads(body)
    except json.JSONDecodeError as exc:
        return Ignore(f"body is not JSON: {exc}")
    if not isinstance(payload, dict):
        return Ignore(f"body is {type(payload).__name__}, not an object")

    kind = str(payload.get("type") or "")
    if kind not in SUBSCRIPTION_EVENTS:
        return Ignore(f"event {kind!r} does not change what an account is entitled to")

    event = (payload.get("data") or {}).get("object")
    if not isinstance(event, dict):
        return Ignore(f"{kind} carried no data.object")
    return _subscription(event, payload)
