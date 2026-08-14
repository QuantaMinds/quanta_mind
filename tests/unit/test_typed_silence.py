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

from quantamind.types.change import ChangedUnit, Diff, Language, PullRequest, Repo
from quantamind.types.finding import Claim, ClaimKind, Finding, Verdict
from quantamind.types.ranking import Budget
from quantamind.types.review import CoverageLine, Review
from quantamind.types.verdict import Construct, Reason, Site, Unresolved

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


def test_a_semantic_claim_cannot_be_marked_confirmed() -> None:
    """The verifier is a parser. Letting it confirm a semantic claim is the whole failure."""
    with pytest.raises(ValueError, match="cannot be CONFIRMED"):
        Claim(
            kind=ClaimKind.SEMANTIC,
            site=Site("pkg/mod.py", 20),
            assertion="the retry loop is wrong",
            verdict=Verdict.CONFIRMED,
        )


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
            coverage=CoverageLine(units_checked=1, files_checked=1),
            budget=Budget(max_requests=3),
            findings=(unchecked,),
            spoke=True,
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


def test_a_silent_review_cannot_claim_to_have_spoken() -> None:
    """A coverage-only review is spoke=False. The two are different products of the pipeline."""
    with pytest.raises(ValueError, match="claims to have spoken"):
        Review(
            pull_request=PR,
            coverage=CoverageLine(units_checked=3, files_checked=2),
            budget=Budget(max_requests=3),
            spoke=True,
        )


def test_cold_units_are_named_not_merely_counted() -> None:
    """Three states, not two: read, unresolvable, and never funded by the budget.

    Cold units go in the denominator because a unit the budget skipped was still part of the
    change. A version that omitted them would report a review reading three of eleven
    functions as complete coverage -- which is the claim this product exists to refuse.
    """
    line = CoverageLine(
        units_checked=3,
        files_checked=2,
        cold=("pkg.mod.send_email", "pkg.mod.validate"),
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
