"""Verification of the graph runner and its failure taxonomy.

WHAT: Asserts that PyCG's real output parses into edges, that the super() edge is
      genuinely absent, and that each way of failing maps to the right status —
      in particular that a parse failure is SYNTAX_UNSUPPORTED, not CRASHED.
WHY:  Two things are being protected.

      VALIDATION.md silent failure 8: a timeout reported as "no edges" makes a
      customer believe a region is clean when it was never looked at. Every
      failure must therefore be a value, never an exception and never an empty
      edge list that looks like a clean result.

      Amendment A7: SYNTAX_UNSUPPORTED is excluded from the study as corpus
      attrition, while TIMEOUT and OOM form the UNANALYZED_RESOURCE arm that
      RUNBOOK section 4.4 reads to decide what kind of product this is. Merging
      them would let the age of our interpreter decide that question.
IMPORTS: phase0.run_graph, phase0.scope, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0 import scope
from phase0.run_graph import DEFAULT_TIMEOUT_S, GraphStatus, run

# Reproduces README.md's example: the base method has no incoming edge.
SWITCHBOARD = '''\
"""Fixture: super() is the switchboard PyCG cannot see through."""


class Base:
    def validate(self, req):
        return True


class Stripe(Base):
    def validate(self, req):
        return super().validate(req)
'''

# `type X = ...` is PEP 695, Python 3.12. PyCG runs on 3.10 and cannot parse it.
MODERN_SYNTAX = '''\
"""Fixture: syntax newer than the instrument's interpreter."""

type Handler = str


def use(h: Handler) -> str:
    return h
'''


def _scope_for(tmp_path: Path, name: str, source: str) -> scope.Scope:
    pkg = tmp_path / "acme"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / name).write_text(source, encoding="utf-8")
    resolved = scope.resolve(tmp_path, [f"acme/{name}"])
    assert resolved is not None
    return resolved


def test_default_timeout_matches_the_runbook() -> None:
    """RUNBOOK section 3 runs the pipeline with --timeout 600."""
    assert DEFAULT_TIMEOUT_S == 600


def test_exhaustion_is_a_status_not_an_exception() -> None:
    """Every way the instrument can fail is a value carried into the arms."""
    assert {s.value for s in GraphStatus} == {
        "ok",
        "timeout",
        "oom",
        "crashed",
        "syntax_unsupported",
    }


def test_syntax_failure_is_attrition_not_an_arm() -> None:
    """A7: only SYNTAX_UNSUPPORTED is attrition; resource failures are an arm."""
    attrition = {s for s in GraphStatus if s is GraphStatus.SYNTAX_UNSUPPORTED}
    assert attrition == {GraphStatus.SYNTAX_UNSUPPORTED}


@pytest.mark.timeout(120)
def test_real_run_produces_edges(tmp_path: Path) -> None:
    """Runs the real instrument. No mock could tell us PyCG's output shape."""
    result = run(_scope_for(tmp_path, "handlers.py", SWITCHBOARD), timeout_s=90)
    assert result.status is GraphStatus.OK
    assert len(result.edges) > 0


@pytest.mark.timeout(120)
def test_super_edge_is_absent_from_the_real_graph(tmp_path: Path) -> None:
    """The founding example, asserted against real output rather than quoted.

    PyCG emits an edge to <builtin>.super and none to Base.validate, so the base
    method sits in the graph with no incoming edge from its subclass. That gap is
    what the census counts and the product sells.
    """
    result = run(_scope_for(tmp_path, "handlers.py", SWITCHBOARD), timeout_s=90)
    targets = {e.dst for e in result.edges if e.src.endswith("Stripe.validate")}
    assert not any(t.endswith("Base.validate") for t in targets)


@pytest.mark.timeout(120)
def test_modern_syntax_is_excluded_not_crashed(tmp_path: Path) -> None:
    """A7's kill-check, on a real file the pinned interpreter cannot parse.

    PEP 695 shipped in 3.12; PyCG is pinned to 3.10 by ENVIRONMENT.lock. If this
    were reported as CRASHED it would enter UNANALYZED and corrupt the arm that
    decides whether this is a scalability product.
    """
    result = run(_scope_for(tmp_path, "modern.py", MODERN_SYNTAX), timeout_s=90)
    assert result.status is GraphStatus.SYNTAX_UNSUPPORTED
    assert result.is_attrition is True


@pytest.mark.timeout(120)
def test_syntax_failure_names_the_repository_file(tmp_path: Path) -> None:
    """The reported path must be the offending source, not our own runpy.py.

    The first `File "..."` line in a traceback is the interpreter entry point; the
    offending source is the last. An earlier version took the first match and
    reported CPython's runpy.py for every failure, which is indistinguishable
    across repositories and would make A7's attrition data useless -- the pilot
    has to tell "syntax newer than 3.10" apart from anything else.
    """
    result = run(_scope_for(tmp_path, "modern.py", MODERN_SYNTAX), timeout_s=90)
    assert Path(result.detail_path).name == "modern.py"


@pytest.mark.timeout(60)
def test_timeout_is_reported_as_timeout(tmp_path: Path) -> None:
    """A zero-second budget must yield TIMEOUT, not a crash or an empty graph."""
    result = run(_scope_for(tmp_path, "handlers.py", SWITCHBOARD), timeout_s=0)
    assert result.status is GraphStatus.TIMEOUT
    assert result.edges == ()
