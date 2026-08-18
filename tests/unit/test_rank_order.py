"""The budget, the allocation labels and the firing rule, including the case where we stay quiet.

WHAT: Asserts that ranks 1-3 are funded and everything below is COLD-but-present, that the
      firing rule is a percentile rather than an absolute score, and that a change with no history
      does not fire.
WHY:  A wrong order misses defects; a wrong threshold buries the customer or goes silent for a
      month. They are separate failures and are tested separately.

      **The no-history case is the one that matters here.** With every file at zero the ordering is
      alphabetical, and firing would present `sort(filenames)` as a judgement about risk.
IMPORTS: quantamind.rank.order, quantamind.types.ranking.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.rank.order import BUDGET, fires, percentiles, rank
from quantamind.types.ranking import Allocation


def test_ranks_one_to_three_are_funded_and_the_rest_are_cold_but_present() -> None:
    scores = {f"f{i}.py": 10 - i for i in range(6)}
    ranking = rank(scores)
    assert len(ranking.units) == 6, "cold units must be carried, not dropped"
    assert [u.allocation for u in ranking.units[:BUDGET]] == [
        Allocation.DEEP,
        Allocation.SHALLOW,
        Allocation.SHALLOW,
    ]
    assert all(u.allocation is Allocation.COLD for u in ranking.units[BUDGET:])
    assert len(ranking.funded()) == BUDGET
    assert len(ranking.cold()) == 3


def test_a_change_with_no_history_does_not_fire() -> None:
    assert fires({"a.py": 0, "b.py": 0}) is False, "an all-zero set is sort(filenames), not a rank"
    assert rank({"a.py": 0, "b.py": 0}).fired is False


def test_a_change_with_history_fires() -> None:
    assert fires({"a.py": 4, "b.py": 0}) is True


def test_the_same_shape_fires_regardless_of_absolute_volume() -> None:
    """An absolute threshold fired on 11% of one repository and 53% of another."""
    quiet = {"a.py": 2, "b.py": 1, "c.py": 0}
    busy = {"a.py": 2000, "b.py": 1000, "c.py": 0}
    assert fires(quiet) == fires(busy), "the firing rule must not depend on repository velocity"
    assert [u.rank for u in rank(quiet).units] == [u.rank for u in rank(busy).units]


def test_tied_scores_share_the_same_percentile() -> None:
    got = percentiles({"a.py": 5, "b.py": 5, "c.py": 1})
    assert got["a.py"] == got["b.py"], "a tie must not be broken by iteration order in the score"
    assert got["c.py"] < got["a.py"]


def test_the_unit_is_the_file_and_says_so() -> None:
    unit = rank({"pkg/mod.py": 3}).units[0].unit
    assert unit.site.line == 0, "line 0 is what declares this a file-level ranking"
    assert unit.qualified_name == "pkg/mod.py"


def test_a_budget_larger_than_the_change_funds_everything() -> None:
    ranking = rank({"a.py": 2, "b.py": 1}, budget=5)
    assert ranking.cold() == (), "with fewer files than budget nothing is cold"


def test_a_negative_budget_is_refused() -> None:
    with pytest.raises(ValueError):
        rank({"a.py": 1}, budget=-1)


def test_the_order_is_score_orders_order_untouched() -> None:
    from quantamind.rank.score import order as score_order

    scores = {"z.py": 3, "a.py": 3, "m.py": 9}
    assert [u.unit.qualified_name for u in rank(scores).units] == score_order(scores)


def test_an_empty_score_set_raises_rather_than_publishing_an_empty_ranking() -> None:
    """An empty Ranking renders as a clean review, so a failed diff fetch must not produce one."""
    from quantamind.rank.order import NothingToRank

    with pytest.raises(NothingToRank):
        rank({})
