"""Ask git, and only git, what touched a path and when.

WHAT: `timestamps()` returns every commit touching a path, oldest first. `deletions()` returns the
      commits that removed it.
WHY:  Split from `assert_pack_matches_git.py` at the 200-line cap, and it is the right seam: this
      is the ORACLE, and it must know nothing about how the pack was built. `ingest` reads one
      `git log --name-only` over the whole history; this asks per path, so a shared misreading of a
      single stream cannot make both agree.

      **`--full-history` or the oracle is wrong.** Plain `git log -- <path>` applies history
      simplification and omits commits whose content matched a parent -- 6 against our 7 for
      `src/flask/ctx.py`. `test_counts_match_git.py` failed the product for being right once over
      exactly this, and `ingest/commits.py` carried the same defect in the other direction.
IMPORTS: stdlib only (collections, pathlib, subprocess).
CONSUMED BY: scripts/verify/assert_pack_matches_git.py.
"""

from __future__ import annotations

import collections
import pathlib
import subprocess

GIT_TIMEOUT_S = 120


def timestamps(clone: pathlib.Path, path: str) -> list[int]:
    """Every commit touching `path`, oldest first, asked of git ALONE.

    `--full-history` because plain `git log -- <path>` simplifies away commits whose content
    matched a parent, and a touch count means every commit that touched the file.
    """
    done = subprocess.run(
        [
            "git",
            "-c",
            "core.commitGraph=false",
            "-C",
            str(clone),
            "log",
            "--full-history",
            "--no-merges",
            "--reverse",
            "--format=%ct",
            "--",
            path,
        ],
        capture_output=True,
        timeout=GIT_TIMEOUT_S,
    )
    if done.returncode != 0:
        raise SystemExit(
            f"[pack-vs-git] git log for {path!r} exited {done.returncode}: "
            f"{done.stderr.decode('utf-8', 'replace')[:200]}"
        )
    return [int(line) for line in done.stdout.decode("utf-8", "replace").split() if line.strip()]


def deletions(clone: pathlib.Path, path: str) -> collections.Counter[int]:
    """When `path` was DELETED, which is exactly what a wildcard `--name-only` read cannot see.

    A rename counts: `src/flask/app.py` -> `src/flask/sansio/app.py` is a deletion of the old path,
    reported by a per-path query and absent from ours. Flask then re-created `app.py` as a shim, so
    "present in HEAD" does NOT mean "never deleted" -- the first version of this check assumed it
    did and reported two false disagreements.
    """
    done = subprocess.run(
        [
            "git",
            "-C",
            str(clone),
            "log",
            "--full-history",
            "--no-merges",
            "--diff-filter=D",
            "--format=%ct",
            "--",
            path,
        ],
        capture_output=True,
        timeout=GIT_TIMEOUT_S,
    )
    if done.returncode != 0:
        raise SystemExit(f"[pack-vs-git] deletion query for {path!r}: {done.stderr[:200]!r}")
    return collections.Counter(
        int(x) for x in done.stdout.decode("utf-8", "replace").split() if x.strip()
    )
