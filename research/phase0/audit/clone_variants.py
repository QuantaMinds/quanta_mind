"""Clone one repository one way, and measure what it cost end to end.

WHAT: `probe` — clones with a given filter, runs one real PR through parent resolution,
      file derivation and the outcome walk, and returns timings plus what the filter
      actually did.
WHY:  Split from `partial_clone.py`, which owns the target list and the decision rule.
      This module owns HOW a variant is measured; that one owns WHICH variants are worth
      measuring and what the answer means. Keeping them apart is what let the clone
      command be corrected without touching the rule it feeds.

      The clone command must match `pipeline/worktree.cloned` exactly, including
      `-c core.longpaths=true`. A probe that clones differently from the pipeline
      measures a different thing: without that flag Windows caps paths at 260 characters
      and Azure's SDK failed on BOTH filters, which would have eliminated both variants
      on a property of the probe rather than of the filter.

      Clone time alone is the wrong measurement. Commit walks, `merge-base` and
      `--name-only` compare tree OIDs and stay blob-free, but symbol extraction parses
      real diff text and fetches -- in single-blob requests with no delta compression, so
      a fast clone can be undone by hundreds of sequential round trips. Hence the whole
      pipeline, and hence the promisor count as a tie-breaker.

      Failures carry their stderr. A denied filter, a lazy-fetch storm and a transient
      network error are three findings, and neither the timing nor the exit code
      separates them.
IMPORTS: stdlib subprocess/shutil/time; phase0.{extract_prs,outcome.scan,parent_commit,
      pipeline.changed,pipeline.worktree}.
CONSUMED BY: audit/partial_clone.py.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from phase0.extract_prs import PRRecord
from phase0.outcome.scan import scan
from phase0.parent_commit import resolve
from phase0.pipeline.changed import changed_python_files
from phase0.pipeline.worktree import CLONE_TIMEOUT_S, _remove_tree


def _failed(repo: str, variant: str, why: str, seconds: float, detail: str = "") -> dict:
    """A clone that never produced a tree. `within_timeout` is False, never absent."""
    return {
        "repo": repo,
        "variant": variant,
        "outcome": why,
        "within_timeout": False,
        "clone_s": round(seconds, 1),
        "stderr": detail,
    }


def _filter_applied(target: Path) -> str:
    """What git recorded as the partial-clone filter, or "none".

    Asserted rather than assumed: github.com may deny a filter and quietly serve a full
    clone, which would show up as a fast variant that is really the baseline.
    """
    out = subprocess.run(
        ["git", "config", "--get", "remote.origin.partialclonefilter"],
        cwd=target,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return out.stdout.strip() or "none"


def _promisor_packs(target: Path) -> int:
    """Packs marked promisor, i.e. arriving from a lazy fetch rather than the clone."""
    packs = target / ".git" / "objects" / "pack"
    return len(list(packs.glob("*.promisor"))) if packs.is_dir() else 0


def _tree_size_kb(target: Path) -> int:
    """On-disk size, or -1 when the tree cannot be walked.

    Never raises. `core.longpaths=true` lets git CREATE paths past 260 characters but
    does nothing for Python's own filesystem calls -- the same asymmetry `worktree.py`
    documents -- and dagster nests `python_modules/automation` deep enough that `rglob`
    dies with WinError 3. Size is a DIAGNOSTIC and appears nowhere in the decision rule,
    so it must not be able to abort the measurement that does decide.
    """
    total = 0
    try:
        for entry in target.rglob("*"):
            try:
                if entry.is_file():
                    total += entry.stat().st_size
            except OSError:
                continue
    except OSError:
        return -1
    return total // 1024


def probe(repo: str, variant: str, flags: list[str], pr: dict, work: Path) -> dict:
    """Clone, run one PR through the pipeline, and report what it cost."""
    target = work / f"{repo.replace('/', '__')}__{variant}"
    # `worktree._remove_tree`, not `shutil.rmtree(ignore_errors=True)`. That flag
    # silently does nothing on Windows -- git's object files are read-only, unlink
    # raises EACCES, and the error is swallowed -- so the directory survives and the
    # NEXT clone fails with "destination path already exists". worktree.py records
    # that exact failure, and this probe reproduced it by copying the broken pattern
    # instead of reusing the corrected one.
    if target.exists():
        _remove_tree(target, strict=False)
    target.parent.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    clone = [
        "git",
        "-c",
        "core.longpaths=true",
        "clone",
        "--quiet",
        *flags,
        f"https://github.com/{repo}.git",
        str(target),
    ]
    try:
        done = subprocess.run(
            clone,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=CLONE_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _failed(repo, variant, "clone_timeout", float(CLONE_TIMEOUT_S))
    clone_s = time.monotonic() - started
    if done.returncode != 0:
        return _failed(repo, variant, "clone_failed", clone_s, done.stderr.strip()[-300:])

    applied = _filter_applied(target)
    before = _promisor_packs(target)

    pipeline_started = time.monotonic()
    parent = resolve(
        target, pr["merge_sha"], frozenset(pr["files"]), pr["commits"], tuple(pr["subjects"])
    )
    derived = (
        changed_python_files(target, parent.parent_sha, pr["merge_sha"])
        if parent.is_resolved
        else []
    )
    verdict = scan(
        target,
        PRRecord(
            pr_id=str(pr["pr_id"]),
            repo=repo,
            language="python",
            parent_sha=parent.parent_sha,
            merged_sha=pr["merge_sha"],
            merged_at=pr["merged_at"],
            changed_files=tuple(derived),
            changed_symbols=(),
            base_ref=pr["base_ref"],
        ),
    )
    pipeline_s = time.monotonic() - pipeline_started
    total = clone_s + pipeline_s

    result = {
        "repo": repo,
        "variant": variant,
        "outcome": "ok",
        "partialclonefilter": applied,
        "filter_actually_applied": applied != "none",
        "clone_s": round(clone_s, 1),
        "pipeline_s": round(pipeline_s, 1),
        "total_s": round(total, 1),
        "within_timeout": total < CLONE_TIMEOUT_S,
        "size_kb": _tree_size_kb(target),
        "lazy_fetches": _promisor_packs(target) - before,
        "parent_resolved": parent.is_resolved,
        "derived_files": len(derived),
        "scan_outcome": verdict.outcome.value,
    }
    _remove_tree(target, strict=False)
    return result
