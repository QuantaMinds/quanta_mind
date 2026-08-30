"""Verification that the selectivity thresholds stay ordered and stay the measured numbers.

WHAT: Pins `CONCENTRATED_AT`, `UNSTABLE_AT` and `ALWAYS_AT` to the values the measurement
      produced, and to the ordering that keeps every branch of the classification reachable.
WHY:  **`ALWAYS_AT` COULD BE SET TO 0.0 WITH EVERY TIER OF THE SUITE GREEN**, including
      `tests/live` against real repositories. At 0.0 the classification reads
      `if rate <= 0.02: CONCENTRATED / elif rate >= 0.0: ALWAYS`, so SELECTIVE becomes
      unreachable and every repository above 2% is reported as firing on everything. Found by
      mutating every numeric constant in `src/quantamind`.

      **THE ORDERING IS THE PROPERTY, NOT JUST THE VALUES.** Three numbers that no longer
      increase describe a classifier with a dead branch, whatever the individual values are, and
      that stays true if the decile boundaries are ever re-measured.

      **WHAT THIS DOES NOT DO.** It does not exercise the branch. `estimate()` reaches it only
      through a populated store — a repository, touches, and a calibration window — and building
      a fixture that genuinely produces a rate on each side of both boundaries is a larger piece
      of work than this file. Until that exists, the branch itself is covered only by
      `tests/live`, which the mutation showed does not distinguish these values either. Stated
      here rather than left to be inferred from the absence of a test.
IMPORTS: quantamind.rank.firing.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.rank.firing import ALWAYS_AT, CONCENTRATED_AT, UNSTABLE_AT


def test_the_thresholds_are_the_measured_values() -> None:
    """Literals, so this file does not move with the code it is checking."""
    assert CONCENTRATED_AT == 0.02
    assert UNSTABLE_AT == 0.10
    assert ALWAYS_AT == 0.50


def test_the_thresholds_increase_so_no_branch_is_dead() -> None:
    """The property that survives a re-measurement. This is what `ALWAYS_AT = 0.0` breaks."""
    assert CONCENTRATED_AT < UNSTABLE_AT < ALWAYS_AT


def test_every_threshold_is_a_proportion() -> None:
    """Rates are proportions; a boundary outside [0, 1] classifies nothing or everything."""
    for name, value in (
        ("CONCENTRATED_AT", CONCENTRATED_AT),
        ("UNSTABLE_AT", UNSTABLE_AT),
        ("ALWAYS_AT", ALWAYS_AT),
    ):
        assert 0.0 < value < 1.0, f"{name} is {value}, which is not a proportion"
