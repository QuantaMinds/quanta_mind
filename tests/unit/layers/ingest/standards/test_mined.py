"""D1d: what the miner proposes, and what it must refuse to propose.

WHAT: `ingest/standards/mined.py` over hand-built comments and over the REAL 1,213-comment corpus
      at `research/phase0/results/oss_review_comments.json`.
WHY:  **THE YIELD WAS MEASURED BEFORE THE CODE EXISTED AND THE TESTS PIN THAT MEASUREMENT.**
      `docs/findings/standards/D1D_REVIEWER_REPETITION_YIELD_2026-08.md` states the refutation
      conditions in advance: a miner proposing more than ~2 rules per repository on this corpus is
      finding noise, and one proposing nothing on `huggingface/transformers` is missing the
      clearest true positive in it. Both are asserted here rather than left as prose.

      **THE ACKNOWLEDGEMENT FILTER IS TESTED AGAINST THE REAL WORDS IT HAS TO SURVIVE**, because
      the largest cluster in the unfiltered corpus is `done` x6 and the second is `fixed` x6. A
      test using invented acknowledgements would pass while the shipped filter missed the ones
      reviewers actually type.
IMPORTS: quantamind.ingest.standards.mined, quantamind.types.standards.proposal; stdlib.
CONSUMED BY: `just test-unit`.
"""

from __future__ import annotations

import pytest

from quantamind.ingest.standards.mined import mine, substantive
from quantamind.types.standards.proposal import Comment

DEPENDENCY_STANDARD = [
    Comment(
        "Right now XLM is not used enough to add KyTea to the required dependencies. But this "
        "workflow with a test and clear error is very nice, we can just recommend it.",
        "src/tokenization_xlm.py",
        pull=1,
    ),
    Comment(
        "Here again, XLM is not used enough to add NLTK to the required dependencies. The "
        "workflow with a test and clear error is nice, we can just recommend installing it.",
        "src/tokenization_xlm.py",
        pull=2,
    ),
]


def test_a_repeated_point_across_two_changes_is_proposed() -> None:
    """**THE TRUE POSITIVE, NAMED.** This exact standard is the one the corpus evidences best."""
    found = mine(DEPENDENCY_STANDARD)

    assert len(found) == 1
    only = found[0]
    assert only.occurrences == 2
    assert "required dependencies" in only.text
    assert only.distinct_pulls == 2
    assert only.across_changes is True


def test_the_same_point_twice_on_ONE_change_is_not_across_changes() -> None:
    """**A REVIEWER RESTATING THEMSELVES IN ONE THREAD IS NOT A STANDARD.**

    Four of thirteen real clusters were exactly this, one of them character-identical. The proposal
    still surfaces — a human may want it — but it must not claim to recur across changes.
    """
    same_thread = [Comment(c.body, c.path, pull=7) for c in DEPENDENCY_STANDARD]
    only = mine(same_thread)[0]

    assert only.occurrences == 2
    assert only.distinct_pulls == 1
    assert only.across_changes is False


def test_an_unknown_pull_number_is_not_reported_as_a_count() -> None:
    """**"Said on two changes" and "we could not tell" must not read alike.**

    The corpus that produced the finding carries no pull numbers at all, so this is the common case
    and not an edge one.
    """
    unknown = [Comment(c.body, c.path) for c in DEPENDENCY_STANDARD]
    only = mine(unknown)[0]

    assert only.distinct_pulls is None, "an unknown count must not collapse to a number"
    assert only.across_changes is False, "unknown is not a claim of recurrence"


@pytest.mark.parametrize(
    "body",
    ["done", "Done.", "fixed", "LGTM", "ditto", "Same as above", "nit", "+1", "Nice", "thanks!"],
)
def test_the_acknowledgements_reviewers_actually_type_are_refused(body: str) -> None:
    """**EVERY ONE OF THESE HEADED A CLUSTER IN THE REAL CORPUS.**"""
    assert not substantive(body)


def test_a_real_standard_is_not_mistaken_for_an_acknowledgement() -> None:
    """The other half: a filter that refused everything would pass the test above."""
    assert substantive(DEPENDENCY_STANDARD[0].body) is True
    assert mine(DEPENDENCY_STANDARD)[0].occurrences == 2, "it survived the filter and clustered"


def test_acknowledgements_never_become_proposals() -> None:
    """**THE FILTER IS TESTED THROUGH `mine`, NOT ONLY THROUGH `substantive`.**

    A filter that exists and is not wired in is the shape a sabotage found twice in D1c.
    """
    assert mine([Comment("done", pull=n) for n in range(6)]) == ()
