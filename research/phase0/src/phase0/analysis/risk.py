"""Relative risk, two ways: the naive interval and the one that decides.

WHAT: A 2x2 count, the Katz log-method interval, and the cluster-robust interval
      that `PHASE0_PREREGISTRATION.md` “Decision thresholds” actually reads. Plus the design effect
      between them.
WHY:  Amendment A8. The unit of analysis is a changed symbol, but symbols are not
      independent: many share one PR, whose outcome is measured per file, and many
      PRs share one repository, and repositories differ systematically in
      fix-commit rate, review culture and test coverage -- three of which
      `PHASE0_PREREGISTRATION.md` “Pre-specified confounders”
      already names as confounders.

      Katz assumes independent Bernoulli trials. Under clustering it understates
      variance, so the interval comes out too narrow, and it does so at exactly the
      boundary that decides the project: `PHASE0_PREREGISTRATION.md` “Decision thresholds” turns on
      whether the lower bound clears
      1.5 and whether it includes 1.0. A naive interval could clear a threshold a
      correct one would not.

      Primary inference is therefore a modified Poisson regression -- log link,
      binary outcome -- with a robust sandwich variance clustered on repository,
      which yields a relative risk directly. statsmodels GEE with an Independence
      working correlation provides exactly that. Not hand-rolled.

      The naive interval is still computed, and reported beside it. The gap is the
      design effect, and a reader is entitled to see it.
IMPORTS: numpy, statsmodels. Nothing from phase0 -- this module knows about
      numbers, not about call graphs.
CONSUMED BY: build_table.py, controls.py; tests/test_risk.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import statsmodels.api as sm
from statsmodels.genmod.families import Poisson
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.stats.contingency_tables import Table2x2

MIN_BREAKAGES_FOR_POWER = 20  # `a` in the table. Below this there is no result.

CIMethod = Literal["katz", "cluster-robust", "unavailable"]


@dataclass(frozen=True, slots=True)
class Counts:
    """The 2x2, in the orientation `PHASE0_PREREGISTRATION.md` “The table” fixes."""

    exposed_broke: int  # a
    exposed_clean: int  # b
    unexposed_broke: int  # c
    unexposed_clean: int  # d

    @property
    def total(self) -> int:
        return self.exposed_broke + self.exposed_clean + self.unexposed_broke + self.unexposed_clean

    @property
    def has_empty_margin(self) -> bool:
        """A zero row or column makes the ratio undefined, not zero."""
        return (self.exposed_broke + self.exposed_clean) == 0 or (
            self.unexposed_broke + self.unexposed_clean
        ) == 0


@dataclass(frozen=True, slots=True)
class RiskResult:
    """A risk ratio, its interval, and what is known about the interval's honesty."""

    counts: Counts
    relative_risk: float
    ci_low: float
    ci_high: float
    ci_method: CIMethod
    clusters: int = 0  # distinct repositories contributing an exposed-arm breakage
    note: str = ""

    @property
    def is_powered(self) -> bool:
        """`PHASE0_PREREGISTRATION.md` “Decision thresholds”: below 20 breakages in the exposed arm,
        stop reading.

        Counted in events. `PHASE0_PREREGISTRATION.md` “Observations are clustered, and the CI must
        say so” additionally requires the number of distinct
        repositories behind them, because 20 events from two repositories are not
        20 independent observations -- `clusters` carries that.
        """
        return self.counts.exposed_broke >= MIN_BREAKAGES_FOR_POWER

    @property
    def excludes_unity(self) -> bool:
        return self.ci_low > 1.0


def _undefined(counts: Counts, note: str) -> RiskResult:
    return RiskResult(
        counts=counts,
        relative_risk=float("nan"),
        ci_low=float("nan"),
        ci_high=float("nan"),
        ci_method="unavailable",
        note=note,
    )


def katz(counts: Counts) -> RiskResult:
    """The naive interval. Reported for comparison; never decides anything."""
    if counts.has_empty_margin:
        return _undefined(counts, "empty margin: risk ratio undefined")
    try:
        table = Table2x2(
            np.array(
                [
                    [counts.exposed_broke, counts.exposed_clean],
                    [counts.unexposed_broke, counts.unexposed_clean],
                ],
                dtype=float,
            )
        )
        low, high = table.riskratio_confint()
        return RiskResult(
            counts=counts,
            relative_risk=float(table.riskratio),
            ci_low=float(low),
            ci_high=float(high),
            ci_method="katz",
        )
    except (ValueError, ZeroDivisionError) as exc:
        return _undefined(counts, f"katz failed: {exc}")


def cluster_robust(
    exposed: list[int], broke: list[int], repo: list[str], counts: Counts
) -> RiskResult:
    """Modified Poisson with a sandwich variance clustered on repository.

    Returns an `unavailable` result rather than raising if the fit does not
    converge. An analysis that crashed must never be mistaken for an analysis that
    found no effect.
    """
    distinct = len({r for r, e, b in zip(repo, exposed, broke, strict=True) if e and b})
    if counts.has_empty_margin or len(set(repo)) < 2:
        return _undefined(counts, "too few clusters for a robust variance")

    try:
        design = sm.add_constant(np.asarray(exposed, dtype=float), has_constant="add")
        model = GEE(
            np.asarray(broke, dtype=float),
            design,
            groups=np.asarray(repo),
            family=Poisson(),
        )
        fit = model.fit()
        interval = fit.conf_int()
        return RiskResult(
            counts=counts,
            relative_risk=float(np.exp(fit.params[1])),
            ci_low=float(np.exp(interval[1][0])),
            ci_high=float(np.exp(interval[1][1])),
            ci_method="cluster-robust",
            clusters=distinct,
        )
    except (ValueError, np.linalg.LinAlgError, ZeroDivisionError) as exc:
        return _undefined(counts, f"GEE did not converge: {exc}")


def design_effect(naive: RiskResult, robust: RiskResult) -> float:
    """How much wider clustering makes the interval, on the log scale.

    1.0 means clustering cost nothing. Above 1.0 means the naive interval was
    overconfident by that factor in variance, and `PHASE0_PREREGISTRATION.md` “Observations are
    clustered, and the CI must say so” requires it reported
    whatever it is.
    """
    for result in (naive, robust):
        if result.ci_method == "unavailable" or not np.isfinite(result.ci_low):
            return float("nan")
    naive_width = np.log(naive.ci_high) - np.log(naive.ci_low)
    robust_width = np.log(robust.ci_high) - np.log(robust.ci_low)
    if naive_width <= 0:
        return float("nan")
    return float((robust_width / naive_width) ** 2)
