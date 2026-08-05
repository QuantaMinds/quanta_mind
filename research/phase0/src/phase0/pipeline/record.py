"""The per-PR audit record, its provenance, and the append-only checkpoint.

WHAT: One JSON line per PR, written the moment that PR completes, plus the reader
      that lets a restart skip what is already done.
WHY:  Every field here is one that cannot be added later without re-running the
      corpus, which is why the list is longer than it looks:

      - `parent_resolution_method` — merge / squash / rebase / ambiguous. Without
        it, A2's attrition cannot be reported by case, and rebase-heavy
        repositories skew larger and more process-heavy than average.
      - `single_site_pairs` / `multi_site_pairs` — drives A6's primary versus
        sensitivity split. Recomputing them means recomputing the graph.
      - `no_static_callee_sites` — A10's prevalence denominator. It bounds how
        much of the problem the exposure variable is structurally blind to, and
        it is the only number that makes the null's scope statable.
      - `graph_status` with the offending construct and line — A7's attrition,
        and the pilot's kill-check on whether PyCG-on-3.10 is viable at all.
      - the four version fields, on EVERY record. If half the corpus is re-run
        after a fix, the only way to know which half is to have stamped it.
      - `duration_ms` per stage — this is what sizes the full run from the pilot.

      Written append-only, per PR, never buffered to a final batch. A crash at
      hour 28 with results held in memory loses the run; a crash with them on disk
      loses one PR.
IMPORTS: stdlib dataclasses, json, platform, subprocess. importlib.metadata for
      pinned versions.
CONSUMED BY: run_pipeline.py; tests/test_run_pipeline.py.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

GIT_TIMEOUT_S = 30


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unknown"


def _pipeline_sha() -> str:
    """The harness commit that produced a record."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    return result.stdout.strip() if result.returncode == 0 else "unknown"


@dataclass(frozen=True, slots=True)
class Provenance:
    """Stamped on every record so a partial re-run stays interpretable."""

    pycg_version: str
    tree_sitter_version: str
    python_version: str
    pipeline_git_sha: str
    # Which machine. The memory cap is enforceable on linux and refused on darwin, so
    # two records with identical versions can still have run under different bounds --
    # and OOM cannot populate the resource arm at all where the cap was refused.
    platform: str

    @classmethod
    def current(cls) -> Provenance:
        return cls(
            pycg_version=_package_version("pycg"),
            tree_sitter_version=_package_version("tree-sitter"),
            python_version=platform.python_version(),
            pipeline_git_sha=_pipeline_sha(),
            platform=f"{sys.platform}-{platform.machine()}",
        )


@dataclass(frozen=True, slots=True)
class SymbolRow:
    """One changed symbol's arms and the diagnostics A6 requires."""

    symbol: str
    primary: str = ""  # "" means no measurable pair: outside the primary table
    sensitivity_low: str = ""
    sensitivity_high: str = ""
    single_site_pairs: int = 0
    multi_site_pairs: int = 0


@dataclass(frozen=True, slots=True)
class PRAudit:
    """Everything known about one PR after the exposure pass."""

    pr_id: str
    repo: str
    repo_id: str
    arm: str
    task_type: str = ""
    parent_sha: str = ""
    merged_sha: str = ""
    parent_resolution_method: str = ""
    graph_status: str = ""
    # The memory bound this PR's graph run actually had, from GraphResult.mem_cap.
    # Empty means UNRECORDED -- a stage that failed before the graph ran. It does not
    # mean "bounded", and an OOM arm assembled from runs that were never capped
    # measures the machine. A30 claimed this travelled on the result; it travelled as
    # far as the in-memory object and was dropped here, so no run on disk stated its
    # bound. Per-record rather than on Provenance because the limit is a call argument.
    mem_cap: str = ""
    graph_detail: str = ""
    graph_detail_path: str = ""
    graph_detail_line: int = 0
    scope_files: int = 0
    call_sites: int = 0
    non_builtin_sites: int = 0
    no_static_callee_sites: int = 0  # A10's prevalence denominator
    symbols: tuple[SymbolRow, ...] = ()
    stage_failed: str = ""  # which stage, not just that one did
    error: str = ""
    duration_ms: dict[str, int] = field(default_factory=dict)
    provenance: Provenance = field(default_factory=Provenance.current)

    @property
    def succeeded(self) -> bool:
        return not self.stage_failed


def append(path: Path, audit: PRAudit) -> None:
    """Write one record immediately. Append-only, one JSON object per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(audit), sort_keys=True) + "\n")
        handle.flush()


def completed_ids(path: Path) -> set[str]:
    """PR ids already on disk, so a restart resumes rather than repeats.

    A truncated final line -- the signature of a crash mid-write -- is skipped
    rather than fatal: that PR simply gets redone.
    """
    if not path.is_file():
        return set()
    done: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                done.add(str(json.loads(line)["pr_id"]))
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    return done


def read_all(path: Path) -> Iterator[dict[str, object]]:
    """Every complete record, for the analysis pass."""
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                yield dict(json.loads(line))
            except json.JSONDecodeError:
                continue
