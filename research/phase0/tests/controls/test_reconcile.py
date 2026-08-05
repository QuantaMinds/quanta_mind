"""Verification that reconciliation accounts for units it cannot measure the outcome of.

WHAT: Asserts the conservation invariant holds once a unit can leave the table for a
      SECOND reason, and that the two reasons are reported separately.
WHY:  `ARCHITECTURE.md` “Invariants” invariant 3 -- nothing is lost between stages.
      There used to be exactly one way out of the 2x2, an unmeasurable arm, and
      `conserved` was computed as in-table plus arm-excluded. Dropping unscannable
      outcomes from the table without teaching the reconciliation about them would have
      left units in neither term: `conserved` would have gone false, or worse, someone
      would have restored the total by folding them back into the clean cell.

      The bounds are asserted separately because they are not interchangeable. A unit
      with an unmeasurable arm still has a known outcome, so it can be placed both ways
      and the interval is tight. A unit with no outcome at all can only be bounded by
      assuming all of them broke and then that none did, which is wider -- and reporting
      one interval for both would understate the second.

      Synthetic Observations rather than a corpus run: this module is arithmetic over
      counts, and building real repositories here would test `corpus.py` instead. The
      behavioural end of the same fix is asserted against real git in
      tests/outcome/test_branch.py.
IMPORTS: phase0.controls.reconcile, phase0.analysis.build_table, phase0.classify_exposure,
      phase0.outcome.conclusion, phase0.controls.corpus.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

from phase0.analysis.build_table import Observation
from phase0.classify_exposure import Exposure
from phase0.controls.corpus import SyntheticPR
from phase0.controls.reconcile import reconcile
from phase0.extract_prs import PRRecord
from phase0.outcome.conclusion import Outcome


def _unit(
    index: int, arm: str, exposure: Exposure | None, outcome: Outcome
) -> tuple[SyntheticPR, Observation]:
    """One measured corpus unit. `arm` is "exp" or "ctl", read from the pr_id by name."""
    record = PRRecord(
        pr_id=f"syn-{arm}-{index}",
        repo="synthetic/corpus",
        language="python",
        parent_sha="0" * 40,
        merged_sha="1" * 40,
        merged_at="2026-03-01T12:00:00Z",
        changed_files=("pkg/mod.py",),
        changed_symbols=("f",),
    )
    synthetic = SyntheticPR(
        repo_path=Path("."),
        record=record,
        mechanism="super_chain",
        planted_break=outcome is Outcome.BROKE,
    )
    observation = Observation(
        symbol="pkg.mod.f",
        repo_id=f"synthetic/corpus-{index}",
        outcome=outcome,
        primary=exposure,
        sensitivity_low=exposure or Exposure.UNEXPOSED,
        sensitivity_high=exposure or Exposure.EXPOSED,
    )
    return synthetic, observation


def test_every_unit_is_accounted_for_when_some_cannot_be_scanned() -> None:
    """In-table + arm-excluded + outcome-excluded must equal the corpus, exactly."""
    measured = [
        _unit(0, "exp", Exposure.EXPOSED, Outcome.BROKE),
        _unit(1, "exp", Exposure.EXPOSED, Outcome.CLEAN),
        _unit(2, "ctl", Exposure.UNEXPOSED, Outcome.CLEAN),
        _unit(3, "exp", None, Outcome.BROKE),  # arm unmeasurable, outcome known
        _unit(4, "exp", Exposure.EXPOSED, Outcome.UNSCANNABLE),  # arm known, outcome not
        _unit(5, "ctl", Exposure.UNEXPOSED, Outcome.UNSCANNABLE),
    ]

    out = reconcile(measured)

    assert out["conserved"] is True
    assert out["unaccounted_units"] == 0
    assert out["table"]["in_table"] == 3
    assert out["excluded_unscannable_outcome"] == 2
    assert out["excluded_from_exposed_arm"] == 1
    assert out["excluded_total"] == 3
    assert out["corpus_units"] == 6


def test_the_two_exclusion_kinds_are_reported_separately() -> None:
    """An unscannable outcome is not an unmeasurable arm, and pooling them loses which.

    The arm count was the only exclusion anyone read. If the unscannable units were added
    to it, a corpus losing units to an unwalkable branch would look identical to one
    losing them to a collapsed call graph, and the two have different fixes.
    """
    measured = [
        _unit(0, "exp", Exposure.EXPOSED, Outcome.BROKE),
        _unit(1, "ctl", Exposure.UNEXPOSED, Outcome.CLEAN),
        _unit(2, "exp", None, Outcome.CLEAN),
        _unit(3, "exp", Exposure.EXPOSED, Outcome.UNSCANNABLE),
    ]

    out = reconcile(measured)

    assert out["excluded_from_exposed_arm"] == 1
    assert out["excluded_unscannable_outcome"] == 1
    assert out["unscannable_by_arm"] == {"exposed": 1, "unexposed": 0}


def test_missing_outcomes_widen_the_bounds_rather_than_vanishing() -> None:
    """A unit with no outcome cannot be placed, so the only honest bound assumes both.

    Before the fix these units were CLEAN, so they did not widen anything -- they moved
    the point estimate toward the null and reported nothing at all.
    """
    measured = [
        _unit(0, "exp", Exposure.EXPOSED, Outcome.BROKE),
        _unit(1, "exp", Exposure.EXPOSED, Outcome.CLEAN),
        _unit(2, "ctl", Exposure.UNEXPOSED, Outcome.BROKE),
        _unit(3, "ctl", Exposure.UNEXPOSED, Outcome.CLEAN),
        _unit(4, "exp", Exposure.EXPOSED, Outcome.UNSCANNABLE),
        _unit(5, "ctl", Exposure.UNEXPOSED, Outcome.UNSCANNABLE),
    ]

    out = reconcile(measured)
    tight_low, tight_high = out["rr_bounds_over_exclusions"]  # type: ignore[misc]
    wide_low, wide_high = out["rr_bounds_over_all_exclusions"]  # type: ignore[misc]

    assert wide_low < tight_low
    assert wide_high > tight_high
