"""What each tier admits, what it refuses, and the two refusals that must never become passes.

WHAT: Exercises `verify.tier_request.admissible()` across all three tiers, including the sabotages
      named in `docs/plans/feat-tier-provisioning.md`.
WHY:  **THIS DECIDES WHO GETS A PAID TIER, SO ITS REFUSALS MATTER MORE THAN ITS PASSES.** A test
      suite that only asserts the happy path would be green with every gate deleted.

      **TWO CASES ARE THE WHOLE POINT.** An unchecked repository must not be admitted to Free --
      "we could not check" and "it qualifies" must never be the same value, which is the
      `Unresolved` discipline applied to eligibility. And `payment_verified` must be unsettable,
      because a field that can be flipped to True is a field that will be, and nothing in this
      product reads a payment processor.
IMPORTS: quantamind.verify.tier_request, quantamind.verify.qualification.
"""

from __future__ import annotations

import pytest

from quantamind.verify.qualification import Verdict as RepoVerdict
from quantamind.verify.tier_request import MAX_REPOS, Request, Tier, Verdict, admissible

OK = RepoVerdict(True, ())
NO = RepoVerdict(False, ("12 stars, and the free tier needs at least 1000",))

PAID = Request(account="acme", repos=("acme/api",), seats=12, payment_ref="sub_123")


def test_team_admits_with_a_reference_and_a_seat_count() -> None:
    verdict = admissible(Tier.TEAM, PAID)
    assert verdict.admissible and verdict.reasons == ()


def test_team_refuses_without_a_payment_reference() -> None:
    """**A PAID TIER WITH NOTHING TO RECORD AGAINST IS A FREE TIER WITH EXTRA STEPS.**"""
    out = admissible(Tier.TEAM, Request(account="acme", repos=("acme/api",), seats=12))
    assert not out.admissible
    assert any("payment reference" in why for why in out.reasons)


def test_team_refuses_zero_seats() -> None:
    out = admissible(Tier.TEAM, Request(account="acme", repos=("acme/api",), payment_ref="s"))
    assert out.reasons == ("0 seats; a paid tier is billed per developer and needs a count",)


def test_enterprise_refuses_without_an_organisation() -> None:
    """**SABOTAGE 4.** Enterprise's one code-visible feature reads from an org's `.quantamind`."""
    out = admissible(Tier.ENTERPRISE, PAID)
    assert not out.admissible
    assert any("organisation" in why for why in out.reasons)


def test_enterprise_admits_with_one() -> None:
    out = admissible(
        Tier.ENTERPRISE,
        Request(account="acme", repos=("acme/api",), seats=40, payment_ref="s", org="acme"),
    )
    assert (out.admissible, out.reasons, out.payment_verified) == (True, (), False)


def test_free_admits_only_an_eligible_repository() -> None:
    req = Request(account="acme", repos=("acme/api",))
    out = admissible(Tier.FREE, req, free_verdicts={"acme/api": OK})
    assert (out.admissible, out.reasons) == (True, ())


def test_free_carries_every_eligibility_reason_through() -> None:
    """A caller told one reason fixes it and is refused again. Every reason travels."""
    req = Request(account="acme", repos=("acme/api",))
    out = admissible(Tier.FREE, req, free_verdicts={"acme/api": NO})
    assert not out.admissible
    assert out.reasons == ("acme/api: 12 stars, and the free tier needs at least 1000",)


def test_an_unchecked_repository_is_refused_not_assumed_eligible() -> None:
    """**SABOTAGE 1, AND THE MOST IMPORTANT TEST IN THIS FILE.**

    With no verdict supplied, a naive implementation admits — nothing said no. "We could not check"
    and "it qualifies" must not be the same value.
    """
    out = admissible(Tier.FREE, Request(account="acme", repos=("acme/api",)), free_verdicts={})
    assert not out.admissible
    assert any("never checked" in why for why in out.reasons)


def test_a_paid_body_posted_to_free_is_still_gated() -> None:
    """**SABOTAGE 2.** Paying fields must not carry a request past the eligibility rules."""
    out = admissible(Tier.FREE, PAID, free_verdicts={"acme/api": NO})
    assert not out.admissible


def test_one_malformed_repository_refuses_the_whole_request() -> None:
    """**SABOTAGE 3.** Partial provisioning leaves a customer paying for what was not admitted."""
    out = admissible(
        Tier.TEAM,
        Request(account="acme", repos=("acme/api", "not-a-repo"), seats=2, payment_ref="s"),
    )
    assert not out.admissible
    assert any("not-a-repo" in why for why in out.reasons), (
        "the bad name must be NAMED, not counted"
    )


def test_a_duplicate_repository_is_refused() -> None:
    out = admissible(
        Tier.TEAM, Request(account="acme", repos=("a/b", "a/b"), seats=1, payment_ref="s")
    )
    assert out.reasons == ("the same repository appears twice in one request",)


def test_an_empty_account_is_refused() -> None:
    out = admissible(Tier.TEAM, Request(account="  ", repos=("a/b",), seats=1, payment_ref="s"))
    assert out.reasons == ("no account was named, and an installation belongs to one",)


def test_the_repository_ceiling_is_enforced() -> None:
    many = tuple(f"acme/r{n}" for n in range(MAX_REPOS + 1))
    out = admissible(Tier.TEAM, Request(account="a", repos=many, seats=1, payment_ref="s"))
    assert out.reasons == (
        f"{MAX_REPOS + 1} repositories in one request; the ceiling is {MAX_REPOS}",
    )


def test_payment_verified_cannot_be_set_true() -> None:
    """**THE TYPE REFUSES THE LIE.** B3 is parked; nothing here reads a payment processor."""
    with pytest.raises(ValueError, match="payment_verified cannot be True"):
        Verdict(True, (), payment_verified=True)


def test_a_refusal_without_a_reason_is_refused() -> None:
    with pytest.raises(ValueError, match="refused without a reason"):
        Verdict(False, ())
