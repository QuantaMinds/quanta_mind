"""Unit tier: the coverage line reports three states and cannot disagree with the ranking.

WHAT: Asserts the arithmetic and the refusals of `CoverageLine` -- an empty review reporting no
      coverage rather than full, cold units named rather than counted, a residual refused
      without a list, and a line derived from a ranking matching it by construction.
WHY:  The coverage line is the product. Every failure asserted here produces a plausible clean
      review: full coverage on an empty denominator, "eight functions not read" as untyped
      silence, a line that contradicts the ranking it describes. Each is refused by the type
      rather than left to discipline.
IMPORTS: quantamind.types (change, ranking, review, verdict), pytest. Tier 1, no mocks.
CONSUMED BY: justfile (`just check`), .github/workflows/ci.yml.
"""

from __future__ import annotations

import pytest

from quantamind.types.change import ChangedUnit, Diff, Language, PullRequest, Repo
from quantamind.types.ranking import Allocation, RankedUnit, Ranking, Score
from quantamind.types.review import CoverageLine
from quantamind.types.verdict import Construct, Reason, Site, Unresolved

REPO = Repo(host="github.com", name="acme/widget")
PR = PullRequest(repo=REPO, number=7, head_sha="0123456789abcdef", base_sha="fedcba9876543210")


def _cold(name: str, rank: int) -> RankedUnit:
    """A cold ranked unit, for building coverage lines in tests."""
    return RankedUnit(
        unit=ChangedUnit(
            site=Site(f"pkg/{name}.py", 1),
            qualified_name=f"pkg.{name}",
            language=Language.PYTHON,
        ),
        rank=rank,
        score=Score(value=0.0, percentile=0.1),
        allocation=Allocation.COLD,
    )


def test_coverage_of_an_empty_diff_is_zero_not_one() -> None:
    """No denominator means no coverage claim.

    The dangerous version returns 1.0: a review that read nothing reports having understood
    everything, and it is indistinguishable from a genuinely complete read.
    """
    assert Diff(pull_request=PR).coverage_ratio() == 0.0
    assert CoverageLine(units_checked=0, files_checked=0).ratio() == 0.0


def test_coverage_counts_the_unresolved_in_its_denominator() -> None:
    """Two of three understood is 2/3, not 2/2. Excluding failures inflates every review."""
    line = CoverageLine(
        units_checked=2,
        files_checked=1,
        unresolved=(Unresolved(Site("a.py", 1), Reason.DYNAMIC_DISPATCH, Construct.CALL_SITE),),
    )
    assert line.total_considered == 3
    assert line.ratio() == pytest.approx(2 / 3)
    assert line.is_complete is False


def test_cold_units_are_named_not_merely_counted() -> None:
    """Three states, not two: read, unresolvable, and never funded by the budget.

    Cold units go in the denominator because a unit the budget skipped was still part of the
    change. A version that omitted them would report a review reading three of eleven
    functions as complete coverage -- which is the claim this product exists to refuse.
    """
    line = CoverageLine(
        units_checked=3,
        files_checked=2,
        cold=(_cold("send_email", 4), _cold("validate", 5)),
        cold_not_listed=6,
        unresolved=(Unresolved(Site("gen.py", 0), Reason.GENERATED_FILE, Construct.FILE),),
    )
    assert line.total_considered == 12
    assert line.ratio() == pytest.approx(3 / 12)
    assert line.is_complete is False


def test_coverage_with_cold_units_is_not_complete_even_with_nothing_unresolved() -> None:
    """Everything parsed cleanly and the budget still skipped most of it. Not complete."""
    line = CoverageLine(units_checked=3, files_checked=2, cold=("a.b", "a.c"), cold_not_listed=6)
    assert not line.unresolved
    assert line.is_complete is False
    assert line.ratio() == pytest.approx(3 / 11)


def test_a_residual_without_a_list_is_refused() -> None:
    """ "Eight functions not read" is untyped silence wearing a number.

    A residual truncates a list; it does not replace one. Allowing it alone would let a review
    report the same unusable silence this product exists to argue against.
    """
    with pytest.raises(ValueError, match="not a substitute"):
        CoverageLine(units_checked=3, files_checked=1, cold_not_listed=8)


def test_a_coverage_line_derived_from_a_ranking_cannot_disagree_with_it() -> None:
    """Built by hand this object can contradict the ranking; derived, it cannot.

    Same argument as an outcome being a new row rather than an edit: one source of truth beats
    two that are usually consistent.
    """
    units = tuple(
        RankedUnit(
            unit=ChangedUnit(
                site=Site(f"pkg/m{i}.py", 1),
                qualified_name=f"pkg.m{i}",
                language=Language.PYTHON,
            ),
            rank=i,
            score=Score(value=float(20 - i), percentile=0.9),
            allocation=Allocation.DEEP
            if i == 1
            else (Allocation.SHALLOW if i <= 3 else Allocation.COLD),
        )
        for i in range(1, 12)
    )
    line = CoverageLine.from_ranking(Ranking(units=units, fired=True), files_checked=4)
    assert line.units_checked == 3
    assert len(line.cold) == 8
    assert line.cold_not_listed == 0
    assert line.total_considered == 11
    assert line.ratio() == pytest.approx(3 / 11)
    assert line.is_complete is False
    assert [u.rank for u in line.cold] == list(range(4, 12))


def test_a_long_cold_list_truncates_by_rank_and_keeps_a_residual() -> None:
    """Least cold first, so a truncated list keeps the units most nearly worth reading."""
    units = tuple(
        RankedUnit(
            unit=ChangedUnit(
                site=Site(f"pkg/m{i}.py", 1),
                qualified_name=f"pkg.m{i}",
                language=Language.PYTHON,
            ),
            rank=i,
            score=Score(value=float(40 - i), percentile=0.9),
            allocation=Allocation.DEEP if i == 1 else Allocation.COLD,
        )
        for i in range(1, 21)
    )
    line = CoverageLine.from_ranking(
        Ranking(units=units, fired=True), files_checked=6, list_limit=5
    )
    assert len(line.cold) == 5
    assert line.cold_not_listed == 14
    assert [u.rank for u in line.cold] == [2, 3, 4, 5, 6]
    assert line.total_considered == 20
