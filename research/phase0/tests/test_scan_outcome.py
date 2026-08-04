"""Contract test for the outcome scanner.

WHAT: Asserts scan() is unimplemented and pins the RUNBOOK section 1.3 label table.
WHY:  The outcome variable is behavioural on purpose. RUNBOOK section 6 forbids
      switching to the AST-based outcome "because it gives a nicer number" -- it is
      contaminated by construction. LABEL_SPEC is written before the classifier so
      the classifier is fitted to the spec rather than the reverse, and the
      >=16/20 hand-labelling gate is checked against these cases.
IMPORTS: phase0.scan_outcome, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import pytest

from phase0.scan_outcome import WINDOW_DAYS, Outcome, scan

# RUNBOOK section 1.3, as data.
LABEL_SPEC: dict[str, Outcome] = {
    "revert_commit_within_7d": Outcome.BROKE,
    "fix_commit_same_file_+2d": Outcome.BROKE,
    "FIX_uppercase_message": Outcome.BROKE,
    "fix_different_file_+2d": Outcome.CLEAN,
    "fix_outside_window_+9d": Outcome.CLEAN,
    "refactor_commit_+1d": Outcome.CLEAN,
}


def test_scan_is_unimplemented() -> None:
    with pytest.raises(NotImplementedError):
        scan(None)  # type: ignore[arg-type]


def test_refactor_is_not_a_fix() -> None:
    """A refactor landing next day is not evidence the PR broke anything."""
    assert LABEL_SPEC["refactor_commit_+1d"] == Outcome.CLEAN


def test_fix_to_an_unrelated_file_is_clean() -> None:
    """Without file overlap, a 'fix' commit says nothing about this PR."""
    assert LABEL_SPEC["fix_different_file_+2d"] == Outcome.CLEAN


def test_window_is_seven_days() -> None:
    """Pre-registered. Widening it after seeing the data is why it is asserted."""
    assert WINDOW_DAYS == 7
