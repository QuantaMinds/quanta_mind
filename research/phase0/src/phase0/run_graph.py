"""The instrument: run a call-graph tool over a repository at one commit.

WHAT: Invokes PyCG (Python arm) or a JS tool (TS/JS arm) scoped to the changed
      package, under a wall-clock and memory limit, and returns edges plus a
      status. A timeout or OOM is a RESULT, not an error.
WHY:  PyCG produced no graph at all for 11 of 50 DyPyBench projects -- 6 timeouts,
      3 OOMs, 2 crashes. RUNBOOK section 3 expects ~78% success and says a 0%
      timeout rate means something is wrong, because it would mean the UNANALYZED
      arm is empty when it should not be. So resource exhaustion is captured as
      GraphStatus and carried forward, never collapsed into "no edges found" --
      that collapse is silent failure 8 in VALIDATION.md.

      PyCG is pinned to 0.0.7 on CPython 3.10 and invoked as `python -m pycg`;
      0.0.8 is unusable and there is no console script. All three findings are
      recorded in ENVIRONMENT.lock.
IMPORTS: stdlib subprocess. pycg is invoked as a subprocess, never imported --
      it installs global import hooks that would corrupt this process.
CONSUMED BY: run_pipeline.py, classify_exposure.py; tests/test_run_graph.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

DEFAULT_TIMEOUT_S = 600
DEFAULT_MEM_LIMIT_GB = 16


class GraphStatus(Enum):
    """Why we do or do not have a graph for this region."""

    OK = "ok"
    TIMEOUT = "timeout"
    OOM = "oom"
    CRASHED = "crashed"


@dataclass(frozen=True, slots=True)
class Edge:
    """One caller -> callee edge as the upstream tool reported it."""

    src: str
    dst: str


@dataclass(frozen=True, slots=True)
class GraphResult:
    """Edges plus the reason the set may be incomplete."""

    edges: tuple[Edge, ...]
    status: GraphStatus
    duration_ms: int


def run(
    repo: Path,
    package: str,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    mem_limit_gb: int = DEFAULT_MEM_LIMIT_GB,
) -> GraphResult:
    """Build a scoped call graph at the repository's current checkout.

    Raises:
        NotImplementedError: Day 1 of the run. See RUNBOOK section 1.
    """
    raise NotImplementedError("Phase 0 Day 1 — see docs/findings/PHASE0_RUNBOOK.md")
