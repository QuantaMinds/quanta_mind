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


def test_a_no_history_change_funds_nothing_and_fabricates_no_order() -> None:
    """Every score ties at zero, so `(-score, path)` falls back to path — alphabetical, not risk."""
    from quantamind.types.ranking import Allocation, Discrimination

    ranking = rank({"src/pay/refund.py": 0, "src/pay/__init__.py": 0, "tests/t.py": 0})
    assert ranking.discrimination is Discrimination.NO_HISTORY
    assert ranking.ranked() is False
    assert ranking.fired is False
    assert ranking.funded() == (), "an alphabetical top-3 must not be published as a ranking"
    assert all(u.allocation is Allocation.COLD for u in ranking.units)
    assert len(ranking.units) == 3, "the files are still carried for the coverage line"


def test_a_ranked_change_still_funds_the_budget() -> None:
    from quantamind.types.ranking import Discrimination

    ranking = rank({"a.py": 9, "b.py": 4, "c.py": 1, "d.py": 0})
    assert ranking.discrimination is Discrimination.ORDERED
    assert ranking.ranked() is True
    assert [u.unit.qualified_name for u in ranking.funded()] == ["a.py", "b.py", "c.py"]


def test_flat_nonzero_history_still_ranks_because_history_exists() -> None:
    from quantamind.types.ranking import Discrimination

    ranking = rank({"a.py": 3, "b.py": 3})
    assert ranking.discrimination is Discrimination.FLAT_NONZERO
    assert ranking.ranked() is True, "flat is not the same as absent; the files have been touched"


def test_funded_is_empty_on_a_no_history_ranking_even_if_the_labels_say_otherwise() -> None:
    """Two mechanisms stop a fabricated top-3, and each needs its own test.

    `rank()` labels every unit COLD when nothing was ranked, AND `Ranking.funded()` returns nothing
    when `ranked()` is False. Sabotaging either one alone left the suite green, because the other
    still produced the right answer — so this exercises the second directly, by handing `Ranking` a
    NO_HISTORY discrimination with funded-looking labels.
    """
    from quantamind.types.change import ChangedUnit, Language
    from quantamind.types.ranking import (
        Allocation,
        Discrimination,
        RankedUnit,
        Ranking,
        Score,
    )
    from quantamind.types.verdict import Site

    def unit(name: str, rank_: int, allocation: Allocation) -> RankedUnit:
        return RankedUnit(
            unit=ChangedUnit(
                site=Site(path=name, line=0), qualified_name=name, language=Language.PYTHON
            ),
            rank=rank_,
            score=Score(value=0.0, percentile=1.0),
            allocation=allocation,
        )

    ranking = Ranking(
        units=(unit("a.py", 1, Allocation.DEEP), unit("b.py", 2, Allocation.SHALLOW)),
        fired=False,
        discrimination=Discrimination.NO_HISTORY,
    )
    assert ranking.funded() == (), (
        "the discrimination must override the labels, not agree with them"
    )


def test_the_gate_without_a_baseline_is_the_rule_the_research_rejected() -> None:
    """`fires(scores)` with no baseline is the ABSOLUTE threshold, and it must stay documented.

    Measured on trpc/trpc it fired on 198 of 200 real changes. The fallback exists for a caller
    with no repository index, not as a default anyone should ship, and this test pins the
    difference so the two cannot be confused by a future edit.
    """
    from quantamind.rank.order import fires

    scores = {"hot.ts": 3, "cold.ts": 0}
    assert fires(scores) is True, "with no baseline, any history at all speaks"
    assert fires(scores, baseline=3) is True, "at the floor is IN the decile"
    assert fires(scores, baseline=4) is False, "below the floor is silence"
    assert fires({"a.ts": 0, "b.ts": 0}, baseline=0) is False, "no history never speaks"
