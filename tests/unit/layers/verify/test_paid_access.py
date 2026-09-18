"""Verification that a failed card, a cancellation and our own missed push get three answers.

WHAT: Drives `verify/paid_access.decide` across every state and across both sides of every
      boundary it has — the period end, the grace end, and the two of them one second apart.
WHY:  **THE BOUNDARIES ARE THE WHOLE MODULE.** `decide` is a pile of comparisons against `at`, and
      a test that only ever asks "clearly inside" and "clearly outside" would pass against `<`
      where `<=` was meant — which is one customer cut off one second early, on renewal day, once
      a month, silently. Every boundary here is asserted at exactly the second it turns.

      **`at` IS A PARAMETER SO THESE TESTS CAN EXIST AT ALL.** A `time.time()` inside `decide`
      would make every branch below unreachable: there is no way to ask a function "what would you
      say in nine days" if it reads the clock itself.

      **ACTIVE COVERAGE WITH AN ENDED PERIOD IS OUR BUG AND MUST NOT READ AS PAID.** It means a
      push was missed. `AGENTS.md` rule 14: a check whose output is the same whether the mechanism
      works or not is not a check, and "still active" forever on a stale row is exactly that shape.

      **NO COVERAGE IS THE FREE TIER, NOT A REFUSAL.** `docs/product/pricing.md` sells a free tier
      that does not expire. A test that accepted `allowed is False` without reading the verdict
      would let somebody later make this mean "blocked" and turn the free tier off.

      **EVERY `State` IS EXERCISED, BECAUSE `_SETTLED` IS A TABLE LOOKUP.** A state missing from it
      raises `KeyError` inside a review rather than returning a wrong verdict — which is the right
      failure, but only if something reaches it before a customer does.
IMPORTS: pytest, quantamind.store.billing.entitlement, quantamind.verify.paid_access.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.store.billing.entitlement import Coverage, State
from quantamind.verify.paid_access import DAY_S, GRACE_DAYS, Access, Verdict, decide

PERIOD_END = 1_700_000_000
GRACE_END = PERIOD_END + GRACE_DAYS * DAY_S


def cover(state: State, *, ends: int | None = PERIOD_END, stale: bool = False) -> Coverage:
    """One account's coverage. Only the state and the period end matter here."""
    return Coverage(
        tier="team",
        state=state,
        seats_included=3,
        reason="",
        as_of=PERIOD_END - DAY_S,
        valid_through=ends,
        grace_until=None,
        stale=stale,
    )


def test_no_coverage_is_the_free_tier_and_says_so() -> None:
    """**Not a refusal.** The caller decides whether it was asking about the paid product."""
    access = decide(cover(State.NONE), at=PERIOD_END)

    assert access.verdict is Verdict.NO_SUBSCRIPTION
    assert access.allowed is False
    assert "free tier, not a refusal" in access.reason
    assert access.paid_through == 0


@pytest.mark.parametrize("state", [State.ACTIVE, State.TRIALING])
def test_paid_up_to_and_including_the_final_second(state: State) -> None:
    """`at == ends` is still paid. A `<` here bills someone for a period it then denies them."""
    assert decide(cover(state), at=PERIOD_END).verdict is Verdict.PAID
    assert decide(cover(state), at=PERIOD_END - 1).verdict is Verdict.PAID
    assert decide(cover(state), at=PERIOD_END).paid_through == PERIOD_END


def test_active_one_second_past_the_period_is_a_missed_push_not_a_payment() -> None:
    """Billing moves an account out of `active` when it stops being paid. So this is ours."""
    access = decide(cover(State.ACTIVE), at=PERIOD_END + 1)

    assert access.verdict is Verdict.STALE_RECORD
    assert access.allowed is True, "our own outage must not cut off a paying customer"
    assert "a push never arrived" in access.reason
    assert "entitlement drain" in access.reason


def test_a_stale_active_record_stops_being_believed_after_the_grace_window() -> None:
    """Held open for the window, then blocked with a reason pointing at us, not at them."""
    assert decide(cover(State.ACTIVE), at=GRACE_END).verdict is Verdict.STALE_RECORD

    lapsed = decide(cover(State.ACTIVE), at=GRACE_END + 1)
    assert lapsed.verdict is Verdict.EXPIRED
    assert lapsed.allowed is False
    assert "re-push the entitlement" in lapsed.reason


