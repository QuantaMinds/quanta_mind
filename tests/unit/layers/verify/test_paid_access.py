"""Verification that a failed card, a cancellation and our own missed webhook get three answers.

WHAT: Drives `verify/paid_access.decide` across every standing and across both sides of every
      boundary it has — the period end, the grace end, and the two of them one second apart.
WHY:  **THE BOUNDARIES ARE THE WHOLE MODULE.** `decide` is a pile of comparisons against `at`, and
      a test that only ever asks "clearly inside" and "clearly outside" would pass against `<`
      where `<=` was meant — which is one customer cut off one second early, on renewal day, once
      a month, silently. Every boundary here is asserted at exactly the second it turns.

      **`at` IS A PARAMETER SO THESE TESTS CAN EXIST AT ALL.** A `time.time()` inside `decide`
      would make every branch below unreachable: there is no way to ask a function "what would you
      say in nine days" if it reads the clock itself.

      **AN ACTIVE SUBSCRIPTION WITH AN ENDED PERIOD IS OUR BUG AND MUST NOT READ AS PAID.** It
      means a delivery was missed. `AGENTS.md` rule 14: a check whose output is the same whether
      the mechanism works or not is not a check, and "still active" forever on a stale row is
      exactly that shape.

      **NO SUBSCRIPTION IS THE FREE TIER, NOT A REFUSAL.** `docs/product/pricing.md` sells a free
      tier that does not expire. A test that accepted `allowed is False` without reading the
      verdict would let somebody later make this mean "blocked" and turn the free tier off.
IMPORTS: pytest, quantamind.types.billing, quantamind.verify.paid_access.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.types.billing import Standing, Subscription
from quantamind.verify.paid_access import DAY_S, GRACE_DAYS, Access, Verdict, decide

PERIOD_END = 1_700_000_000
GRACE_END = PERIOD_END + GRACE_DAYS * DAY_S


def sub(standing: Standing, *, ends: int = PERIOD_END) -> Subscription:
    """One subscription in a given standing. Only `standing` and the period end matter here."""
    return Subscription(
        account="octocat",
        subscription_id="sub_1",
        customer_id="cus_1",
        price_id="price_1",
        standing=standing,
        seats=3,
        amount_cents=2900,
        currency="usd",
        current_period_end=ends,
        event_at=PERIOD_END - DAY_S,
    )


def test_no_subscription_is_the_free_tier_and_says_so() -> None:
    """**Not a refusal.** The caller decides whether it was asking about the paid product."""
    access = decide(None, at=PERIOD_END)

    assert access.verdict is Verdict.NO_SUBSCRIPTION
    assert access.allowed is False
    assert "free tier, not a refusal" in access.reason
    assert access.paid_through == 0


@pytest.mark.parametrize("standing", [Standing.ACTIVE, Standing.TRIALING])
def test_paid_up_to_and_including_the_final_second(standing: Standing) -> None:
    """`at == ends` is still paid. A `<` here bills someone for a period it then denies them."""
    assert decide(sub(standing), at=PERIOD_END).verdict is Verdict.PAID
    assert decide(sub(standing), at=PERIOD_END - 1).verdict is Verdict.PAID
    assert decide(sub(standing), at=PERIOD_END).paid_through == PERIOD_END


def test_active_one_second_past_the_period_is_a_missed_delivery_not_a_payment() -> None:
    """Stripe moves a subscription out of `active` when it stops being paid. So this is ours."""
    access = decide(sub(Standing.ACTIVE), at=PERIOD_END + 1)

    assert access.verdict is Verdict.STALE_RECORD
    assert access.allowed is True, "our own outage must not cut off a paying customer"
    assert "we missed a delivery" in access.reason
    assert "webhook endpoint" in access.reason


def test_a_stale_active_record_stops_being_believed_after_the_grace_window() -> None:
    """Held open for the window, then blocked with a reason pointing at us, not at them."""
    assert decide(sub(Standing.ACTIVE), at=GRACE_END).verdict is Verdict.STALE_RECORD

    lapsed = decide(sub(Standing.ACTIVE), at=GRACE_END + 1)
    assert lapsed.verdict is Verdict.EXPIRED
    assert lapsed.allowed is False
    assert "re-read the subscription from Stripe" in lapsed.reason


def test_past_due_keeps_access_through_the_grace_window_and_not_one_second_longer() -> None:
    """A bank's fraud hold must not take down their CI on the first failed charge."""
    assert decide(sub(Standing.PAST_DUE), at=PERIOD_END + 1).verdict is Verdict.IN_GRACE
    assert decide(sub(Standing.PAST_DUE), at=GRACE_END).verdict is Verdict.IN_GRACE

    closed = decide(sub(Standing.PAST_DUE), at=GRACE_END + 1)
    assert closed.verdict is Verdict.EXPIRED
    assert closed.allowed is False


