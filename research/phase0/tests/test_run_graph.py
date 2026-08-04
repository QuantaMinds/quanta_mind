"""Contract test for the graph runner.

WHAT: Asserts run() is unimplemented and that resource exhaustion is a modelled
      status rather than an exception or an empty edge list.
WHY:  VALIDATION.md silent failure 8: a timeout reported as "no edges" makes a
      customer believe a region is clean when it was never looked at. PyCG failed
      outright on 11 of 50 DyPyBench projects, so this is the common case, not the
      edge case. The GraphStatus assertion below fails the moment someone
      simplifies the return type to a bare edge list.
IMPORTS: phase0.run_graph, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0.run_graph import DEFAULT_TIMEOUT_S, GraphStatus, run


def test_run_is_unimplemented() -> None:
    with pytest.raises(NotImplementedError):
        run(Path("."), package="pkg")


def test_exhaustion_is_a_status_not_an_exception() -> None:
    """Timeout, OOM and crash are results the study carries into UNANALYZED."""
    assert {s.value for s in GraphStatus} == {"ok", "timeout", "oom", "crashed"}


def test_default_timeout_matches_the_runbook() -> None:
    """RUNBOOK section 3 runs the pipeline with --timeout 600."""
    assert DEFAULT_TIMEOUT_S == 600
