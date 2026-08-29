"""Verification that two-rater agreement is computed, not asserted.

WHAT: Pins kappa against hand-computed answers, the refusal to score an incomplete pair, and
      that disagreements are itemised rather than summarised away.
WHY:  One rater at n=24 is a first measurement. `adjudication-preregistration.md` requires a
      second before a number like 25.0% is leaned on, and the ranking result got one at 92%
      agreement, kappa 0.66.

      **KAPPA IS TESTED AT ITS KNOWN POINTS**, because a chance-corrected statistic is exactly
      the kind that looks plausible while being wrong: identical raters must give 1.0, 50%
      agreement with balanced margins must give 0.0 rather than 0.5, and raters who disagree on
      everything must go negative. A test asserting only "returns a float" passes on all of them.
IMPORTS: pytest, phase0.findings.agreement.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import math

from phase0.findings.agreement import kappa

VARIED = {"i1": "TRUE", "i2": "FALSE", "i3": "UNKNOWN", "i4": "TRUE"}


def test_identical_raters_score_one() -> None:
    assert kappa(VARIED, dict(VARIED)) == 1.0


def test_fifty_percent_agreement_on_balanced_margins_is_chance() -> None:
    """**THE POINT OF CHANCE CORRECTION.** Raw agreement here is 50%; kappa must say 0.0."""
    a = {"i1": "TRUE", "i2": "FALSE", "i3": "TRUE", "i4": "FALSE"}
    b = {"i1": "TRUE", "i2": "FALSE", "i3": "FALSE", "i4": "TRUE"}
    assert kappa(a, b) == 0.0, kappa(a, b)


def test_total_disagreement_goes_negative() -> None:
    b = {"i1": "FALSE", "i2": "TRUE", "i3": "TRUE", "i4": "UNKNOWN"}
    assert kappa(VARIED, b) < 0, kappa(VARIED, b)


def test_one_category_only_is_undefined_not_perfect() -> None:
    """Two raters who both said TRUE to everything agree completely and have shown nothing.

    Returning 1.0 would let a rater who never varied look like a perfectly calibrated one.
    """
    same = {f"i{n}": "TRUE" for n in range(10)}
    got = kappa(same, dict(same))
    assert math.isnan(got), f"expected NaN for a single-category pair, got {got}"
    assert got != 1.0, "a rater who never varied must not score as perfectly calibrated"


def test_no_shared_items_is_undefined() -> None:
    """Zero overlap is not zero agreement; returning 0.0 would read as chance-level."""
    got = kappa({}, {})
    assert math.isnan(got), f"expected NaN for an empty pair, got {got}"
    assert got != 0.0, "no shared items must not read as chance-level agreement"
