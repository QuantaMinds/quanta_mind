"""Account for every unit in the control corpus, including the ones nothing measured.

WHAT: Reduces the measured corpus to the 2x2, every exclusion category, a conservation
      check, and worst-case bounds over both kinds of exclusion.
WHY:  Split from `gate.py`, which runs the gate. This module answers a different
      question: where did the units GO. `ARCHITECTURE.md` “Invariants” invariant 3 --
      nothing is lost between stages -- applied to the control itself. It exists because
      a pooled RR of 8.0 was once computed from 50 of 80 units, with all 30 exclusions
      falling in the EXPOSED arm and none in the control arm. That asymmetry produced
      the 8.0 and no output said so.

      There are now TWO ways to leave the table and they are bounded differently. A unit
      with no measurable arm has a known outcome, so it can be placed in the table both
      ways and the bound is tight. A unit whose outcome could not be scanned has no
      outcome at all, so the only honest bound is to assume every one of them broke and
      then that none did. Reporting one number for both would understate the second.

      A6's sensitivity bounds do not cover either. They bound MULTI-site collapse; a
      zero-site symbol returns None for primary AND for both bounds, so the largest
      exclusion category was invisible to the mechanism built to bound exclusions.
IMPORTS: phase0.analysis.build_table, phase0.classify_exposure, phase0.outcome.conclusion,
      phase0.controls.corpus.
CONSUMED BY: controls/gate.py; tests/controls/test_controls.py.
"""

from __future__ import annotations

from phase0.analysis.build_table import Observation, by_primary, tabulate
from phase0.classify_exposure import Exposure
from phase0.controls.corpus import SyntheticPR
from phase0.outcome.conclusion import Outcome

Measured = list[tuple[SyntheticPR, Observation]]


def _rr(aa: int, bb: int, cc: int, dd: int) -> float:
    if (aa + bb) == 0 or (cc + dd) == 0 or cc == 0:
        return float("nan")
    return (aa / (aa + bb)) / (cc / (cc + dd))


def _unscannable(observation: Observation) -> bool:
    return observation.outcome is Outcome.UNSCANNABLE


def reconcile(measured: Measured) -> dict[str, object]:
    """Account for every unit: in-table + arm-excluded + outcome-excluded == corpus."""
    observations = [o for _, o in measured]
    counts, _, _, _ = tabulate(observations, by_primary)

    # An unmeasurable arm. Outcome is known, so these bound tightly.
    arm_excluded = [(s, o) for s, o in measured if o.primary is None and not _unscannable(o)]
    arm_exposed = [(s, o) for s, o in arm_excluded if "-exp-" in s.record.pr_id]
    arm_control = [(s, o) for s, o in arm_excluded if "-ctl-" in s.record.pr_id]

    # An unscannable outcome. These are the units the base-branch bug used to score
    # CLEAN, so they were never excluded and never appeared in any bound.
    outcome_excluded = [(s, o) for s, o in measured if _unscannable(o)]
    unknown_exposed = sum(1 for _, o in outcome_excluded if o.primary is Exposure.EXPOSED)
    unknown_unexposed = sum(1 for _, o in outcome_excluded if o.primary is Exposure.UNEXPOSED)

    ex_broke = sum(1 for _, o in arm_exposed if o.outcome is Outcome.BROKE)
    ex_clean = len(arm_exposed) - ex_broke
    a, b = counts.exposed_broke, counts.exposed_clean
    c, d = counts.unexposed_broke, counts.unexposed_clean

    lower = _rr(a, b, c + ex_broke, d + ex_clean)  # abstentions coded UNEXPOSED
    upper = _rr(a + ex_broke, b + ex_clean, c, d)  # abstentions coded EXPOSED

    # Worst case over the missing outcomes, on top of the arm bounds: to drive RR down,
    # every unscannable exposed unit was clean and every unscannable unexposed unit
    # broke; to drive it up, the reverse.
    both_low = _rr(a, b + unknown_exposed, c + ex_broke + unknown_unexposed, d + ex_clean)
    both_high = _rr(a + ex_broke + unknown_exposed, b + ex_clean, c, d + unknown_unexposed)

    planted_exposed = sum(1 for s, _ in measured if "-exp-" in s.record.pr_id)
    accounted = counts.total + len(arm_excluded) + len(outcome_excluded)
    return {
        "table": {"a": a, "b": b, "c": c, "d": d, "in_table": counts.total},
        "excluded_total": len(arm_excluded) + len(outcome_excluded),
        "excluded_from_exposed_arm": len(arm_exposed),
        "excluded_from_control_arm": len(arm_control),
        "excluded_unscannable_outcome": len(outcome_excluded),
        "unscannable_by_arm": {"exposed": unknown_exposed, "unexposed": unknown_unexposed},
        "conserved": accounted == len(measured),
        "unaccounted_units": len(measured) - accounted,
        "corpus_units": len(measured),
        # Recall against planted exposure, which the pooled RR does not show.
        "planted_exposure_detected": f"{a + b}/{planted_exposed}",
        "detection_recall": (a + b) / planted_exposed if planted_exposed else 0.0,
        "rr_bounds_over_exclusions": [lower, upper],
        "rr_bounds_over_all_exclusions": [both_low, both_high],
        "bounds_agree_on_gate": (lower >= 5.0) == (upper >= 5.0),
        "bounds_agree_on_gate_with_unscannable": (both_low >= 5.0) == (both_high >= 5.0),
    }
