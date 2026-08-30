"""Two questions about whether a commit is still in this repository's history.

WHAT: `head_sha(repo_dir)` names the current HEAD. `is_ancestor(repo_dir, sha)` says whether a
      stored commit is still reachable from it.
WHY:  **AN INDEX WATERMARK IS ONLY MEANINGFUL IF THE COMMIT IT NAMES IS STILL THERE.** A
      force-push, rebase or squash-merge replaces commits, and `git log <sha>..HEAD` from a
      watermark that is no longer reachable returns a set missing everything the rewrite dropped.
      The result is a short index, and a short index looks exactly like a quiet repository — no
      error, no warning, a ranking computed against a history that stopped early.

      Split from `ingest/commits.py` because that file is the one place the product runs `git log`
      and had reached the 200-line cap; these are `rev-parse` and `merge-base`, a different
      question with a different failure. They carry their own runner rather than importing that
      module's private one, which rule 7 forbids reaching for.
IMPORTS: stdlib only (subprocess). Same layer as `commits`, no sibling internals.
CONSUMED BY: `serve/commands/run_review.py`, deciding whether the touch index can be extended.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

PROBE_TIMEOUT_S = 30


def _probe(repo_dir: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        capture_output=True,
        text=True,
        timeout=PROBE_TIMEOUT_S,
    )


def head_sha(repo_dir: Path) -> str:
    """The commit `HEAD` names, or `""` when there is none. This is the watermark."""
    got = _probe(repo_dir, ["rev-parse", "HEAD"])
    return got.stdout.strip() if got.returncode == 0 else ""


def is_ancestor(repo_dir: Path, sha: str) -> bool:
    """Whether `sha` is still reachable from HEAD. **False means the history was rewritten.**

    An empty `sha` is False rather than an error: "we have no watermark" and "our watermark is
    stale" both mean the same thing to the caller, which is read everything.
    """
    if not sha:
        return False
    return _probe(repo_dir, ["merge-base", "--is-ancestor", sha, "HEAD"]).returncode == 0
