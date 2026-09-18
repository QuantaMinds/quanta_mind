"""Whether an account's paid subscription is open right now, and the sentence saying how we know.

WHAT: `Access`, and `decide(subscription, at, grace_days)` -> `Access`. Given the subscription row
      we last heard from Stripe and the current time, it answers open or blocked, and names which
      rule decided it. No I/O, no clock read, no store.
WHY:  **"DID THEY PAY" AND "MAY WE REVIEW" ARE DIFFERENT QUESTIONS AND THIS MODULE ANSWERS THE
      FIRST.** `docs/product/pricing.md` sells a free tier that *"does not expire and it does not
      degrade"*, so an account with no subscription is not a blocked account -- it is a free one.
      `NO_SUBSCRIPTION` therefore closes the PAID product and says nothing about the free one, and
      the caller is the only thing that knows which it is asking about. Collapsing the two here
      would turn every free-tier customer off with one import.

      **AN EXPIRED PERIOD IS NOT THE SAME AS A CANCELLED SUBSCRIPTION, AND NEITHER IS A RETRY.**
      Three different customers: one who left, one whose card failed this morning, and one whose
      renewal we simply have not heard about yet. They need three answers, three emails and three
      different amounts of patience, so `Verdict` names which one it is rather than returning a
      boolean anybody downstream would have to re-derive.

      **A `past_due` CUSTOMER KEEPS ACCESS THROUGH THE GRACE WINDOW, AND THAT IS A DECISION.**
      Stripe retries a failed card for days. Cutting off a customer at the first failed charge
      means a bank's fraud hold takes down their CI, and the recovery rate on those retries is the
      reason dunning exists at all. `GRACE_DAYS` is the number, it is stated, and it is a
      parameter so a test can prove the boundary rather than trusting it.

      **AN `active` SUBSCRIPTION WHOSE PERIOD ENDED IS OUR BUG, NOT THEIRS, AND IT IS NAMED.**
      Stripe moves a subscription out of `active` when it stops being paid, so `active` with a
      period that ended weeks ago means we MISSED A DELIVERY -- the webhook was down, the secret
      was wrong, the endpoint 500ed. Reading it as paid grants free service forever on a stale row;
      reading it as unpaid cuts off a customer who has paid. It is `STALE_RECORD`, it stays open
      through the grace window so nobody is cut off by our own outage, and after that it blocks
      with a reason that points at us. **A clean "still active" months after a period ended is the
      shape `AGENTS.md` rule 14 is about: the same output whether the mechanism works or not.**
IMPORTS: stdlib only, plus `types/billing.py`. Nothing to its right, and nothing that reads a clock
      -- `at` is passed in, so every boundary in here is reachable from a test.
CONSUMED BY: `serve/web/billing_route.py`, and whatever later decides `may_review`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from quantamind.types.billing import Standing, Subscription

GRACE_DAYS = 7
"""How long a failed renewal keeps access. **Chosen, not measured**, and stated so it can be
argued with: Stripe's default retry schedule runs to about a week, so this is "until Stripe itself
gives up" rather than a number picked to look generous."""

DAY_S = 86_400


class Verdict(Enum):
    """Which rule decided. **Every value is a different customer needing a different answer.**"""

    PAID = "paid"
    """Active or trialing, inside the paid period. The only unambiguous open."""

    IN_GRACE = "in_grace"
    """A renewal is failing and Stripe is still retrying. **A customer, not an ex-customer.**"""

    STALE_RECORD = "stale_record"
    """Active, but the period ended and no newer delivery arrived. **Our missed webhook.**"""

    EXPIRED = "expired"
    """The paid period ended and the grace window with it."""

    CANCELED = "canceled"
    """They chose to leave. Distinct from EXPIRED: nobody's card failed."""

    NEVER_PAID = "never_paid"
    """A checkout that never completed its first payment. They were never a customer."""

    PAUSED = "paused"
    NO_SUBSCRIPTION = "no_subscription"
    """No row at all. **This is the free tier, not a refusal** -- see the module docstring."""


OPEN = frozenset({Verdict.PAID, Verdict.IN_GRACE, Verdict.STALE_RECORD})
"""The verdicts that leave the paid product open. **Named as a set rather than as a boolean on
each member**, so adding a verdict forces a decision about it instead of defaulting to closed."""


