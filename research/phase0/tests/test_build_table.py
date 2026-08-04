"""Contract test for the analysis stage.

WHAT: Asserts build() is unimplemented and pins the pre-registered thresholds and
      the power floor.
WHY:  RUNBOOK section 4.2: "If a < 20, stop reading. You have no result." An
      underpowered null reported as a negative kills a live thesis on noise, so
      the floor is asserted rather than remembered. The verdict boundaries come
      from PHASE0_PREREGISTRATION.md and are fixed before data is seen -- that is
      what makes them a pre-registration rather than a description.
IMPORTS: phase0.build_table, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0.build_table import (
    MIN_BREAKAGES_FOR_POWER,
    STRONG_CI_LOW,
    STRONG_RR,
    WEAK_RR,
    RiskResult,
    build,
)


def test_build_is_unimplemented() -> None:
    with pytest.raises(NotImplementedError):
        build(Path("exposure.jsonl"), Path("outcome.jsonl"))


def test_power_floor_is_twenty_breakages() -> None:
    assert MIN_BREAKAGES_FOR_POWER == 20


def test_underpowered_table_is_not_powered() -> None:
    """19 breakages is not a null result. It is no result."""
    result = RiskResult(19, 100, 5, 100, relative_risk=3.8, ci_low=1.6, ci_high=9.0)
    assert result.is_powered is False


def test_powered_table_at_the_boundary() -> None:
    """Exactly 20 clears the floor -- the comparison is >=, not >."""
    result = RiskResult(20, 100, 5, 100, relative_risk=3.8, ci_low=1.6, ci_high=9.0)
    assert result.is_powered is True


def test_verdict_thresholds_match_the_preregistration() -> None:
    """Strong: RR >= 3.0 with CI lower bound > 1.5. Weak but real: RR >= 1.5."""
    assert (STRONG_RR, STRONG_CI_LOW, WEAK_RR) == (3.0, 1.5, 1.5)
