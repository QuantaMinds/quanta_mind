"""Whether an account's paid entitlement is open right now, and the sentence saying how we know.

WHAT: `Access`, and `decide(coverage, at, grace_days)` -> `Access`. Given the coverage the billing
      service last pushed and the current time, it answers open or blocked, and names which rule
      decided it. No I/O, no clock read, no store.
WHY:  **IT READS THE PUSHED ENTITLEMENT, NOT A STRIPE SUBSCRIPTION ROW.** `server/` owns the
      Stripe relationship and pushes the result over `POST /entitlement`; this layer never sees a
      Stripe object. Recorded in `docs/engineering/STRIPE.md`: money lives in Postgres where a
      ledger can be transactional, and the reviewer holds a cache it can read while billing is down.

      **"DID THEY PAY" AND "MAY WE REVIEW" ARE DIFFERENT QUESTIONS AND THIS ANSWERS THE FIRST.**
      `docs/product/pricing.md` sells a free tier that *"does not expire and it does not degrade"*,
      so an account with no coverage is free, not blocked. `NO_SUBSCRIPTION` closes the PAID
      product and says nothing about the free one; the caller knows which it was asking about.

      **AN EXPIRED PERIOD, A CANCELLATION AND A FAILING RETRY ARE THREE CUSTOMERS, NOT ONE**, so
      `Verdict` names which rather than returning a boolean anybody downstream would re-derive. A
      `past_due` customer keeps access for `GRACE_DAYS`: Stripe retries a failed card for days, and
      cutting them off at the first failure means a bank's fraud hold takes down their CI.

      **AN `active` COVERAGE WHOSE PERIOD ENDED IS OUR BUG, NOT THEIRS, AND IT IS NAMED.** Billing
      moves an account out of `active` when it stops being paid, so `active` with a period that
      ended weeks ago means A PUSH NEVER ARRIVED. Reading it as paid grants free service forever on
      a stale row; reading it as unpaid cuts off a customer who has paid. `STALE_RECORD` stays open
      through the grace window, then blocks with a reason pointing at us. **A clean "still active"
      months after a period ended is `AGENTS.md` rule 14: the same output whether it works or not.**
IMPORTS: stdlib only, plus `store/billing/entitlement.py`. Nothing reads a clock -- `at` is passed
      in, so every boundary in here is reachable from a test.
CONSUMED BY: `serve/web/provision_payment.py`, and whatever later decides `may_review`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from quantamind.store.billing.entitlement import Coverage, State

GRACE_DAYS = 7
"""How long a failed renewal keeps access. **Chosen, not measured**: Stripe's retry schedule runs
to about a week, so this is "until Stripe gives up" rather than a number picked to look generous."""

DAY_S = 86_400


class Verdict(Enum):
    """Which rule decided. **Every value is a different customer needing a different answer.**"""

    PAID = "paid"
    """Active or trialing, inside the paid period. The only unambiguous open."""

    IN_GRACE = "in_grace"
    """A renewal is failing and Stripe is still retrying. **A customer, not an ex-customer.**"""

    STALE_RECORD = "stale_record"
    """Active, but the period ended and no newer push arrived. **Our missed delivery.**"""

    EXPIRED = "expired"
    """The paid period ended and the grace window with it."""

    CANCELED = "canceled"
    """They chose to leave. Distinct from EXPIRED: nobody's card failed."""

    NEVER_PAID = "never_paid"
    """A checkout that never completed its first payment. They were never a customer."""

    PAUSED = "paused"
    NO_SUBSCRIPTION = "no_subscription"
    """No coverage. **This is the free tier, not a refusal** -- see the module docstring."""


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


_SETTLED = {
    State.CANCELLED: (
        Verdict.CANCELED,
        "the subscription was cancelled",
    ),
    State.UNPAID: (
        Verdict.EXPIRED,
        "every retry failed and Stripe stopped. **Nobody chose this** -- it is a card that never "
        "recovered, and it is worth a human contacting them",
    ),
    State.PAUSED: (
        Verdict.PAUSED,
        "collection is paused",
    ),
    State.INCOMPLETE: (
        Verdict.NEVER_PAID,
        "the first payment never completed, so this account has never paid us. It is not a lapsed "
        "customer and must not be dunned like one",
    ),
}
"""States that need no date arithmetic. **Held as a table so a new `State` fails at import with a
KeyError rather than falling through to a default** -- a default here would be a verdict nobody
chose, applied to a paying customer."""


def _quiet(coverage: Coverage) -> str:
    """The extra sentence when the billing service itself has gone quiet, or nothing."""
    if not coverage.stale:
        return ""
    return (
        ". Separately, the billing service has not pushed since its grace window closed, so this "
        "row may not reflect what Stripe says now -- check the entitlement drain"
    )


def decide(coverage: Coverage, *, at: int, grace_days: int = GRACE_DAYS) -> Access:
    """Whether the paid product is open for this account at this instant.

    `at` is a parameter and not a `time.time()` call: every boundary this function has is a
    comparison against it, and a clock read inside would make all of them unreachable from a test.
    """
    if coverage.state is State.NONE:
        return Access(
            False,
            Verdict.NO_SUBSCRIPTION,
            "no coverage on record. **This is the free tier, not a refusal** -- the caller "
            "decides whether it was asking about the paid product or about access at all",
        )

    ends = coverage.valid_through or 0
    through = f"paid through {ends}" if ends else "no period on the record"
    # When patience runs out. **From the period end, not from now** -- a window measured from the
    # moment we happen to ask would never close, because every call restarts it.
    patience = ends + grace_days * DAY_S

    # `Coverage.paid` is the store's own definition; repeating the tuple would let them disagree.
    if coverage.paid:
        if ends == 0 or at <= ends:
            # `_quiet` belongs here too: an account still inside its period otherwise reads as
            # healthy while the drain keeping it healthy has stopped -- which is exactly when
            # somebody can still fix it before anyone is cut off.
            return Access(
                True, Verdict.PAID, f"{coverage.state.value}, {through}" + _quiet(coverage), ends
            )
        if at <= patience:
            return Access(
                True,
                Verdict.STALE_RECORD,
                f"billing last said {coverage.state.value} but the period ended at {ends}, "
                f"{(at - ends) // DAY_S}d ago. **That means a push never arrived, not that they "
                f"stopped paying** -- access is held open for {grace_days}d. Check the entitlement "
                f"drain and the provisioning secret before touching this account"
                + _quiet(coverage),
                ends,
            )
        return Access(
            False,
            Verdict.EXPIRED,
            f"billing last said {coverage.state.value} at {ends}, more than {grace_days}d ago, "
            f"and nothing newer arrived. The row is stale and cannot be relied on; re-push the "
            f"entitlement rather than trusting it" + _quiet(coverage),
            ends,
        )

    if coverage.state is State.PAST_DUE:
        if at <= patience:
            return Access(
                True,
                Verdict.IN_GRACE,
                f"a renewal failed and Stripe is still retrying; {through}, access held for "
                f"{grace_days}d past that" + _quiet(coverage),
                ends,
            )
        return Access(
            False,
            Verdict.EXPIRED,
            f"the renewal failed and the {grace_days}d grace window closed; {through}",
            ends,
        )

    verdict, why = _SETTLED[coverage.state]
    return Access(False, verdict, f"{why}; {through}" + _quiet(coverage), ends)
