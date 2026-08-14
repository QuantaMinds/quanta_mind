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


def _ranked(i: int, allocation: Allocation) -> RankedUnit:
    return RankedUnit(
        unit=ChangedUnit(
            site=Site(f"pkg/m{i}.py", 1),
            qualified_name=f"pkg.m{i}",
            language=Language.PYTHON,
        ),
        rank=i,
        score=Score(value=float(40 - i), percentile=0.9),
        allocation=allocation,
    )


def _ranking(funded: int, cold: int) -> Ranking:
    """A ranking with `funded` units receiving a call and `cold` receiving none."""
    units = [
        _ranked(i, Allocation.DEEP if i == 1 else Allocation.SHALLOW) for i in range(1, funded + 1)
    ]
    units += [_ranked(i, Allocation.COLD) for i in range(funded + 1, funded + cold + 1)]
    return Ranking(units=tuple(units), fired=bool(funded))


def test_coverage_of_an_empty_review_is_zero_not_one() -> None:
    """No denominator means no coverage claim.

    The dangerous version returns 1.0: a review that read nothing reports having understood
    everything, indistinguishable from a genuinely complete read.
    """
    assert Diff(pull_request=PR).coverage_ratio() == 0.0
    assert CoverageLine(ranking=Ranking(), files_checked=0).ratio() == 0.0


def test_coverage_counts_the_unresolved_in_its_denominator() -> None:
    """Two of three understood is 2/3, not 2/2. Excluding failures inflates every review."""
    line = CoverageLine(
        ranking=_ranking(funded=2, cold=0),
        files_checked=1,
        unresolved=(Unresolved(Site("a.py", 1), Reason.DYNAMIC_DISPATCH, Construct.CALL_SITE),),
    )
    assert line.total_considered == 3
    assert line.ratio() == pytest.approx(2 / 3)
    assert line.is_complete is False


def test_cold_units_are_named_not_merely_counted() -> None:
    """ "Eight functions not read" is untyped silence wearing a number.

    A named list is actionable; a count is the thing this product accuses competitors of.
    """
    line = CoverageLine(ranking=_ranking(funded=3, cold=8), files_checked=2)
    assert line.units_checked == 3
    assert [u.unit.qualified_name for u in line.cold][:2] == ["pkg.m4", "pkg.m5"]
    assert line.total_considered == 11
    assert line.ratio() == pytest.approx(3 / 11)
    assert line.is_complete is False


def test_a_line_cannot_be_built_that_disagrees_with_its_ranking() -> None:
    """The counts are a VIEW, so there is no field to set inconsistently.

    An earlier version stored them beside a `from_ranking` helper callers were expected to
    prefer -- a rule in a docstring, which is what this project keeps finding fails. Holding
    the ranking makes the disagreement unrepresentable rather than discouraged.
    """
    ranking = _ranking(funded=3, cold=8)
    line = CoverageLine(ranking=ranking, files_checked=4)
    assert line.units_checked == len(ranking.funded())
    assert line.cold_not_listed == 0
    assert len(line.cold) == len(ranking.cold())
    assert line.total_considered == len(ranking.units)
    assert not hasattr(line, "__dict__") or "units_checked" not in getattr(line, "__dict__", {})


def test_a_long_cold_list_truncates_by_rank_and_keeps_a_residual() -> None:
    """Least cold first, so a truncated list keeps the units most nearly worth reading."""
    line = CoverageLine(ranking=_ranking(funded=1, cold=19), files_checked=6, list_limit=5)
    assert len(line.cold) == 5
    assert line.cold_not_listed == 14
    assert [u.rank for u in line.cold] == [2, 3, 4, 5, 6]
    assert line.total_considered == 20


def test_a_zero_list_limit_is_refused() -> None:
    """A line naming no cold units at all is the silence this type exists to end."""
    with pytest.raises(ValueError, match="at least 1"):
        CoverageLine(ranking=_ranking(funded=3, cold=4), files_checked=2, list_limit=0)


def test_complete_coverage_requires_no_cold_units_at_all() -> None:
    """Everything parsed cleanly and the budget still skipped most of it. Not complete."""
    assert CoverageLine(ranking=_ranking(3, 8), files_checked=2).is_complete is False
    assert CoverageLine(ranking=_ranking(3, 0), files_checked=2).is_complete is True
