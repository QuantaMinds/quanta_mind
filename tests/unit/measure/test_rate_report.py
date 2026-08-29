"""Verification that a published-findings rate cannot be quoted without its denominator.

WHAT: Pins the three denominators against hand-computed answers, and that an unknown outcome
      is refused rather than silently excluded from every total.
WHY:  A6 reported 0.686 findings published per change. Two later samples on the same
      repository and pipeline appeared to give 0.46 and 0.25, which read as instability in the
      pipeline and was in fact a change of denominator -- the later ones divided by every
      commit attempted, A6 by the changes on which the model was asked anything.

      **THE KNOWN-ANSWER TEST IS THE POINT.** Six findings over the same ten commits read as
      1.500, 1.000 or 0.600 here. A test asserting only that `report()` returns a non-empty
      string would pass against every arrangement of that arithmetic, including the wrong ones.
IMPORTS: pytest, scripts/measure/record.py.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "measure"))

from record import ChangeRecord, rates, report  # noqa: E402


def _ten() -> list[ChangeRecord]:
    """Four measured changes carrying six kept findings, and six that never reached the model."""
    return (
        [ChangeRecord("a" * 40, "measured", raw=3, kept=2, unanchored=1)] * 2
        + [ChangeRecord("b" * 40, "measured", raw=1, kept=1)] * 2
        + [ChangeRecord("c" * 40, "empty-diff")] * 2
        + [ChangeRecord("d" * 40, "no-funded-files")] * 3
        + [ChangeRecord("e" * 40, "no-timestamp")]
    )


def test_the_same_findings_give_three_different_rates() -> None:
    """6 kept over 4 measured, 6 reaching the stage, 10 attempted. Hand-computed, not derived."""
    got = rates(_ten())
    assert got["changes measured (the model was asked)"] == (4, 1.5), got
    assert got["changes reaching the model stage"] == (6, 1.0), got
    assert got["every commit attempted"] == (10, 0.6), got


def test_every_denominator_appears_in_the_report() -> None:
    """A rate printed alone is the defect. All three must be on the page together."""
    text = report(_ten())
    assert "1.500" in text and "1.000" in text and "0.600" in text, text


def test_the_ways_a_change_missed_the_model_are_counted_not_dropped() -> None:
    """A run where nothing reached the model must not look like one where it found nothing."""
    text = report(_ten())
    assert "empty-diff       2" in text, text
    assert "no-funded-files  3" in text, text
    assert "no-timestamp     1" in text, text


def test_gate_rejection_is_computed_over_raw_not_over_changes() -> None:
    """8 raw, 6 kept -> 25%. Dividing by changes would give a number that looks similar."""
    assert "GATE REJECTION     25.0%" in report(_ten()), report(_ten())


def test_a_run_where_the_model_was_never_asked_reports_no_measured_rate() -> None:
    """Zero measured changes must omit the rate, not divide by zero or print 0.000."""
    got = rates([ChangeRecord("f" * 40, "no-funded-files")] * 3)
    assert "changes measured (the model was asked)" not in got, got
    assert got["every commit attempted"] == (3, 0.0), got


def test_an_unrecognised_outcome_is_refused() -> None:
    """A typo'd outcome would be excluded from every pool and shrink the denominator silently."""
    with pytest.raises(ValueError, match="not one of"):
        ChangeRecord("g" * 40, "skipped")
