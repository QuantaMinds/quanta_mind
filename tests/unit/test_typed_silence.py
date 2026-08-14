"""Unit tier: the types refuse to represent a silence that cannot be read.

WHAT: Asserts that the constructions this project has been bitten by are impossible to
      build -- a nameless unit, an unadjudicated finding reaching publication, a coverage
      ratio of 1.0 on a review that examined nothing.
WHY:  Rule 3 says silence must be typed, and a rule enforced only by discipline is a wish.
      These are the specific collapses that produce a plausible clean review: "we found
      nothing" reported identically to "we could not look", and an empty denominator
      reported as full coverage. Each is asserted here as a refusal, not a convention.
IMPORTS: quantamind.types (change, finding, ranking, review, verdict), pytest. Tier 1.
CONSUMED BY: justfile (`just check`), .github/workflows/ci.yml.
"""

from __future__ import annotations

import pytest

from quantamind.types.change import ChangedUnit, Language, PullRequest, Repo
from quantamind.types.finding import Claim, ClaimKind, Finding, Verdict
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


def test_a_semantic_claim_cannot_be_marked_confirmed() -> None:
    """The verifier is a parser. Letting it confirm a semantic claim is the whole failure."""
    with pytest.raises(ValueError, match="cannot be CONFIRMED"):
        Claim(
            kind=ClaimKind.SEMANTIC,
            site=Site("pkg/mod.py", 20),
            assertion="the retry loop is wrong",
            verdict=Verdict.CONFIRMED,
        )


def test_a_contradicted_claim_sinks_its_whole_finding() -> None:
    """A model that described code that is not there was not reading the code it describes."""
    finding = Finding(
        site=Site("pkg/mod.py", 71),
        body="the early return skips the ledger write",
        claims=(
            Claim(
                kind=ClaimKind.SYMBOL_EXISTS,
                site=Site("pkg/mod.py", 71),
                assertion="process_refund exists",
                verdict=Verdict.CONTRADICTED,
            ),
        ),
    )
    assert finding.publishable is False


def test_a_verified_finding_is_labelled_differently_from_a_suggestion() -> None:
    """Undecidable is not confirmed, and the comment must not present them the same way."""
    suggestion = Finding(
        site=Site("pkg/mod.py", 30),
        body="this retry may double-charge",
        claims=(
            Claim(
                kind=ClaimKind.SEMANTIC,
                site=Site("pkg/mod.py", 30),
                assertion="the retry is unsafe",
                verdict=Verdict.UNDECIDABLE,
            ),
        ),
    )
    assert suggestion.publishable is True
    assert suggestion.label() == "suggested"
    assert suggestion.is_verified is False


def test_a_review_refuses_findings_that_verify_never_saw() -> None:
    """An unadjudicated finding reaching a Review is indistinguishable from verify/ being off.

    This is the sabotage: the finding is well-formed, the body is real, and the only thing
    missing is that nothing checked it. The type refuses rather than publishing it.
    """
    unchecked = Finding(
        site=Site("pkg/mod.py", 71),
        body="the early return skips the ledger write",
        claims=(
            Claim(
                kind=ClaimKind.ORDER_OF_STATEMENTS,
                site=Site("pkg/mod.py", 71),
                assertion="line 71 precedes line 88",
            ),
        ),
    )
    assert unchecked.publishable is False
    with pytest.raises(ValueError, match="never adjudicated"):
        Review(
            pull_request=PR,
            coverage=CoverageLine(ranking=Ranking(), files_checked=1),
            budget=Budget(max_requests=3),
            findings=(unchecked,),
            spoke=True,
        )


def test_a_silent_review_cannot_claim_to_have_spoken() -> None:
    """A coverage-only review is spoke=False. The two are different products of the pipeline."""
    with pytest.raises(ValueError, match="claims to have spoken"):
        Review(
            pull_request=PR,
            coverage=CoverageLine(ranking=Ranking(), files_checked=2),
            budget=Budget(max_requests=3),
            spoke=True,
        )
