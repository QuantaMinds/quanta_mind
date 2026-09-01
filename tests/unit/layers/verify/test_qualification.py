"""Verification that free-tier eligibility names every failing rule, and refuses on none silently.

WHAT: Drives `verify/qualification.qualifies` across each rule and their combinations, and
      `Verdict`'s own invariant that eligibility and reasons cannot disagree.
WHY:  **AN ELIGIBILITY LIST NOBODY CHECKS IS A PROMISE; THIS IS A DECISION.** Every rule in
      `docs/plans/roadmap/product-build.md` B8 is readable from the GitHub API at install time, so
      it can be enforced before anything is provisioned.

      **EVERY FAILING RULE IS RETURNED, NEVER JUST THE FIRST.** A prospect told "not eligible",
      who fixes one thing and is told it again, learns the list by attrition. The test for this is
      a repository that fails four rules at once and must hear about four.

      **AND A REFUSAL WITHOUT A REASON IS NOT A VERDICT.** `Verdict.__post_init__` refuses to
      construct one, because "no" with no cause is the silence this codebase exists to reject.

      **BOTH ACTIVITY RULES ARE REQUIRED**, and the test proves each alone is insufficient: a
      repository busy once and abandoned passes the span, and a repository pushed yesterday with
      a week of history passes recency. Either alone would admit one of them.
IMPORTS: pytest, quantamind.verify.qualification.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.verify.qualification import (
    FREE_REPOS_TOTAL,
    MIN_ACTIVE_DAYS,
    MIN_CONTRIBUTORS,
    MIN_STARS,
    Facts,
    Verdict,
    qualifies,
)

STARS, PEOPLE, DAYS, TOTAL = 1_000, 50, 180, 40
"""The published thresholds, written out. Reading the constants would pass at any value."""


def _facts(**over: object) -> Facts:
    base: dict[str, object] = {
        "repo": "acme/payments",
        "private": False,
        "stars": 4_200,
        "contributors": 120,
        "active_days": 900,
        "pushed_days_ago": 2,
    }
    base.update(over)
    return Facts(**base)  # type: ignore[arg-type]  — a test fixture, checked by the dataclass


def _verdict(**over: object) -> Verdict:
    return qualifies(_facts(**over), owner_already_free=False, repos_taken=0)


def test_the_published_thresholds_are_the_shipped_ones() -> None:
    assert (MIN_STARS, MIN_CONTRIBUTORS, MIN_ACTIVE_DAYS, FREE_REPOS_TOTAL) == (
        STARS,
        PEOPLE,
        DAYS,
        TOTAL,
    )


def test_a_qualifying_repository_is_accepted_with_no_reasons() -> None:
    """The control. Without it every rule below could pass by refusing everything."""
    verdict = _verdict()

    assert verdict.eligible is True
    assert verdict.reasons == ()


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("private", True, "private"),
        ("stars", STARS - 1, "stars"),
        ("contributors", PEOPLE - 1, "contributor"),
        ("active_days", DAYS - 1, "days of history"),
        ("pushed_days_ago", 400, "last pushed"),
    ],
)
def test_each_rule_refuses_on_its_own(field: str, value: object, expected: str) -> None:
    verdict = _verdict(**{field: value})

    assert verdict.eligible is False
    assert any(expected in reason for reason in verdict.reasons), verdict.reasons


@pytest.mark.parametrize("field", ["stars", "contributors", "active_days"])
def test_exactly_at_each_threshold_is_accepted(field: str) -> None:
    """The boundary is inclusive: 1,000 stars qualifies, 999 does not."""
    at = {"stars": STARS, "contributors": PEOPLE, "active_days": DAYS}[field]

    assert _verdict(**{field: at}).eligible is True


def test_a_repository_busy_once_and_abandoned_is_refused() -> None:
    """Span alone is not activity. Nine hundred days of history, last pushed two years ago."""
    verdict = _verdict(active_days=900, pushed_days_ago=730)

    assert verdict.eligible is False
    assert any("last pushed" in reason for reason in verdict.reasons)


def test_a_brand_new_busy_repository_is_refused() -> None:
    """Recency alone is not history. Pushed yesterday, seven days old."""
    verdict = _verdict(active_days=7, pushed_days_ago=1)

    assert verdict.eligible is False
    assert any("days of history" in reason for reason in verdict.reasons)


def test_every_failing_rule_is_named_not_only_the_first() -> None:
    """Four failures must produce four reasons, so a prospect learns the list at once."""
    verdict = qualifies(
        _facts(private=True, stars=10, contributors=2, active_days=3),
        owner_already_free=False,
        repos_taken=0,
    )

    assert len(verdict.reasons) == 4, verdict.reasons


def test_one_free_repository_per_account() -> None:
    verdict = qualifies(_facts(), owner_already_free=True, repos_taken=0)

    assert verdict.eligible is False
    assert any("one per account" in reason for reason in verdict.reasons)


def test_the_offer_closes_when_the_places_are_taken() -> None:
    verdict = qualifies(_facts(), owner_already_free=False, repos_taken=TOTAL)

    assert verdict.eligible is False
    assert any(f"all {TOTAL} places" in reason for reason in verdict.reasons)


def test_the_last_place_is_still_open() -> None:
    """39 taken is open, 40 is closed. Off by one here silently closes the offer early."""
    assert qualifies(_facts(), owner_already_free=False, repos_taken=TOTAL - 1).eligible is True


def test_a_refusal_without_a_reason_cannot_be_constructed() -> None:
    """`no` with no cause is the silence this codebase rejects."""
    with pytest.raises(ValueError, match="without a reason"):
        Verdict(eligible=False, reasons=())


def test_an_acceptance_carrying_reasons_cannot_be_constructed() -> None:
    with pytest.raises(ValueError, match="not a verdict"):
        Verdict(eligible=True, reasons=("something",))
