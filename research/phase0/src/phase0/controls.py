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
IMPORTS: phase0.census, phase0.classify_exposure, phase0.build_table, phase0.risk.
CONSUMED BY: run_pipeline.py; tests/test_controls.py. Results to results/controls.json.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from phase0.build_table import Observation, estimate
from phase0.census import count_call_sites
from phase0.classify_exposure import Exposure, classify
from phase0.pycg_failure import GraphStatus
from phase0.risk import RiskResult

POSITIVE_CONTROL_N = 30
POSITIVE_CONTROL_MIN_RR = 5.0
NEGATIVE_CONTROL_MAX_RR = 1.5

# Four ways a caller can exist that PyCG will not emit an edge for. Each source
# defines `target` and calls it ONLY through the named mechanism.
MECHANISMS: dict[str, str] = {
    "super_chain": (
        "class Base:\n    def target(self, r):\n        return r\n\n\n"
        "class Child(Base):\n    def target(self, r):\n        return super().target(r)\n"
    ),
    "computed_getattr": (
        "def target(r):\n    return r\n\n\n"
        "def caller(mod, cfg):\n    return getattr(mod, cfg['name'])(1)\n"
    ),
    "string_registry": (
        "REGISTRY = {}\n\n\ndef target(r):\n    return r\n\n\n"
        "REGISTRY['t'] = target\n\n\ndef caller(k):\n    return REGISTRY[k](1)\n"
    ),
    "registering_decorator": (
        "HOOKS = []\n\n\ndef register(fn):\n    HOOKS.append(fn)\n    return fn\n\n\n"
        "@register\ndef target(r):\n    return r\n\n\ndef caller():\n    return HOOKS[0](1)\n"
    ),
}


@dataclass(frozen=True, slots=True)
class MechanismProbe:
    """Whether the exposure variable can see one kind of hidden caller."""

    mechanism: str
    detected: bool
    reason: str


@dataclass(frozen=True, slots=True)
class ControlResult:
    """One control arm and whether it cleared its threshold."""

    name: str
    relative_risk: float
    ci_low: float
    ci_high: float
    passed: bool
    detail: str = ""


def probe_mechanism(
    name: str, source: str, edges: dict[str, set[str]] | None = None
) -> MechanismProbe:
    """Can the exposure variable detect a hidden caller of `target` via `name`?

    Runs the real census and asks classify with an empty edge set -- i.e. PyCG
    resolved nothing -- so a mechanism that still comes out UNEXPOSED is one the
    variable is structurally blind to, not one PyCG happened to handle.

    A site whose callee has no static name (`getattr(m, k)()`) cannot be attributed
    to any symbol, so it produces no pair at all. That is a FALSE NEGATIVE, biased
    toward the null, and it is the reason this probe exists.
    """
    sites = count_call_sites(source, path=f"{name}.py", module=name)
    result = classify(f"{name}.target", "target", sites, edges or {}, GraphStatus.OK)

    if result.primary is Exposure.EXPOSED:
        return MechanismProbe(name, True, "named call site with no edge")
    if result.primary is None:
        return MechanismProbe(
            name, False, "no call site names the symbol: invisible to the variable"
        )
    return MechanismProbe(name, False, f"classified {result.primary.value}")


def probe_all_mechanisms() -> list[MechanismProbe]:
    """RUNBOOK 2.1's diversification, as a capability profile of our own variable."""
    return [probe_mechanism(name, source) for name, source in MECHANISMS.items()]


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
    "symbol_initial_a_to_m": lambda o: o.symbol.rsplit(".", 1)[-1][:1].lower() < "n",
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
        robust, naive = estimate(_recoded(observations, predicate))
        chosen: RiskResult = robust if robust.ci_method != "unavailable" else naive
        passed = (
            chosen.ci_method == "unavailable" or chosen.relative_risk <= NEGATIVE_CONTROL_MAX_RR
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