@dataclass(frozen=True, slots=True)
class Access:
    """Open or blocked, which rule said so, and one sentence a human can act on."""

    allowed: bool
    verdict: Verdict
    reason: str
    paid_through: int = 0
    """Unix seconds the paid period runs to. Zero when there is no period to name."""

    def __post_init__(self) -> None:
        # The set and the flag must not be able to disagree: a caller reading one and a log
        # reading the other is how an account shows as blocked in a dashboard and open in a review.
        if self.allowed != (self.verdict in OPEN):
            raise ValueError(
                f"{self.verdict.value} is {'in' if self.verdict in OPEN else 'not in'} OPEN but "
                f"allowed={self.allowed}; the flag and the verdict must agree"
            )
        if not self.reason:
            raise ValueError("an access decision without a reason cannot be shown to anybody")


def _grace_end(subscription: Subscription, grace_days: int) -> int:
    """When patience runs out. **From the period end, not from now** -- a window measured from
    the moment we happen to ask would never close, because every call restarts it."""
    return subscription.current_period_end + grace_days * DAY_S


def decide(subscription: Subscription | None, *, at: int, grace_days: int = GRACE_DAYS) -> Access:
    """Whether the paid product is open for this account at this instant.

    `at` is a parameter and not a `time.time()` call: every boundary this function has is a
    comparison against it, and a clock read inside would make all of them unreachable from a test.
    """
    if subscription is None:
        return Access(
            False,
            Verdict.NO_SUBSCRIPTION,
            "no subscription on record. **This is the free tier, not a refusal** -- the caller "
            "decides whether it was asking about the paid product or about access at all",
        )

    ends = subscription.current_period_end
    through = f"paid through {ends}" if ends else "no period on the record"

    if subscription.standing in (Standing.ACTIVE, Standing.TRIALING):
        if ends == 0 or at <= ends:
            return Access(
                True,
                Verdict.PAID,
                f"{subscription.standing.value}, {through}",
                paid_through=ends,
            )
        # Active with a period that ended: see STALE_RECORD in the module docstring.
        if at <= _grace_end(subscription, grace_days):
            return Access(
                True,
                Verdict.STALE_RECORD,
                f"Stripe last said {subscription.standing.value} but the period ended at {ends}, "
                f"{(at - ends) // DAY_S}d ago. **That means we missed a delivery, not that they "
                f"stopped paying** -- access is held open for {grace_days}d. Check the webhook "
                f"endpoint and the signing secret before touching this account",
                paid_through=ends,
            )
        return Access(
            False,
            Verdict.EXPIRED,
            f"Stripe last said {subscription.standing.value} at {ends}, more than {grace_days}d "
            f"ago, and nothing newer arrived. The record is stale and cannot be relied on; "
            f"re-read the subscription from Stripe rather than trusting this row",
            paid_through=ends,
        )

    if subscription.standing is Standing.PAST_DUE:
        if at <= _grace_end(subscription, grace_days):
            return Access(
                True,
                Verdict.IN_GRACE,
                f"a renewal failed and Stripe is still retrying; {through}, access held for "
                f"{grace_days}d past that",
                paid_through=ends,
            )
        return Access(
            False,
            Verdict.EXPIRED,
            f"the renewal failed and the {grace_days}d grace window closed; {through}",
            paid_through=ends,
        )

    if subscription.standing is Standing.CANCELED:
        return Access(
            False, Verdict.CANCELED, f"the subscription was cancelled; {through}", paid_through=ends
        )
    if subscription.standing is Standing.UNPAID:
        return Access(
            False,
            Verdict.EXPIRED,
            f"every retry failed and Stripe stopped; {through}. **Nobody chose this** -- it is a "
            f"card that never recovered, and it is worth a human contacting them",
            paid_through=ends,
        )
    if subscription.standing is Standing.PAUSED:
        return Access(False, Verdict.PAUSED, f"collection is paused; {through}", paid_through=ends)
    # INCOMPLETE and INCOMPLETE_EXPIRED: checkout finished, the first payment did not.
    return Access(
        False,
        Verdict.NEVER_PAID,
        f"{subscription.standing.value}: the first payment never completed, so this account has "
        f"never paid us. It is not a lapsed customer and must not be dunned like one",
        paid_through=ends,
    )
