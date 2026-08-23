"""Obtain a local clone for a repository, and keep it current without re-cloning it.

WHAT: `ensure(repo, root)` returns a path to a full clone of `repo`, cloning on first use and
      fetching on every use after. `sweep(root, keep)` deletes the least recently used clones and
      RETURNS how many it removed.
WHY:  **A REVIEW READS HISTORY, SO THE ENDPOINT NEEDS A CLONE AND THE CLI GETS ONE FROM ITS
      OPERATOR.** `run_review.review()` takes `clone` as an argument precisely so the socket layer
      decides where it comes from. This is that decision for the endpoint.

      **A BLOB-FILTERED CLONE IS NOT USED, AND THAT IS DELIBERATE.** `--filter=blob:none` would
      make the first clone far faster and is exactly the wrong trade here: `git log -p` exits
      non-zero on a blob-filtered clone and emits a truncated patch stream. That defect voided four
      measurements in this project.

      **`sweep()` RETURNS THE COUNT RATHER THAN CLAIMING A CLEANUP HAPPENED.** A cleanup path here
      once carried the comment "a leftover is caught by the strict pass on the next attempt"; the
      next attempt was a different repository, nothing checked, and 1.6 GB accumulated. Rule 14
      exists because of it, so the number is observable rather than asserted.

      **A FETCH FAILURE ON AN EXISTING CLONE IS FATAL, NOT A FALLBACK.** Reviewing against a stale
      history scores a pull request on commits that predate it, and the output looks entirely
      normal -- same shape, same coverage line, a ranking drawn from the wrong past. Neither
      `ingest/` nor the reader can tell.
IMPORTS: stdlib only. Rightmost layer.
CONSUMED BY: `serve/review_delivery.py`.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

CLONE_TIMEOUT_S = 900
FETCH_TIMEOUT_S = 300
DEFAULT_KEEP = 8


class CloneFailed(RuntimeError):
    """Carries the repository and what git said. Never a bare failure."""

    def __init__(self, repo: str, reason: str) -> None:
        super().__init__(f"{repo}: {reason}")
        self.repo = repo
        self.reason = reason


def path_for(repo: str, root: Path) -> Path:
    """`owner/name` -> a directory under `root`, refusing anything that could escape it.

    The repository name arrives from a webhook payload. It is authenticated by HMAC, so it is not
    arbitrary -- but "authenticated" is not "well-formed", and a path built from a remote string
    without a check is the kind of thing that is only ever noticed afterwards.
    """
    parts = repo.split("/")
    if len(parts) != 2 or not all(p.strip() for p in parts):
        raise CloneFailed(repo, "expected exactly 'owner/name'")
    if any(p in {".", ".."} or "\\" in p or p.startswith("-") for p in parts):
        raise CloneFailed(repo, "path traversal or option injection in the repository name")
    return root / parts[0] / parts[1]


def ensure(repo: str, root: Path) -> Path:
    """A current full clone of `repo`. Clones on first use, fetches thereafter.

    Fetches `+refs/pull/*/head` as well as the branches, because the head of a pull request opened
    from a fork is on no branch of the upstream repository and a plain fetch will not have it.
    """
    where = path_for(repo, root)
    if (where / ".git").is_dir():
        done = subprocess.run(
            [
                "git",
                "-C",
                str(where),
                "fetch",
                "--prune",
                "origin",
                "+refs/heads/*:refs/remotes/origin/*",
                "+refs/pull/*/head:refs/remotes/origin/pr/*",
            ],
            capture_output=True,
            text=True,
            timeout=FETCH_TIMEOUT_S,
        )
        if done.returncode != 0:
            # NOT a fallback to the stale clone. See the module docstring.
            raise CloneFailed(repo, f"fetch exited {done.returncode}: {done.stderr.strip()[:160]}")
        return where

    where.parent.mkdir(parents=True, exist_ok=True)
    done = subprocess.run(
        ["git", "clone", "--no-checkout", f"https://github.com/{repo}.git", str(where)],
        capture_output=True,
        text=True,
        timeout=CLONE_TIMEOUT_S,
    )
    if done.returncode != 0:
        # A half-written directory would be taken for a good clone on the next delivery.
        shutil.rmtree(where, ignore_errors=True)
        raise CloneFailed(repo, f"clone exited {done.returncode}: {done.stderr.strip()[:160]}")
    return ensure(repo, root)


def sweep(root: Path, keep: int = DEFAULT_KEEP) -> int:
    """Delete all but the `keep` most recently modified clones. Returns how many were removed."""
    if not root.is_dir():
        return 0
    clones = [
        p
        for owner in root.iterdir()
        if owner.is_dir()
        for p in owner.iterdir()
        if (p / ".git").is_dir()
    ]
    clones.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    for stale in clones[max(0, keep) :]:
        shutil.rmtree(stale, ignore_errors=True)
        removed += 1
    return removed
