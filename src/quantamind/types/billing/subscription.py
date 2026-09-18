"""What a subscription IS, with no way to spell "probably paid".

WHAT: `Standing`, the state Stripe says a subscription is in; `NotAStanding` when it says one we
      do not have; and `Subscription`, one account's current subscription as we last heard it.
WHY:  **A BOOLEAN `active` CANNOT TELL "THEY CANCELLED" FROM "THEIR CARD FAILED ON TUESDAY."**
      Those need different answers from us -- one is a customer leaving and one is a customer who
      does not know yet -- and a product that collapses them has to guess which email to send.
      So the standing is a name, and `paid` is derived from it rather than stored beside it.

      **AN UNRECOGNISED STANDING RAISES. IT IS NEVER READ AS UNPAID, AND NEVER AS PAID.** Stripe
      has added states before and will again. Reading an unknown one as unpaid cuts off a paying
      customer on the day Stripe ships a new name; reading it as paid keeps serving one who
      stopped paying. `types/deployment.named()` refuses an unknown deployment shape for the same
      reason and this follows it deliberately.

      **`current_period_end` IS STORED BECAUSE "NOT ACTIVE" IS THE WRONG ANSWER ON RENEWAL DAY.**
      A card retried at 03:00 leaves a subscription `past_due` for a few hours on a customer who
      has paid us every month for a year. Holding the date lets the answer be "paid through the
      3rd, retrying" instead of a state that reads like a cancellation.

      **`event_at` IS STRIPE'S TIMESTAMP, NOT OURS, AND IT IS HERE FOR ORDERING.** Stripe does not
      guarantee delivery order, so an older event must not overwrite a newer one --
      `store/subscriptions.py` compares this field and the comparison is the only thing standing
      between a redelivered `canceled` and a live customer being switched off.
IMPORTS: stdlib only (dataclasses, enum). Nothing from any layer; this is the leftmost.
CONSUMED BY: `store/subscriptions.py`, `serve/webhook_stripe.py`, `verify/tier_request.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Standing(Enum):
    """Where a subscription stands with Stripe. **The value is Stripe's own `status` string.**"""

    INCOMPLETE = "incomplete"
    """Checkout finished, the first payment has not. Not paid, and not a failure either."""

    INCOMPLETE_EXPIRED = "incomplete_expired"
    """The first payment never completed and Stripe gave up. They never paid us once."""

    TRIALING = "trialing"
    ACTIVE = "active"

    PAST_DUE = "past_due"
    """A renewal failed and Stripe is retrying. **A customer, not an ex-customer.**"""

    CANCELED = "canceled"
    UNPAID = "unpaid"
    """Every retry failed and Stripe stopped. Distinct from CANCELED: nobody chose this."""

    PAUSED = "paused"
    """Paused by the customer or by a paused collection setting. Not paying, not leaving."""

    @property
    def paid(self) -> bool:
        """Whether money is currently flowing. **Trialing counts and past_due does not.**

        A trial is a subscription Stripe is holding a payment method for and will charge; the
        product is being delivered under an arrangement the customer entered. `past_due` is
        excluded HERE and is deliberately not the same as "cut them off" -- what a caller does
        about a retrying card is a decision about grace, made against `current_period_end`, and
        this property is not the place to bury it.
        """
        return self in (Standing.ACTIVE, Standing.TRIALING)


class NotAStanding(ValueError):
    """Stripe sent a status we do not have. **Refused rather than read as either answer.**"""

    def __init__(self, raw: str) -> None:
        super().__init__(
            f"Stripe sent subscription status {raw!r}, which this build does not know. It is "
            f"refused rather than guessed: reading it as unpaid would cut off a paying customer "
            f"and reading it as paid would serve one who stopped. Known: "
            f"{', '.join(s.value for s in Standing)}."
        )
        self.raw = raw


def standing(raw: str) -> Standing:
    """Stripe's status string as a `Standing`. **An unknown name raises; see `NotAStanding`.**"""
    try:
        return Standing(raw)
    except ValueError:
        raise NotAStanding(raw) from None


@dataclass(frozen=True, slots=True)
class Subscription:
    """One account's subscription as we last heard it from Stripe over a signed channel.

    **EVERY FIELD IS SOMETHING STRIPE TOLD US, NOT SOMETHING A CALLER SENT.** That is the whole
    distinction `verify/tier_request.py` turns on: a `payment_ref` in a request body is a string
    somebody typed, and this is a record written from an authenticated delivery. Constructing one
    of these from a request payload would erase the difference the type exists to hold.
    """

    account: str
    """The GitHub login, carried through checkout as `client_reference_id`. **Our key, not
    Stripe's** -- Stripe knows a customer id and has never heard of a GitHub account."""

    subscription_id: str
    customer_id: str
    price_id: str
    standing: Standing
    seats: int
    amount_cents: int
    """What Stripe says the line costs, in the smallest currency unit. **Recorded so a
    misconfigured price id is visible in the row rather than only on an invoice.**"""

    currency: str
    current_period_end: int
    """Unix seconds. Zero when Stripe did not send one, which is a real case on an incomplete
    subscription -- and zero is legible as "no period" in a way a guessed date would not be."""

    event_at: int
    """Stripe's `created` on the event that produced this row. **Ordering, not history.**"""

    @property
    def paid(self) -> bool:
        return self.standing.paid

    def sentence(self) -> str:
        """One line for an operator. Names the standing, never just paid or not."""
        return (
            f"{self.account}: {self.standing.value}, {self.seats} seat(s) at "
            f"{self.amount_cents / 100:.2f} {self.currency.upper()}, "
            f"subscription {self.subscription_id}"
        )
