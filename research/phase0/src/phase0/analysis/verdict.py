"""The reading: a risk result to a decision, by thresholds fixed before the data.

WHAT: `Verdict`, the three pre-registered thresholds, and `read_verdict`, which applies
      them in a fixed order with the power check first and unconditional.
WHY:  Separated from `build_table.py` because building a contingency table and deciding
      what it means are different concerns, and only one of them is a commitment. These
      three constants are the study's decision boundary: `PHASE0_PREREGISTRATION.md`
      forbids moving them after data is seen, and a boundary is easier to protect when
      it is not buried among the tabulation code that legitimately changes.

      The power check runs first and cannot be skipped. Below `a = 20` the answer is
      "no result", never "null" -- an underpowered null reported as a negative kills a
      live thesis on noise, which is the most expensive mistake this study can make.
IMPORTS: phase0.analysis.risk.
CONSUMED BY: build_table.py, run_pipeline.py; tests/test_build_table.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from phase0.analysis.risk import MIN_BREAKAGES_FOR_POWER, RiskResult

STRONG_RR = 3.0
STRONG_CI_LOW = 1.5
WEAK_RR = 1.5


@dataclass(frozen=True, slots=True)
class Verdict:
    """The `PHASE0_PREREGISTRATION.md` “Decision thresholds” reading, with power checked first."""

    label: str
    reason: str


def read_verdict(result: RiskResult) -> Verdict:
    """`PHASE0_PREREGISTRATION.md` “Decision thresholds”, with the power check first and
    unconditional.
    """
    if not result.is_powered:
        return Verdict(
            "no result",
            f"a={result.counts.exposed_broke} < {MIN_BREAKAGES_FOR_POWER}: underpowered, "
            f"which is not a negative. Widen the corpus before concluding anything.",
        )
    if result.ci_method == "unavailable":
        return Verdict("no result", result.note or "interval unavailable")
    if result.relative_risk >= STRONG_RR and result.ci_low > STRONG_CI_LOW:
        return Verdict(
            "strong",
            "RR >= 3.0 with CI lower bound > 1.5. Proceed to the call-site census layer.",
        )
    if result.relative_risk >= WEAK_RR and result.excludes_unity:
        return Verdict(
            "weak but real",
            "RR in [1.5, 3.0) excluding 1. Proceed, but rewrite "
            "`PROJECT_CONTEXT.md` “Business case” first: the pitch becomes "
            "'prioritise review attention', not 'prevent breakage'.",
        )
    return Verdict(
        "null",
        "RR < 1.5 or CI includes 1.0. Stop and publish -- see "
        "`PHASE0_PREREGISTRATION.md` “If the result is null”.",
    )
