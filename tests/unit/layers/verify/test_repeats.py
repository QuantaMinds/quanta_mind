"""Verification that a repeated claim is reported and a distinct one is left alone.

WHAT: Drives `verify/repeats.repeats` — same file and same claim collapses, different file or
      different claim does not, and the FIRST statement is the one kept.
WHY:  **WE EMIT 194 COMMENTS COVERING 81 GOLDEN DEFECTS WHERE QODO EMITS 152 COVERING 98**, at a
      17.3% redundancy rate against their 1.0%. This is the model-free half of that gap.

      **THE FALSE-POSITIVE DIRECTION IS THE ONE THAT MATTERS.** A rule that collapses two genuine
      findings deletes a defect a customer would have been told about, and the count would look
      better for it. So most of this file is cases that must NOT collapse: a different file, a
      different claim, a shared vocabulary without a shared claim.

      **INDICES, NOT A SHORTER LIST.** A function returning fewer findings makes "dropped a
      repeat" and "lost a finding" the same value on the wire. The caller counts what it
      discarded, which is the only way the two stay distinguishable.
IMPORTS: pytest, quantamind.verify.repeats, quantamind.types.finding.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.types.finding import Finding
from quantamind.verify.repeats import SIMILAR_AT, alike, repeats

SAME = "The connection is never closed when the request raises, leaking a socket per failure."
REWORDED = "The connection is never closed when the request raises — leaking a socket per failure"
OTHER = "The retry count is read before the config is loaded, so it is always zero here."


def _finding(claim: str, path: str = "src/a.py", quote: str = "compute(alpha)") -> Finding:
    return Finding(path=path, quote=quote, claim=claim)


def test_the_threshold_is_the_registered_value() -> None:
    """0.86, fixed before any outcome was read. The pre-registration's first bar tests it."""
    assert SIMILAR_AT == 0.86


def test_the_same_claim_twice_reports_the_second() -> None:
    """The first statement is kept — the one the model reached first, not an arbitrary member."""
    assert repeats([_finding(SAME), _finding(SAME)]) == (1,)


def test_a_rewording_of_the_same_claim_is_still_a_repeat() -> None:
    """Punctuation and case vary between generations; the claim does not."""
    assert repeats([_finding(SAME), _finding(REWORDED)]) == (1,)


def test_a_different_claim_about_the_same_file_is_kept() -> None:
    """Two real defects in one file is the ordinary case, not a duplicate."""
    assert repeats([_finding(SAME), _finding(OTHER)]) == ()


def test_the_same_claim_about_a_different_file_is_kept() -> None:
    """Different files are different findings however alike the prose."""
    assert repeats([_finding(SAME), _finding(SAME, path="src/b.py")]) == ()


def test_nothing_is_reported_for_a_single_finding() -> None:
    assert repeats([_finding(SAME)]) == ()


def test_an_empty_list_reports_nothing_rather_than_raising() -> None:
    """No findings is a legitimate review, and must stay distinct from a failure."""
    assert repeats([]) == ()


def test_three_statements_of_one_claim_report_two() -> None:
    """The count of discarded findings is what the caller reports, so it must be exact."""
    assert repeats([_finding(SAME), _finding(REWORDED), _finding(SAME)]) == (1, 2)


@pytest.mark.parametrize(
    ("left", "right"),
    [(SAME, OTHER), ("", SAME), (SAME, ""), ("", "")],
)
def test_unlike_or_empty_claims_score_below_the_threshold(left: str, right: str) -> None:
    """Empty against anything is 0, never 1 — otherwise two blank claims would collapse."""
    assert alike(left, right) < SIMILAR_AT


def test_an_identical_claim_scores_one() -> None:
    """The control: without this, the similarity function could return 0 always and pass above."""
    assert alike(SAME, SAME) == 1.0
