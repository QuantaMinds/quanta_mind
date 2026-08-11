"""A better call graph does NOT widen the capability profile. The census decides it.

WHAT: Feeds `probe_mechanism` a PERFECT call graph — an edge from each mechanism's
      caller straight to its target — and asserts the profile is unchanged.
WHY:  A10 reports one mechanism of four detected, and that has been read as a limit of
      the VENDORED ANALYSER: swap PyCG for something flow-sensitive and the other three
      arrive. Measured, they do not. `classify_exposure` matches a call site to a symbol
      by NAME, and `census` records `callee_name=""` for `REGISTRY[k]`, `HOOKS[0]` and
      `getattr(mod, cfg["name"])` — there is no name at those sites for any analyser to
      change. The limit is in attribution, not in resolution.

      Pinned as a test because the claim is load-bearing for the product roadmap and is
      the kind that rots silently: if `classify_exposure` is ever changed to attribute a
      site by its RESOLVED EDGE rather than by name — which is the actual fix — this test
      fails, and whoever makes that change is forced to update A50 rather than leaving a
      superseded claim on the record.
IMPORTS: phase0.controls.mechanisms, phase0.census.
CONSUMED BY: `just check`; A50.
"""

from __future__ import annotations

from phase0.census import count_call_sites
from phase0.controls.mechanisms import MECHANISMS, probe_mechanism

# The three the exposure variable cannot see. `super_chain` is the one it can.
INVISIBLE = ("computed_getattr", "string_registry", "registering_decorator")


def _perfect_graph(name: str) -> dict[str, set[str]]:
    """What a flawless analyser would hand us: caller resolved straight to target."""
    return {f"{name}.caller": {f"{name}.target"}}


def test_a_perfect_call_graph_does_not_add_a_single_mechanism() -> None:
    """The measurement behind A50, run rather than argued."""
    without = {name: probe_mechanism(name, src).detected for name, src in MECHANISMS.items()}
    with_graph = {
        name: probe_mechanism(name, src, _perfect_graph(name)).detected
        for name, src in MECHANISMS.items()
    }

    assert without == {
        "super_chain": True,
        "computed_getattr": False,
        "string_registry": False,
        "registering_decorator": False,
    }
    assert with_graph == without, (
        "a perfect call graph changed the profile, so the limit was resolution after all "
        "and A50 needs rewriting"
    )


def test_the_reason_is_an_empty_callee_name_at_the_call_site() -> None:
    """WHY it cannot help: there is no name at the site to attribute to a symbol.

    Asserted on the census's own output rather than on the probe's verdict, because the
    probe reports a conclusion and this reports the cause. `callee_text` IS recorded,
    which is what makes an edge-based attribution possible later — the raw material is
    present and only the join is missing.
    """
    for name in INVISIBLE:
        sites = count_call_sites(MECHANISMS[name], path=f"{name}.py", module=name)
        dispatching = [s for s in sites if s.enclosing == f"{name}.caller"]
        assert dispatching, f"{name}: no call site inside caller()"
        # NOT "every site here is unnamed" -- that was asserted first and is FALSE:
        # `getattr(mod, cfg["name"])(1)` contains a NAMED call to `getattr` beside the
        # unnamed dispatch. The claim A50 rests on is narrower and is the true one.
        assert not any(s.callee_name == "target" for s in dispatching), (
            f"{name}: a site names `target`, so the census could attribute it by name and "
            f"this mechanism is not invisible for the reason A50 states"
        )
        unnamed = [s for s in dispatching if s.callee_name == ""]
        assert unnamed, f"{name}: no unnamed dispatching site; the mechanism is not modelled"
        assert all(s.callee_text for s in unnamed), (
            f"{name}: callee_text is empty, so an edge-based attribution has nothing to "
            f"join on and A50's product path does not exist"
        )


def test_super_chain_is_visible_for_the_opposite_reason() -> None:
    """The control. It is detected because a site literally names `target`."""
    sites = count_call_sites(MECHANISMS["super_chain"], path="s.py", module="super_chain")
    assert "target" in {s.callee_name for s in sites}
