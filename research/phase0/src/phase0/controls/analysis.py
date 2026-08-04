"""Controls: earn the right to believe the answer.

WHAT: A positive control that plants breakage the instrument should detect, spread
      across four mechanisms rather than one, and negative controls that replace
      exposure with variables which cannot possibly matter.
WHY:  RUNBOOK section 2.1 calls the positive control the most important gate in
      the study: you cannot interpret a null from an instrument you have not shown
      can produce a positive, because you would probably believe it.

      Four mechanisms, not one. `super()` is PyCG's single best-documented blind
      spot and therefore the easiest possible positive; a control that fires only
      there tells you the instrument is narrow BEFORE you interpret a null.
      Per-mechanism detection is reported alongside the pooled figure, because the
      pooled figure can look healthy while three of four mechanisms are invisible.

      Negative controls re-run the pipeline with nonsense exposure. RR must come
      out near 1. Anything above 1.5 means the pipeline manufactures signal, most
      likely because the outcome scan is contaminated by repository identity
      rather than by the PR.
IMPORTS: phase0.build_table, phase0.classify_exposure, phase0.risk.
CONSUMED BY: run_pipeline.py; tests/test_controls.py. Results to results/controls.json.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from phase0.build_table import Observation, estimate
from phase0.classify_exposure import Exposure
from phase0.risk import RiskResult

POSITIVE_CONTROL_N = 30
POSITIVE_CONTROL_MIN_RR = 5.0
NEGATIVE_CONTROL_MAX_RR = 1.5


@dataclass(frozen=True, slots=True)
class ControlResult:
    """One control arm and whether it cleared its threshold."""

    name: str
    relative_risk: float
    ci_low: float
    ci_high: float
    passed: bool
    detail: str = ""


def run_positive_control(observations: Sequence[Observation]) -> ControlResult:
    """Synthetic PRs where breakage IS caused by an unresolvable edge.

    Expected RR >= 5. RR near 1 means the instrument is broken: stop, and do not
    run on real data, because a null would be uninterpretable.
    """
    robust, naive = estimate(observations)
    chosen = robust if robust.ci_method != "unavailable" else naive
    return ControlResult(
        name="positive",
        relative_risk=chosen.relative_risk,
        ci_low=chosen.ci_low,
        ci_high=chosen.ci_high,
        passed=chosen.relative_risk >= POSITIVE_CONTROL_MIN_RR,
        detail=f"n={len(observations)} synthetic, method={chosen.ci_method}",
    )


# Variables that cannot possibly cause breakage. RUNBOOK 2.2.
NONSENSE: dict[str, Callable[[Observation], bool]] = {
    # Full symbol, not the trailing name: every symbol in a corpus may share a
    # short name, which leaves the variable constant and the 2x2 with an empty
    # margin. RUNBOOK 2.2 specifies the FILE initial for the same reason.
    "symbol_initial_a_to_m": lambda o: o.symbol[:1].lower() < "n",
    "symbol_length_even": lambda o: len(o.symbol) % 2 == 0,
    "repo_name_length_odd": lambda o: len(o.repo_id) % 2 == 1,
}


def _recoded(
    observations: Sequence[Observation], predicate: Callable[[Observation], bool]
) -> list[Observation]:
    """The same rows with exposure replaced by a variable that cannot matter."""
    recoded: list[Observation] = []
    for observation in observations:
        arm = Exposure.EXPOSED if predicate(observation) else Exposure.UNEXPOSED
        recoded.append(
            Observation(
                symbol=observation.symbol,
                repo_id=observation.repo_id,
                outcome=observation.outcome,
                primary=arm,
                sensitivity_low=arm,
                sensitivity_high=arm,
            )
        )
    return recoded


def run_negative_controls(observations: Sequence[Observation]) -> list[ControlResult]:
    """Re-run the pipeline against variables that cannot matter.

    Expected RR near 1 with an interval spanning it. Above 1.5 means the pipeline
    manufactures signal and must be fixed before the real result is believed.
    """
    results: list[ControlResult] = []
    for name, predicate in NONSENSE.items():
        # A predicate that is constant across the corpus assigns every row to one
        # arm, leaves the 2x2 with an empty margin, and yields "unavailable" -- which
        # looks identical to a control that ran and found nothing. Three separate
        # fixtures were degenerate this way before the check existed, so the cause
        # is named rather than left to be inferred from a NaN.
        values = {predicate(o) for o in observations}
        if len(values) < 2:
            results.append(
                ControlResult(
                    name=f"negative:{name}",
                    relative_risk=float("nan"),
                    ci_low=float("nan"),
                    ci_high=float("nan"),
                    passed=False,
                    detail=(
                        f"predicate is constant ({values.pop() if values else 'no rows'}) "
                        f"across all {len(observations)} rows: this control tests nothing"
                    ),
                )
            )
            continue

        robust, naive = estimate(_recoded(observations, predicate))
        chosen: RiskResult = robust if robust.ci_method != "unavailable" else naive
        # An uncomputable control FAILS. It previously passed, which made
        # "we could not compute this" indistinguishable from "this cleared" --
        # the exact confusion between silence and success that VALIDATION.md
        # exists to forbid, sitting inside the control logic itself.
        passed = (
            chosen.ci_method != "unavailable" and chosen.relative_risk <= NEGATIVE_CONTROL_MAX_RR
        )
        results.append(
            ControlResult(
                name=f"negative:{name}",
                relative_risk=chosen.relative_risk,
                ci_low=chosen.ci_low,
                ci_high=chosen.ci_high,
                passed=passed,
                detail=chosen.note or f"method={chosen.ci_method}",
            )
        )
    return results
