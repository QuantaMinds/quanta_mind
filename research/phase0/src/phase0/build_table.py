"""Analysis: the 2x2, the bounds, the arms, and the verdict.

WHAT: Joins exposure and outcome records into contingency tables, and reports the
      primary result, A6's sensitivity bounds, the UNANALYZED_RESOURCE arm and the
      pre-specified strata.
WHY:  The analysis is relative risk, NOT a count. With roughly 15% of call sites
      unresolved, "15% of breakages were at unresolved sites" is zero signal that
      reads as confirmation. §3.3 rejects the count explicitly, and fixing RR as
      the statistic before any data is seen is what stops the number being chosen
      after the fact.

      Power is read BEFORE the point estimate. §4: if `a < 20` there is no result,
      only an underpowered null, and reporting that as negative is the most
      expensive mistake available -- it kills a live thesis on noise.

      A6: the primary table is the single-site subset, where the instrument
      measures exposure exactly. Multi-site pairs are held out and reported as
      bounds. When the bounds agree, the collapse provably changed no conclusion.

      A7/§4.4: RR_unanalyzed is computed over UNANALYZED_RESOURCE only and never
      pooled. If the effect lives there, this is a scalability product rather than
      an unsoundness product -- a different company, and the thesis gets rewritten
      before any code is.
IMPORTS: phase0.risk for the statistics, phase0.classify_exposure and
      phase0.scan_outcome for the arm types.
CONSUMED BY: controls.py, run_pipeline.py; tests/test_build_table.py.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from phase0.classify_exposure import Exposure
from phase0.risk import MIN_BREAKAGES_FOR_POWER, Counts, RiskResult, cluster_robust, design_effect
from phase0.risk import katz as katz_ci
from phase0.scan_outcome import Outcome

STRONG_RR = 3.0
STRONG_CI_LOW = 1.5
WEAK_RR = 1.5

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
class Verdict:
    """The §4 reading, with power checked first."""

    label: str
    reason: str


@dataclass(frozen=True, slots=True)
class Analysis:
    """Everything Results §8 needs, and nothing it does not."""

    primary: RiskResult
    primary_naive: RiskResult
    design_effect: float
    sensitivity_low: RiskResult
    sensitivity_high: RiskResult
    unanalyzed: RiskResult
    strata: dict[str, RiskResult]
    multi_site_excluded: int
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


def read_verdict(result: RiskResult) -> Verdict:
    """§4, with the power check first and unconditional."""
    if not result.is_powered:
        return Verdict(
            "no result",
            f"a={result.counts.exposed_broke} < {MIN_BREAKAGES_FOR_POWER}: underpowered, "
            f"which is not a negative. Widen the corpus before concluding anything.",
        )
    if result.ci_method == "unavailable":
        return Verdict("no result", result.note or "interval unavailable")
    if result.relative_risk >= STRONG_RR and result.ci_low > STRONG_CI_LOW:
        return Verdict("strong", "RR >= 3.0 with CI lower bound > 1.5. Proceed to Phase 1.")
    if result.relative_risk >= WEAK_RR and result.excludes_unity:
        return Verdict(
            "weak but real",
            "RR in [1.5, 3.0) excluding 1. Proceed, but rewrite PROJECT_CONTEXT.md §5 "
            "first: the pitch becomes 'prioritise review attention', not 'prevent breakage'.",
        )
    return Verdict("null", "RR < 1.5 or CI includes 1.0. Stop and publish -- see §6.")


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
        verdict=read_verdict(primary),
    )
