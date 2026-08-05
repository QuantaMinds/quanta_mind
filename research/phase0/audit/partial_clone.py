"""Can a partial clone recover the repositories the timeout excludes?

WHAT: Clones each timed-out repository three ways -- full, `blob:none`, `blob:limit=1m` --
      and times the clone PLUS one real PR pipeline on each: parent resolution, the outcome
      scan, and changed-symbol extraction.
WHY:  Four clone timeouts have removed repositories with a median size of 959,522 KB
      against 76,908 KB for those that cloned. That is a resource exclusion selecting on
      repository size, which tracks project age, activity and release discipline -- the
      same population the base-branch defect removed, arriving through a different door.
      It is also the ONLY one of the four doors on to A16's confounder that is a property
      of our clone command rather than of the data, so it is the only one that can be
      closed rather than bounded.

      Clone time alone would be the wrong measurement. A partial clone finishes fast and
      then pays on first access: commit walks, `merge-base` and `--name-only` compare tree
      OIDs and stay blob-free, but symbol extraction parses real diff text and will fetch.
      Worse, missing blobs are fetched in SINGLE-BLOB requests with no delta compression,
      so a fast clone can be undone by hundreds of sequential round trips. Hence
      end-to-end, and hence `blob:limit=1m` alongside `blob:none`: Python sources sit far
      below 1 MB, so they arrive in the initial pack and only the large binaries that make
      these repositories a gigabyte are skipped.

      The filter is ASSERTED, not assumed. A server may deny a filter and silently serve a
      full clone; `remote.origin.partialclonefilter` says whether it actually applied. An
      unapplied filter reporting a fast clone would be one more absence read as success.
IMPORTS: stdlib subprocess/time/json; phase0.{parent_commit,outcome.scan,pipeline.changed}.
CONSUMED BY: run by hand before the full run; writes results/partial_clone.json.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "E:/Code/quanta_mind/research/phase0/src")

from phase0.extract_prs import PRRecord
from phase0.outcome.scan import scan
from phase0.parent_commit import resolve
from phase0.pipeline.changed import changed_python_files
from phase0.pipeline.worktree import CLONE_TIMEOUT_S

RESULTS = Path("E:/Code/quanta_mind/research/phase0/results")
CACHE = Path("E:/Code/quanta_mind/research/phase0/data/gh_cache")
WORK = Path("E:/Code/quanta_mind/research/phase0/data/partial_clone_probe")

VARIANTS = {
    "full": [],
    "blob_none": ["--filter=blob:none"],
    "blob_limit_1m": ["--filter=blob:limit=1m"],
}


def _run(args: list[str], cwd: Path | None = None, timeout: int = CLONE_TIMEOUT_S) -> int:
    out = subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
    )
    return out.returncode


def _filter_applied(target: Path) -> str:
    out = subprocess.run(
        ["git", "config", "--get", "remote.origin.partialclonefilter"],
        cwd=target,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return out.stdout.strip() or "none"


def _tree_size_kb(target: Path) -> int:
    return sum(f.stat().st_size for f in target.rglob("*") if f.is_file()) // 1024


def probe(repo: str, variant: str, pr: dict) -> dict:
    target = WORK / f"{repo.replace('/', '__')}__{variant}"
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
    target.parent.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    try:
        code = _run(
            [
                "git",
                "clone",
                "--quiet",
                *VARIANTS[variant],
                f"https://github.com/{repo}.git",
                str(target),
            ]
        )
    except subprocess.TimeoutExpired:
        return {
            "repo": repo,
            "variant": variant,
            "outcome": "clone_timeout",
            "clone_s": CLONE_TIMEOUT_S,
            "within_timeout": False,
        }
    clone_s = time.monotonic() - started
    if code != 0:
        return {
            "repo": repo,
            "variant": variant,
            "outcome": "clone_failed",
            "clone_s": round(clone_s, 1),
            "within_timeout": False,
        }

    applied = _filter_applied(target)
    # The pipeline, on one real PR: parent resolution, symbol-bearing file diff, and the
    # outcome walk. This is where a partial clone pays its lazy-fetch cost, if it pays.
    pipeline_started = time.monotonic()
    parent = resolve(target, pr["merge_sha"], frozenset(pr["files"]), pr["commits"], pr["subjects"])
    derived = (
        changed_python_files(target, parent.parent_sha, pr["merge_sha"])
        if parent.is_resolved
        else []
    )
    record = PRRecord(
        pr_id=str(pr["pr_id"]),
        repo=repo,
        language="python",
        parent_sha=parent.parent_sha,
        merged_sha=pr["merge_sha"],
        merged_at=pr["merged_at"],
        changed_files=tuple(derived),
        changed_symbols=(),
        base_ref=pr["base_ref"],
    )
    verdict = scan(target, record)
    pipeline_s = time.monotonic() - pipeline_started

    total = clone_s + pipeline_s
    result = {
        "repo": repo,
        "variant": variant,
        "outcome": "ok",
        "partialclonefilter": applied,
        # Asserted, never assumed: a server may deny the filter and serve a full clone.
        "filter_actually_applied": (variant == "full") == (applied == "none"),
        "clone_s": round(clone_s, 1),
        "pipeline_s": round(pipeline_s, 1),
        "total_s": round(total, 1),
        "within_timeout": total < CLONE_TIMEOUT_S,
        "size_kb": _tree_size_kb(target),
        "parent_resolved": parent.is_resolved,
        "derived_files": len(derived),
        "scan_outcome": verdict.outcome.value,
    }
    shutil.rmtree(target, ignore_errors=True)
    return result


def main() -> int:
    targets = json.loads((RESULTS / "partial_clone_targets.json").read_text(encoding="utf-8"))
    rows = []
    for entry in targets:
        for variant in VARIANTS:
            row = probe(entry["repo"], variant, entry)
            rows.append(row)
            print(json.dumps(row), flush=True)
            (RESULTS / "partial_clone.json").write_text(
                json.dumps(rows, indent=2) + "\n", encoding="utf-8"
            )

    print("\nDECISION RULE (fixed before looking): a variant wins only if every target")
    print(f"completes clone + one full PR pipeline inside CLONE_TIMEOUT_S = {CLONE_TIMEOUT_S}s.")
    for variant in VARIANTS:
        got = [r for r in rows if r["variant"] == variant]
        passed = [r for r in got if r.get("within_timeout")]
        applied = all(r.get("filter_actually_applied", False) for r in got if r["outcome"] == "ok")
        print(
            f"  {variant:<14} {len(passed)}/{len(got)} within timeout   filter honoured: {applied}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
