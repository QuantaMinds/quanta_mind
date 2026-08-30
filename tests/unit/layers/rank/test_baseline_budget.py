"""Verification that the chance baseline is computed over the budget the product actually spends.

WHAT: Drives `rank/baseline.chance_hit` — the probability a random read of `budget` files touches
      a file a later fix returns to — at its default and against hand-computed values.
WHY:  **THE BASELINE IS THE NUMBER EVERY CLAIM IN THIS PROJECT IS MEASURED AGAINST, AND ITS
      BUDGET WAS FREELY MUTABLE.** `DEFAULT_BUDGET` is the three files the ranker funds; a
      baseline computed over a different budget is not the comparison the evidence ledger quotes.
      Setting it to 0 makes the chance of hitting anything zero, which would make every measured
      improvement look infinite. Every tier stayed green for both mutations.

      **THE VALUES ARE HAND-COMPUTED, NOT RECORDED FROM THE FUNCTION.** Reading today's output
      into a golden would pin whatever it does rather than what it should do. With 10 files, 1
      target and a budget of 3, the chance of missing is 9/10 x 8/9 x 7/8 = 7/10, so the chance
      of hitting is 3/10 exactly — budget/files, as it must be for a single target.
IMPORTS: pytest, quantamind.rank.baseline.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.rank.baseline import chance_hit

BUDGET = 3
"""The funded ranks. Written out; `DEFAULT_BUDGET` would read the value under test."""


def test_the_default_budget_is_the_three_ranks_the_ranker_funds() -> None:
    """A single target in ten files is hit exactly budget/files of the time."""
    assert chance_hit(10, 1) == pytest.approx(0.3)


def test_the_default_matches_passing_the_budget_explicitly() -> None:
    """Behavioural: the default is wired through, not merely declared beside the function."""
    assert chance_hit(20, 2) == chance_hit(20, 2, budget=BUDGET)


def test_a_different_budget_gives_a_different_answer() -> None:
    """The false-positive direction: a function ignoring `budget` would pass everything above."""
    assert chance_hit(10, 1, budget=1) == pytest.approx(0.1)
    assert chance_hit(10, 1, budget=5) == pytest.approx(0.5)


def test_a_budget_covering_every_non_target_is_certain() -> None:
    """Too few non-targets to fill the read: some target is seen no matter what."""
    assert chance_hit(4, 2, budget=3) == 1.0


def test_impossible_events_raise_rather_than_returning_a_plausible_number() -> None:
    """A fabricated baseline in a customer-facing number is the failure being prevented."""
    with pytest.raises(ValueError, match="is not an event"):
        chance_hit(0, 1)
    with pytest.raises(ValueError, match="returned-to file"):
        chance_hit(3, 4)
    with pytest.raises(ValueError, match="budget cannot be negative"):
        chance_hit(10, 1, budget=-1)
