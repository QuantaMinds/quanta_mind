"""Analysis: the 2x2, the bounds, the arms, and the verdict.

WHAT: Joins exposure and outcome records into contingency tables, and reports the
      primary result, A6's sensitivity bounds, the UNANALYZED_RESOURCE arm and the
      pre-specified strata.
WHY:  The statistic is relative risk, NOT a count. With ~15% of call sites
      unresolved, "15% of breakages were at unresolved sites" is zero signal that
      reads as confirmation; `PHASE0_PREREGISTRATION.md` “The table” rejects the
      count explicitly. Fixing RR before any data is seen stops the number being
      chosen after the fact.

      Power is read BEFORE the point estimate -- `PHASE0_PREREGISTRATION.md`
      “Decision thresholds”. Below `a = 20` there is no result, only an
      underpowered null, and reporting that as negative kills a live thesis on
      noise.

      A6: the primary table is the single-site subset, where the instrument
      measures exposure exactly. Multi-site pairs are held out as bounds; when the
      bounds agree, the collapse provably changed no conclusion.

      A7: RR_unanalyzed covers UNANALYZED_RESOURCE only and is never pooled --
      `PHASE0_RUNBOOK.md` “The `UNANALYZED` arm decides what company this is”. An
      effect living there makes this a scalability product, not an unsoundness
      product: a different company, and the thesis gets rewritten first.
IMPORTS: phase0.analysis.risk, phase0.analysis.verdict, phase0.classify_exposure and
      phase0.scan_outcome for the arm types.
CONSUMED BY: controls.py, run_pipeline.py; tests/test_build_table.py.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from phase0.analysis.risk import Counts, RiskResult, cluster_robust, design_effect
from phase0.analysis.risk import katz as katz_ci
from phase0.analysis.verdict import Verdict, read_verdict
from phase0.classify_exposure import Exposure
from phase0.outcome.scan import Outcome

ArmOf = Callable[["Observation"], Exposure | None]


@dataclass(frozen=True, slots=True)
class Observation:
    """One changed symbol: its arm under each coding, its outcome, its cluster."""

    symbol: str
    repo_id: str  # the clustering unit, per A8
    outcome: Outcome
    primary: Exposure | None  # None: no single-site pair, outside the primary table
    sensitivity_low: Exposure | None
    sensitivity_high: Exposure | None
    strata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Analysis:
    """Everything Results `PHASE0_PREREGISTRATION.md` “Results” needs, and nothing it does not."""

    primary: RiskResult
    primary_naive: RiskResult
    design_effect: float
    sensitivity_low: RiskResult
    sensitivity_high: RiskResult
    unanalyzed: RiskResult
    strata: dict[str, RiskResult]
    multi_site_excluded: int
    # Units dropped because the outcome could not be scanned at all, by category. A
    # complete-case table is only honest while the size of the case it is missing is
    # reported next to it -- an exclusion nobody counts is indistinguishable from the
    # silent CLEAN it replaced.
    outcome_excluded: int
    verdict: Verdict

    @property
    def bounds_agree(self) -> bool:
        """A6: when both bounds give the same verdict, the collapse did not matter."""
        return read_verdict(self.sensitivity_low).label == read_verdict(self.sensitivity_high).label


def by_primary(observation: Observation) -> Exposure | None:
    return observation.primary


def by_sensitivity_low(observation: Observation) -> Exposure | None:
    return observation.sensitivity_low


def by_sensitivity_high(observation: Observation) -> Exposure | None:
    return observation.sensitivity_high


def tabulate(
    observations: Sequence[Observation],
    arm_of: ArmOf = by_primary,
    exposed_arm: Exposure = Exposure.EXPOSED,
) -> tuple[Counts, list[int], list[int], list[str]]:
    """Reduce observations to a 2x2 plus the vectors the robust fit needs.

    Only `exposed_arm` and UNEXPOSED are counted. Everything else -- an
    unmeasurable pair (None) or the other arm -- is excluded rather than folded in,
    because folding is how a third arm silently becomes part of a second.

    The same applies down the other axis. An UNSCANNABLE outcome is a MISSING outcome,
    and this used to code it 0, which put it in the clean cell. That is the base-branch
    bug surviving one layer below the fix: the scan was corrected to say "I could not
    look", and `tabulate` translated that back into "nothing broke" before the estimate
    ever saw it. The 2x2 is complete-case by A16, and this is what makes it so.
    """
    a = b = c = d = 0
    exposed: list[int] = []
    broke: list[int] = []
    repo: list[str] = []

    for observation in observations:
        arm = arm_of(observation)
        if arm is exposed_arm:
            flag = 1
        elif arm is Exposure.UNEXPOSED:
            flag = 0
        else:
            continue

        if observation.outcome is Outcome.UNSCANNABLE:
            continue
        outcome = 1 if observation.outcome is Outcome.BROKE else 0
        if flag and outcome:
            a += 1
        elif flag:
            b += 1
        elif outcome:
            c += 1
        else:
            d += 1

        exposed.append(flag)
        broke.append(outcome)
        repo.append(observation.repo_id)

    return Counts(a, b, c, d), exposed, broke, repo


def estimate(
    observations: Sequence[Observation],
    arm_of: ArmOf = by_primary,
    exposed_arm: Exposure = Exposure.EXPOSED,
) -> tuple[RiskResult, RiskResult]:
    """Return (cluster-robust, naive). The first decides; the second is context."""
    counts, exposed, broke, repo = tabulate(observations, arm_of, exposed_arm)
    return cluster_robust(exposed, broke, repo, counts), katz_ci(counts)


def build(observations: Sequence[Observation], strata: Sequence[str] = ()) -> Analysis:
    """Produce the primary result, the bounds, the third arm and the strata."""
    primary, primary_naive = estimate(observations, by_primary)
    low, _ = estimate(observations, by_sensitivity_low)
    high, _ = estimate(observations, by_sensitivity_high)
    unanalyzed, _ = estimate(observations, by_primary, exposed_arm=Exposure.UNANALYZED_RESOURCE)

    stratified: dict[str, RiskResult] = {}
    for name in strata:
        values = {o.strata.get(name, "") for o in observations}
        for value in sorted(v for v in values if v):
            subset = [o for o in observations if o.strata.get(name) == value]
            stratified[f"{name}={value}"] = estimate(subset, by_primary)[0]

    return Analysis(
        primary=primary,
        primary_naive=primary_naive,
        design_effect=design_effect(primary_naive, primary),
        sensitivity_low=low,
        sensitivity_high=high,
        unanalyzed=unanalyzed,
        strata=stratified,
        multi_site_excluded=sum(1 for o in observations if o.primary is None),
        outcome_excluded=sum(1 for o in observations if o.outcome is Outcome.UNSCANNABLE),
        verdict=read_verdict(primary),
    )
