"""The four unresolvable-caller mechanisms, and whether we can see them.

WHAT: Source templates for four ways a caller can exist that PyCG will not emit an
      edge for, and a probe reporting which the exposure variable detects.
WHY:  `PHASE0_RUNBOOK.md` “Positive control” requires a positive control. `super()` is PyCG's single
      best-documented blind spot and therefore the easiest possible positive; a
      control that fires only there says the instrument is narrow, and A11 fixes
      the reading of each pattern before the numbers exist.

      The probe runs with an EMPTY edge set — PyCG resolved nothing — so a
      mechanism that still comes out UNEXPOSED is one the variable is
      structurally blind to, not one PyCG happened to handle. That distinction is
      the whole value of the probe.

      Measured result, recorded in A10: one of four. Calls dispatched through a
      value carry no callee name, so nothing can be attributed to the symbol and
      it produces no pair at all — a false negative, biased toward the null.
IMPORTS: phase0.census, phase0.classify_exposure, phase0.pycg_failure.
CONSUMED BY: controls/corpus.py, controls/__init__.py; tests/test_controls.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from phase0.census import count_call_sites
from phase0.classify_exposure import Exposure, classify
from phase0.pycg_failure import GraphStatus

# Each source defines `target` and calls it ONLY through the named mechanism.
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

# A caller that IS resolvable, for the control arm of the positive control.
RESOLVABLE = "def target(r):\n    return r\n\n\ndef caller():\n    return target(1)\n"


@dataclass(frozen=True, slots=True)
class MechanismProbe:
    """Whether the exposure variable can see one kind of hidden caller."""

    mechanism: str
    detected: bool
    reason: str


def probe_mechanism(
    name: str, source: str, edges: dict[str, set[str]] | None = None
) -> MechanismProbe:
    """Can the exposure variable detect a hidden caller of `target` via `name`?

    Empty edge set by default, so a miss is structural rather than something PyCG
    happened to resolve. A site whose callee has no static name — `getattr(m, k)()`
    — cannot be attributed to any symbol and produces no pair, which is a false
    negative biased toward the null.
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
    """`PHASE0_RUNBOOK.md` “Positive control” diversification, as a capability profile of our own
    variable.
    """
    return [probe_mechanism(name, source) for name, source in MECHANISMS.items()]