def test_past_due_keeps_access_through_the_grace_window_and_not_one_second_longer() -> None:
    """A bank's fraud hold must not take down their CI on the first failed charge."""
    assert decide(cover(State.PAST_DUE), at=PERIOD_END + 1).verdict is Verdict.IN_GRACE
    assert decide(cover(State.PAST_DUE), at=GRACE_END).verdict is Verdict.IN_GRACE

    closed = decide(cover(State.PAST_DUE), at=GRACE_END + 1)
    assert closed.verdict is Verdict.EXPIRED
    assert closed.allowed is False


def test_the_grace_window_is_measured_from_the_period_end_not_from_now() -> None:
    """A window measured from the moment we ask never closes, because every call restarts it."""
    long_after = GRACE_END + 400 * DAY_S

    assert decide(cover(State.PAST_DUE), at=long_after).verdict is Verdict.EXPIRED


def test_a_shorter_grace_moves_the_boundary_so_the_number_is_not_decoration() -> None:
    """**The constant is exercised, not merely present.**"""
    two_days = PERIOD_END + 2 * DAY_S

    assert decide(cover(State.PAST_DUE), at=two_days, grace_days=7).verdict is Verdict.IN_GRACE
    assert decide(cover(State.PAST_DUE), at=two_days, grace_days=1).verdict is Verdict.EXPIRED


def test_cancelled_is_not_expired_because_nobody_s_card_failed() -> None:
    """Two blocked accounts needing two different emails and two different conversations."""
    left = decide(cover(State.CANCELLED), at=PERIOD_END + 1)
    failed = decide(cover(State.UNPAID), at=PERIOD_END + 1)

    assert left.verdict is Verdict.CANCELED
    assert failed.verdict is Verdict.EXPIRED
    assert "was cancelled" in left.reason
    assert "worth a human contacting them" in failed.reason


def test_a_checkout_that_never_paid_is_not_a_lapsed_customer() -> None:
    """They were never a customer. Dunning them is a letter about a debt that does not exist."""
    access = decide(cover(State.INCOMPLETE), at=PERIOD_END)

    assert access.verdict is Verdict.NEVER_PAID
    assert "must not be dunned like one" in access.reason


def test_paused_is_its_own_verdict_and_not_folded_into_cancelled() -> None:
    access = decide(cover(State.PAUSED), at=PERIOD_END)

    assert access.verdict is Verdict.PAUSED
    assert access.allowed is False


@pytest.mark.parametrize("state", [one for one in State if one is not State.NONE])
def test_every_state_reaches_a_verdict_rather_than_a_KeyError(state: State) -> None:
    """`_SETTLED` is a table, and a `State` added without an entry raises INSIDE a review.

    Parametrised over the enum rather than over a written-out list, so adding a member to `State`
    adds a case here automatically instead of leaving the gap for a customer to find.
    """
    assert decide(cover(state), at=PERIOD_END).verdict in Verdict


def test_coverage_with_no_period_is_open_rather_than_instantly_expired() -> None:
    """`valid_through` is None when the push carried no period. None is not 1970."""
    for ends in (None, 0):
        access = decide(cover(State.ACTIVE, ends=ends), at=PERIOD_END)

        assert access.verdict is Verdict.PAID
        assert "no period on the record" in access.reason


def test_a_quiet_billing_service_is_named_without_closing_access() -> None:
    """`stale` is our failure to push, not their failure to pay — it degrades, it does not refuse.

    Asserting the verdict AND the sentence: without the sentence an operator sees a working
    account and never learns the drain stopped, which is the state this flag exists to surface.
    """
    quiet = decide(cover(State.ACTIVE, ends=PERIOD_END + DAY_S, stale=True), at=PERIOD_END)
    fresh = decide(cover(State.ACTIVE, ends=PERIOD_END + DAY_S), at=PERIOD_END)

    assert quiet.verdict is Verdict.PAID
    assert quiet.allowed is True, "a quiet drain is our fault; it must not close a paid account"
    # The first version of this test asserted only the verdict, and passed against a `decide` that
    # never mentioned the quiet drain at all on the PAID path — an account reading as healthy while
    # the thing keeping it healthy had stopped. The two reasons must differ.
    assert "has not pushed since its grace window closed" in quiet.reason
    assert "has not pushed" not in fresh.reason
    assert quiet.reason != fresh.reason


def test_the_flag_and_the_verdict_cannot_be_made_to_disagree() -> None:
    """A dashboard reading one and a review reading the other is the failure this refuses."""
    with pytest.raises(ValueError, match="must agree"):
        Access(True, Verdict.CANCELED, "they left")


def test_a_decision_without_a_reason_is_refused_at_construction() -> None:
    with pytest.raises(ValueError, match="cannot be shown to anybody"):
        Access(True, Verdict.PAID, "")