def test_the_grace_window_is_measured_from_the_period_end_not_from_now() -> None:
    """A window measured from the moment we ask never closes, because every call restarts it."""
    long_after = GRACE_END + 400 * DAY_S

    assert decide(sub(Standing.PAST_DUE), at=long_after).verdict is Verdict.EXPIRED


def test_a_shorter_grace_moves_the_boundary_so_the_number_is_not_decoration() -> None:
    """**The constant is exercised, not merely present.** `just check` counts 95 of 130 product
    constants as changeable with every test still green; this is one that is not."""
    two_days = PERIOD_END + 2 * DAY_S

    assert decide(sub(Standing.PAST_DUE), at=two_days, grace_days=7).verdict is Verdict.IN_GRACE
    assert decide(sub(Standing.PAST_DUE), at=two_days, grace_days=1).verdict is Verdict.EXPIRED


def test_cancelled_is_not_expired_because_nobody_s_card_failed() -> None:
    """Two blocked accounts needing two different emails and two different conversations."""
    left = decide(sub(Standing.CANCELED), at=PERIOD_END + 1)
    failed = decide(sub(Standing.UNPAID), at=PERIOD_END + 1)

    assert left.verdict is Verdict.CANCELED
    assert failed.verdict is Verdict.EXPIRED
    assert "was cancelled" in left.reason
    assert "worth a human contacting them" in failed.reason


@pytest.mark.parametrize("standing", [Standing.INCOMPLETE, Standing.INCOMPLETE_EXPIRED])
def test_a_checkout_that_never_paid_is_not_a_lapsed_customer(standing: Standing) -> None:
    """They were never a customer. Dunning them is a letter about a debt that does not exist."""
    access = decide(sub(standing), at=PERIOD_END)

    assert access.verdict is Verdict.NEVER_PAID
    assert "must not be dunned like one" in access.reason


def test_paused_is_its_own_verdict_and_not_folded_into_cancelled() -> None:
    access = decide(sub(Standing.PAUSED), at=PERIOD_END)

    assert access.verdict is Verdict.PAUSED
    assert access.allowed is False


def test_a_subscription_with_no_period_is_open_rather_than_instantly_expired() -> None:
    """`current_period_end` is 0 on a subscription Stripe sent no period for. Zero is not 1970."""
    access = decide(sub(Standing.ACTIVE, ends=0), at=PERIOD_END)

    assert access.verdict is Verdict.PAID
    assert "no period on the record" in access.reason


def test_the_flag_and_the_verdict_cannot_be_made_to_disagree() -> None:
    """A dashboard reading one and a review reading the other is the failure this refuses."""
    with pytest.raises(ValueError, match="must agree"):
        Access(True, Verdict.CANCELED, "they left")


def test_a_decision_without_a_reason_is_refused_at_construction() -> None:
    with pytest.raises(ValueError, match="cannot be shown to anybody"):
        Access(True, Verdict.PAID, "")
