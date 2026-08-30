"""Verification that a mutation caught only by breaking the code is not reported as covered.

WHAT: Drives `scripts/mutate/verdict.verdict` over the three states a constant can be in.
WHY:  **COUNTING CATCHES TOGETHER HID A WHOLE SWEEP'S REAL RESULT.** 29 of 130 mutations were
      caught on `src/quantamind` and that was reported as the coverage figure. 20 of the 29 were
      the `-> 0` case, and zero rarely fails an assertion — it breaks the code. `BLOB_TIMEOUT_S`
      set to 0 failed 23 tests with 69 `TimeoutExpired` and 7 assertions: the suite saw a crash,
      not a wrong number. Read as values actually pinned, that run covered 8 constants of 62.

      **THE DIFFERENCE BETWEEN 8 AND 29 WAS INVISIBLE**, which is the same defect this whole tool
      exists to find, committed by the tool's own report.
IMPORTS: pytest, scripts/mutate/verdict.py.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "mutate"))

from verdict import verdict


@dataclass(frozen=True)
class Fake:
    name: str
    new: str
    path: Path = Path("src/mod.py")


def _pair(name: str, new: str, caught: bool) -> tuple[Fake, bool]:
    return Fake(name, new), caught


def test_a_constant_caught_both_ways_is_pinned() -> None:
    lines = verdict([_pair("CAP", "0", True), _pair("CAP", "31", True)])

    assert "1 constant(s) pinned, 0 WEAK, 0 unseen" in lines[1]
    assert not [line for line in lines if "WEAK" in line and "constant(s)" not in line]


def test_a_constant_caught_only_at_zero_is_weak_not_covered() -> None:
    """The finding. At 0 the code breaks; the value itself is unchecked."""
    lines = verdict([_pair("TIMEOUT_S", "0", True), _pair("TIMEOUT_S", "61", False)])

    assert "0 constant(s) pinned, 1 WEAK" in lines[1]
    assert any("WEAK   TIMEOUT_S" in line for line in lines)
    assert any("breaks the code rather than checking the value" in line for line in lines)


def test_a_constant_caught_neither_way_is_unseen() -> None:
    lines = verdict([_pair("GONE", "0", False), _pair("GONE", "17", False)])

    assert "0 constant(s) pinned, 0 WEAK, 1 unseen" in lines[1]
    assert any("unseen GONE" in line for line in lines)


def test_the_three_states_are_counted_separately() -> None:
    """A mixed run must not collapse into one number, which is how the difference was lost."""
    lines = verdict(
        [
            _pair("PINNED", "0", True),
            _pair("PINNED", "9", True),
            _pair("WEAKONE", "0", True),
            _pair("WEAKONE", "9", False),
            _pair("BLIND", "0", False),
            _pair("BLIND", "9", False),
        ]
    )

    assert "1 constant(s) pinned, 1 WEAK, 1 unseen" in lines[1]
    assert "6 mutations over 3 constants" in lines[1]


def test_judging_nothing_raises_rather_than_reporting_a_clean_sweep() -> None:
    with pytest.raises(ValueError, match="not a clean sweep"):
        verdict([])
