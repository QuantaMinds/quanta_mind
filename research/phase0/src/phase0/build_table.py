"""Analysis: the 2x2, relative risk with a CI, and the stratified breakdown.

WHAT: Joins exposure and outcome records into the contingency table, computes RR
      with a 95% CI by the Katz log method, and repeats it per stratum.
WHY:  The analysis is relative risk, NOT a count. With roughly 15% of call sites
      unresolved, "15% of breakages were at unresolved sites" is zero signal that
      reads as confirmation. PHASE0_PREREGISTRATION.md fixes RR as the statistic
      before any data is seen, which is what stops the number being chosen after
      the fact.

      Power is read BEFORE the point estimate. If a < 20 there is no result, only
      an underpowered null -- and reporting that as negative is the most expensive
      mistake available here, because it kills a live thesis on noise.

      RR_unanalyzed is computed separately, never pooled. RUNBOOK section 4.4: if
      the effect sits entirely in UNANALYZED this is a scalability product, not an
      unsoundness product, and the thesis gets rewritten before any code is.
IMPORTS: scipy, statsmodels, pandas; classify_exposure (Exposure), scan_outcome.
CONSUMED BY: run_pipeline.py; tests/test_build_table.py. Output results/phase0-*.json.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MIN_BREAKAGES_FOR_POWER = 20  # `a` in the table; below this there is no result
STRONG_RR = 3.0
STRONG_CI_LOW = 1.5
WEAK_RR = 1.5


@dataclass(frozen=True, slots=True)
class RiskResult:
    """One 2x2 reduced to a risk ratio and its interval."""

    exposed_broke: int  # a
    exposed_clean: int  # b
    unexposed_broke: int  # c
    unexposed_clean: int  # d
    relative_risk: float
    ci_low: float
    ci_high: float

    @property
    def is_powered(self) -> bool:
        """RUNBOOK section 4.2: below 20 breakages in the exposed arm, stop reading."""
        return self.exposed_broke >= MIN_BREAKAGES_FOR_POWER


def build(exposure: Path, outcome: Path, strata: tuple[str, ...] = ()) -> dict[str, RiskResult]:
    """Produce the pooled table plus one per stratum.

    Raises:
        NotImplementedError: Day 6 of the run. See RUNBOOK section 4.
    """
    raise NotImplementedError("Phase 0 Day 6 — see docs/findings/PHASE0_RUNBOOK.md")
