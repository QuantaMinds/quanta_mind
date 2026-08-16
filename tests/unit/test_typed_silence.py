"""Unit tier: the types refuse to represent a silence that cannot be read.

WHAT: Asserts that the constructions this project has been bitten by are impossible to
      build -- a nameless unit, an unreadable coverage record, a coverage ratio of 1.0 on a
      review that examined nothing, and a model claim smuggled into a Review.
WHY:  Rule 3 says silence must be typed, and a rule enforced only by discipline is a wish.
      These are the specific collapses that produce a plausible clean review: "we found
      nothing" reported identically to "we could not look", and an empty denominator
      reported as full coverage. Each is asserted here as a refusal, not a convention.
IMPORTS: quantamind.types (change, ranking, review, verdict), pytest. Tier 1.
CONSUMED BY: justfile (`just check`), .github/workflows/ci.yml.
"""

from __future__ import annotations

import pytest

from quantamind.types.change import ChangedUnit, Language, PullRequest, Repo
from quantamind.types.ranking import Allocation, Budget, RankedUnit, Ranking, Score
from quantamind.types.review import CoverageLine, Review
from quantamind.types.verdict import Construct, Reason, Site, Unresolved


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


REPO = Repo(host="github.com", name="acme/widget")
PR = PullRequest(repo=REPO, number=7, head_sha="0123456789abcdef", base_sha="fedcba9876543210")


def test_a_unit_cannot_be_built_without_a_name() -> None:
    """A nameless unit is an Unresolved wearing the wrong type."""
    with pytest.raises(ValueError, match="emit an Unresolved"):
        ChangedUnit(site=Site("pkg/mod.py", 10), qualified_name="", language=Language.PYTHON)


def test_unresolved_renders_what_and_why_not_just_where() -> None:
    """A coverage line naming a path without a reason tells a reader nothing actionable."""
    record = Unresolved(
        site=Site("pkg/registry.py", 88),
        reason=Reason.RUNTIME_REGISTRATION,
        construct=Construct.CALL_SITE,
    )
    assert record.render() == "call site at pkg/registry.py:88 — runtime registration"


def test_a_review_that_examined_nothing_reports_no_coverage_not_full_coverage() -> None:
    """An empty denominator must not divide into 1.0.

    This is the collapse the module docstring names and nothing asserted until now: a review
    that considered zero units has examined none of them, and a ratio that reads 100% on that
    input is the most confident possible way of saying nothing happened.
    """
    empty = CoverageLine(ranking=Ranking(), files_checked=0)
    assert empty.total_considered == 0
    assert empty.ratio() == 0.0
    assert empty.is_complete is False


def test_cold_units_are_named_not_counted() -> None:
    """ "Eight functions not read" is untyped silence wearing a number.

    The reader has to be able to say "read that one anyway", which needs the names. Past the
    limit the count is still reported, so truncation never passes for completeness.
    """
    ranking = Ranking(units=tuple(_cold(f"m{i}", i) for i in range(1, 9)))
    line = CoverageLine(ranking=ranking, files_checked=8, list_limit=3)

    assert [u.unit.qualified_name for u in line.cold] == ["pkg.m1", "pkg.m2", "pkg.m3"]
    assert line.cold_not_listed == 5
    assert line.units_checked == 0
    assert line.ratio() == 0.0


def test_a_coverage_line_must_name_at_least_one_cold_unit() -> None:
    """A limit of zero reports the count and none of the names, which is the banned shape."""
    with pytest.raises(ValueError, match="untyped silence"):
        CoverageLine(ranking=Ranking(), files_checked=1, list_limit=0)


def test_a_review_cannot_carry_a_model_claim_at_all() -> None:
    """The product publishes coverage, and the type is what enforces it.

    Seven review designs failed pre-registered bars -- 207 findings, 5.80% correct -- so no
    `infer/` ships. `Review` once had `findings` and `spoke` guarded by two validations, and
    with nothing able to populate them neither guard could fire: an unreachable check and a
    passing one print the same thing. The fields are gone, so the smuggling attempt below is
    refused by the dataclass rather than by a rule someone has to remember.
    → `docs/product/review-half-record.md`
    """
    with pytest.raises(TypeError, match="findings"):
        Review(  # type: ignore[call-arg]  # the point of the test is that this signature is gone
            pull_request=PR,
            coverage=CoverageLine(ranking=Ranking(), files_checked=1),
            budget=Budget(max_requests=3),
            findings=("the early return skips the ledger write",),
        )


def test_a_review_records_that_no_model_ran() -> None:
    """ "We call no model" must be falsifiable, or it is marketing.

    `ran_model` reads the ledger, not the configuration, so if inference were ever wired up by
    accident this flips. That is the whole reason the ledger outlived the findings.
    """
    review = Review(
        pull_request=PR,
        coverage=CoverageLine(ranking=Ranking(), files_checked=2),
        budget=Budget(max_requests=3),
    )
    assert review.ran_model is False
    assert review.overspent is False
