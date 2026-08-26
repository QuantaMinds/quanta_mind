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
from collections.abc import Sequence
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


def _present(where: Path, pull_refs: Sequence[int], timeout_s: int) -> list[int]:
    """The subset of `pull_refs` the remote actually has.

    **AN EXPLICIT REFSPEC IS STRICT AND A WILDCARD IS NOT.** A pull head that does not exist fails
    the WHOLE fetch -- `fatal: couldn't find remote ref`, exit 128 -- where the wildcard matched
    whatever was there. So this asks first, in one `ls-remote` that moves no objects.
    """
    if not pull_refs:
        return []
    done = subprocess.run(
        [
            "git",
            "-C",
            str(where),
            "ls-remote",
            "origin",
            *(f"refs/pull/{n}/head" for n in pull_refs),
        ],
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )
    if done.returncode != 0:
        return list(pull_refs)  # let the fetch report the real failure rather than guessing here
    have = {
        line.split("refs/pull/")[1].split("/")[0]
        for line in done.stdout.splitlines()
        if "refs/pull/" in line
    }
    return [n for n in pull_refs if str(n) in have]


def _pull_refspecs(pull_refs: Sequence[int] | None) -> list[str]:
    """Refspecs for the pull heads asked for. None means every one, which is the old behaviour."""
    if pull_refs is None:
        return ["+refs/pull/*/head:refs/remotes/pull/*"]
    return [f"+refs/pull/{n}/head:refs/remotes/pull/{n}" for n in pull_refs]


def ensure(
    repo: str,
    root: Path,
    *,
    clone_timeout_s: int = CLONE_TIMEOUT_S,
    fetch_timeout_s: int = FETCH_TIMEOUT_S,
    pull_refs: Sequence[int] | None = None,
) -> Path:
    """A current full clone of `repo`. Clones on first use, fetches thereafter.

    **THE TIMEOUTS ARE ARGUMENTS BECAUSE THE DEFAULT IS A PRODUCT DECISION AND A BENCH RUN IS
    NOT.** 900 seconds is not enough for grafana -- 1.9 GB plus every `refs/pull/*` ref timed out
    mid-clone and cost the run that repository's ten pull requests. Raising the shipped default
    for a research harness would change what a customer's delivery waits for, so the harness
    passes its own value and the endpoint keeps the one it was given.

    **A LONGER CEILING IS NOT FREE.** `review_delivery` blocks on this, so the default bounds how
    long a webhook can sit on one delivery.

    **`pull_refs` NARROWS THE FETCH, AND THE WILDCARD IS NOT A ROUNDING ERROR.** grafana carries
    **83,202** pull-head refs and home-assistant/core 105,913; a review needs ONE. Fetching all of
    them timed out at 900s, then ran 25 minutes and exited 1 at 2700s. `None` keeps the wildcard so
    nothing changes for a caller that does not ask; an empty sequence fetches branches only.

    Fetches `+refs/pull/*/head` as well as the branches, because the head of a pull request opened
    from a fork is on no branch of the upstream repository and a plain fetch will not have it.

    **PULL HEADS LAND IN `refs/remotes/pull/*`, NOT UNDER `refs/remotes/origin/`.** They used to
    map to `refs/remotes/origin/pr/*`, which collides with any branch actually named `pr/<x>`:
    git refuses the whole fetch with `fatal: Cannot fetch both refs/heads/pr/1 and
    refs/pull/1/head to refs/remotes/origin/pr/1`. It is not hypothetical -- discourse/discourse
    has such a branch, and `ensure()` raised `CloneFailed` on it every time. A separate namespace
    cannot collide with a branch whatever the customer names it.
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
                *_pull_refspecs(
                    None if pull_refs is None else _present(where, pull_refs, fetch_timeout_s)
                ),
            ],
            capture_output=True,
            text=True,
            timeout=fetch_timeout_s,
        )
        if done.returncode != 0:
            # NOT a fallback to the stale clone. See the module docstring.
            # **THE TAIL, NOT THE HEAD.** git writes "From <url>" first and the real failure
            # last, so the leading characters are reliably the part that says nothing.
            tail = done.stderr.strip()[-300:]
            raise CloneFailed(repo, f"fetch exited {done.returncode}: ...{tail}")
        return where

    where.parent.mkdir(parents=True, exist_ok=True)
    done = subprocess.run(
        ["git", "clone", "--no-checkout", f"https://github.com/{repo}.git", str(where)],
        capture_output=True,
        text=True,
        timeout=clone_timeout_s,
    )
    if done.returncode != 0:
        # A half-written directory would be taken for a good clone on the next delivery.
        shutil.rmtree(where, ignore_errors=True)
        raise CloneFailed(repo, f"clone exited {done.returncode}: {done.stderr.strip()[:160]}")
    return ensure(
        repo,
        root,
        clone_timeout_s=clone_timeout_s,
        fetch_timeout_s=fetch_timeout_s,
        pull_refs=pull_refs,
    )


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
