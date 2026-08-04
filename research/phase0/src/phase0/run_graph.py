"""The instrument: run PyCG over a checkout and classify how it ended.

WHAT: Invokes PyCG as a subprocess under a wall-clock and memory limit, parses its
      edge map, and returns a status saying why the result may be incomplete.
WHY:  PyCG produced no graph at all for 11 of 50 DyPyBench projects -- 6 timeouts,
      3 OOMs, 2 crashes. Resource exhaustion is the common case, not the edge
      case, so it is captured as a status and carried forward. Collapsing it into
      "no edges found" is VALIDATION.md silent failure 8: a customer believes a
      region is clean when it was never looked at.

      SYNTAX_UNSUPPORTED is separate from OOM and TIMEOUT by amendment A7. PyCG
      parses with its host interpreter's ast, pinned at CPython 3.10, so a repo
      using `except*` (3.11) or `type X = ...` (3.12) fails because our toolchain
      is behind, not because the code is dynamic. RUNBOOK section 4.4 reads the
      UNANALYZED arm to decide whether this is a scalability product rather than
      an unsoundness product; letting a fact about our interpreter into that arm
      would let it decide what company this is.

      PyCG is run as a subprocess and never imported: it installs global import
      hooks that would corrupt this process. It also ships no console script, so
      it is invoked as `python -m pycg` -- see ENVIRONMENT.lock.
IMPORTS: stdlib json, re, subprocess, sys. phase0.scope for the file set.
CONSUMED BY: run_pipeline.py, classify_exposure.py; tests/test_run_graph.py.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass

from phase0.pycg_failure import GraphStatus, classify, syntax_location
from phase0.scope import Scope

DEFAULT_TIMEOUT_S = 600
DEFAULT_MEM_LIMIT_GB = 16


@dataclass(frozen=True, slots=True)
class Edge:
    """One caller -> callee edge as the upstream tool reported it."""

    src: str
    dst: str


@dataclass(frozen=True, slots=True)
class GraphResult:
    """Edges plus the reason the set may be incomplete.

    `edges` is empty for every non-OK status, and callers must branch on `status`
    rather than on emptiness -- that is the whole point of the type.
    """

    status: GraphStatus
    duration_ms: int
    edges: tuple[Edge, ...] = ()
    detail: str = ""  # syntax error text, or the tail of stderr
    detail_path: str = ""  # file the parse failed in, when known
    detail_line: int = 0

    @property
    def is_analysable(self) -> bool:
        return self.status is GraphStatus.OK

    @property
    def is_attrition(self) -> bool:
        """A7: excluded from the study rather than assigned to an arm."""
        return self.status.is_attrition


def _limit_memory(mem_limit_gb: int) -> Callable[[], None] | None:
    """A preexec_fn capping address space, or None where that is unavailable.

    POSIX only. On Windows the cap is not applied and the timeout is the only
    bound -- the full run happens on Linux, and ENVIRONMENT.lock records which
    platform produced a result.
    """
    if sys.platform == "win32":
        return None

    import resource

    limit = mem_limit_gb * 1024**3

    def apply() -> None:
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

    return apply


def _parse_edges(payload: str) -> tuple[Edge, ...]:
    """PyCG emits {caller_fqn: [callee_fqn, ...]}. No line numbers, by design."""
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError:
        return ()
    if not isinstance(raw, dict):
        return ()
    return tuple(
        Edge(src=str(src), dst=str(dst))
        for src, callees in raw.items()
        if isinstance(callees, list)
        for dst in callees
    )


def run(
    scope: Scope,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    mem_limit_gb: int = DEFAULT_MEM_LIMIT_GB,
) -> GraphResult:
    """Build a scoped call graph at the repository's current checkout.

    Never raises for an analysis failure. Every way PyCG can fail is a value,
    because a traceback here would be indistinguishable from a region with no
    edges -- and those two must never be the same thing on the wire.
    """
    command = [
        sys.executable,
        "-m",
        "pycg",
        "--package",
        str(scope.package_root),
        *(str(f) for f in scope.files),
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            preexec_fn=_limit_memory(mem_limit_gb),
        )
    except subprocess.TimeoutExpired:
        return GraphResult(
            status=GraphStatus.TIMEOUT,
            duration_ms=timeout_s * 1000,
            detail=f"exceeded {timeout_s}s on {scope.file_count} files",
        )
    except OSError as exc:
        return GraphResult(status=GraphStatus.CRASHED, duration_ms=0, detail=str(exc))

    if completed.returncode != 0:
        status, detail = classify(completed.returncode, completed.stderr)
        path, line = syntax_location(completed.stderr)
        return GraphResult(
            status=status,
            duration_ms=0,
            detail=detail,
            detail_path=path,
            detail_line=line,
        )

    return GraphResult(
        status=GraphStatus.OK,
        duration_ms=0,
        edges=_parse_edges(completed.stdout),
    )
