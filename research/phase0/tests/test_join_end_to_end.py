"""The join, exercised across every stage against real PyCG output.

WHAT: Builds a package on disk, runs the real census and the real instrument over
      it, and asserts the resulting arms for two symbols chosen to exercise the
      two ways the join can silently break.
WHY:  Every other exposure test hands `classify` a hand-built edge dictionary,
      which proves the reduction logic and nothing about whether the two halves
      agree on names. Naming is exactly where this join fails silently: PyCG has
      no line numbers, so a mismatch does not error, it just returns no edge, and
      every site reads as unresolved. Exposure would climb toward 100% and
      RUNBOOK section 6 Q4's "classifier degenerate" would fire with no
      indication of the cause.

      Two symbols, two failure modes:
      - Base.validate is reached only through `super()`, which PyCG does not
        emit. This is README.md's switchboard and must come out EXPOSED.
      - helper_fn lives in a nested module, where PyCG names the same function
        `sub.deep.helper_fn` at its definition and `acme.sub.deep.helper_fn`
        where an import resolved it. It must come out UNEXPOSED; strict equality
        would make it a false positive.
IMPORTS: phase0.scope, phase0.census, phase0.graph.run_graph, phase0.classify_exposure.
      No mocks -- a mock could not tell us PyCG's naming convention.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0 import scope
from phase0.census import count_call_sites
from phase0.classify_exposure import Exposure, classify
from phase0.graph.run_graph import GraphStatus, run

HANDLERS = """\
from acme.sub.deep import helper_fn


class Base:
    def validate(self, r):
        return helper_fn(r)


class Stripe(Base):
    def validate(self, r):
        return super().validate(r)
"""

DEEP = "def helper_fn(r):\n    return r\n"


def _build(tmp_path: Path) -> scope.Scope:
    pkg = tmp_path / "acme"
    (pkg / "sub").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "sub" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "handlers.py").write_text(HANDLERS, encoding="utf-8")
    (pkg / "sub" / "deep.py").write_text(DEEP, encoding="utf-8")
    resolved = scope.resolve(tmp_path, ["acme/handlers.py"])
    assert resolved is not None
    return resolved


def _census_and_graph(
    resolved: scope.Scope,
) -> tuple[list, dict[str, set[str]], GraphStatus]:
    graph = run(resolved, timeout_s=90)
    edges: dict[str, set[str]] = {}
    for edge in graph.edges:
        edges.setdefault(edge.src, set()).add(edge.dst)

    sites = []
    for path in resolved.files:
        sites += count_call_sites(
            path.read_text(encoding="utf-8"),
            path=str(path),
            module=resolved.module_of(path),
        )
    return sites, edges, graph.status


@pytest.mark.timeout(180)
def test_super_reached_symbol_is_exposed(tmp_path: Path) -> None:
    """The founding example, end to end: base method, no incoming edge.

    Stripe.validate calls super().validate(r). The census counts that site; PyCG
    emits only <builtin>.super out of Stripe.validate. So the one caller of
    Base.validate is unresolved, and the symbol is EXPOSED.
    """
    sites, edges, status = _census_and_graph(_build(tmp_path))
    result = classify("handlers.Base.validate", "validate", sites, edges, status)
    assert result.primary is Exposure.EXPOSED


@pytest.mark.timeout(180)
def test_nested_module_symbol_is_not_a_false_positive(tmp_path: Path) -> None:
    """Package-prefix drift must not read as an unresolved call.

    The edge target is `acme.sub.deep.helper_fn`; the symbol at its definition
    site is `sub.deep.helper_fn`. Strict FQN equality would call this EXPOSED and
    inflate the exposed arm for every layered repository in the corpus.
    """
    sites, edges, status = _census_and_graph(_build(tmp_path))
    result = classify("sub.deep.helper_fn", "helper_fn", sites, edges, status)
    assert result.primary is Exposure.UNEXPOSED


@pytest.mark.timeout(180)
def test_both_symbols_are_measured_exactly(tmp_path: Path) -> None:
    """Both are single-site pairs, so both belong in the primary table.

    If either fell to MULTI, A6 would hold it out and this fixture would stop
    testing what it claims to test.
    """
    sites, edges, status = _census_and_graph(_build(tmp_path))
    counts = {
        "base": classify("handlers.Base.validate", "validate", sites, edges, status),
        "deep": classify("sub.deep.helper_fn", "helper_fn", sites, edges, status),
    }
    assert [(r.single_site_pairs, r.multi_site_pairs) for r in counts.values()] == [(1, 0), (1, 0)]
