"""Contract test for the controls.

WHAT: Asserts both control runners are unimplemented and pins their thresholds.
WHY:  RUNBOOK section 2.1 calls the positive control "the most important gate in
      the entire study": until the instrument is shown able to detect a planted
      positive, a null is uninterpretable. Thresholds are asserted here so that
      lowering one to make a run pass shows up as a failing test rather than as a
      quiet edit -- which PHASE0_PREREGISTRATION.md calls research misconduct on
      ourselves.
IMPORTS: phase0.controls, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0.controls import (
    NEGATIVE_CONTROL_MAX_RR,
    POSITIVE_CONTROL_MIN_RR,
    POSITIVE_CONTROL_N,
    run_negative_controls,
    run_positive_control,
)


def test_positive_control_is_unimplemented() -> None:
    with pytest.raises(NotImplementedError):
        run_positive_control(Path("."))


def test_negative_controls_are_unimplemented() -> None:
    with pytest.raises(NotImplementedError):
        run_negative_controls(Path("."))


def test_positive_control_threshold_is_five() -> None:
    """RR >= 5 on synthetic data. Below that the instrument is broken, not the thesis."""
    assert POSITIVE_CONTROL_MIN_RR == 5.0


def test_positive_control_uses_thirty_synthetic_prs() -> None:
    assert POSITIVE_CONTROL_N == 30


def test_negative_control_ceiling_is_one_point_five() -> None:
    """A nonsense variable above this means the pipeline manufactures signal."""
    assert NEGATIVE_CONTROL_MAX_RR == 1.5
