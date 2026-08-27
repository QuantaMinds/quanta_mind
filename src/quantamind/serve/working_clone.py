"""Obtain a local clone for a repository, and keep it current without re-cloning it.

WHAT: `ensure(repo, root, token=...)` returns a path to a full clone of `repo`, cloning on first
      use and fetching on every use after, authenticated when a token is given. `sweep(root, keep)`
      deletes the least recently used clones and RETURNS how many it removed.
WHY:  **A REVIEW READS HISTORY, SO THE ENDPOINT NEEDS A CLONE AND THE CLI GETS ONE FROM ITS
      OPERATOR.** `run_review.review()` takes `clone` as an argument precisely so the socket layer
      decides where it comes from. This is that decision for the endpoint.

      **EVERY GIT COMMAND HERE RUNS WITH A SUPPLIED ENVIRONMENT, NEVER THE AMBIENT ONE.** The
      clone was unauthenticated and passed every test, because on a developer's machine a
      credential helper answered for them and a container has none -- so no customer's private
      repository could ever be read. `ingest/git_credentials.py` holds the whole account.

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
IMPORTS: stdlib, plus `ingest.{git_credentials,pull_refs}` -- leftward, which is allowed.
CONSUMED BY: `serve/review_delivery.py`.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path

from quantamind.ingest.git_credentials import environment
from quantamind.ingest.pull_refs import present, refspecs

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


def ensure(
    repo: str,
    root: Path,
    *,
    clone_timeout_s: int = CLONE_TIMEOUT_S,
    fetch_timeout_s: int = FETCH_TIMEOUT_S,
    pull_refs: Sequence[int] | None = None,
    token: str | None = None,
) -> Path:
    """A current full clone of `repo`. Clones on first use, fetches thereafter.

    **`token` IS THE INSTALLATION TOKEN AND WITHOUT IT ONLY PUBLIC REPOSITORIES WORK.** It is
    threaded into the environment of every git command rather than into the URL, because a URL is
    persisted into `.git/config` and a token expires in an hour; `ingest/git_credentials.py` gives
    the full reasoning. `None` is correct for the bench, which reads public repositories only.

    **THE CLONE FALLS THROUGH INTO THE FETCH RATHER THAN RECURSING.** A fresh clone still needs the
    pull heads, which live outside `refs/heads/*`; doing that as one pass makes the credential and
    the refspecs impossible to apply to one path and forget on the other.

    **THE TIMEOUTS ARE ARGUMENTS BECAUSE THE DEFAULT IS A PRODUCT DECISION AND A BENCH RUN IS
    NOT.** 900 seconds is not enough for grafana -- 1.9 GB plus every `refs/pull/*` ref timed out
    mid-clone and cost the run that repository's ten pull requests. Raising the shipped default
    for a research harness would change what a customer's delivery waits for, so the harness
    passes its own value and the endpoint keeps the one it was given.

    **A LONGER CEILING IS NOT FREE.** `review_delivery` blocks on this, so the default bounds how
    long a webhook can sit on one delivery.

    **`pull_refs` NARROWS THE FETCH, AND WHY IS IN `ingest/pull_refs.py`:** grafana carries 83,202
    pull-head refs and a review needs ONE. That module also explains why the heads are fetched at
    all and why they land outside `refs/remotes/origin/`.
    """
    where = path_for(repo, root)
    env = environment(token)
    if not (where / ".git").is_dir():
        where.parent.mkdir(parents=True, exist_ok=True)
        done = subprocess.run(
            ["git", "clone", "--no-checkout", f"https://github.com/{repo}.git", str(where)],
            capture_output=True,
            text=True,
            timeout=clone_timeout_s,
            env=env,
        )
        if done.returncode != 0:
            # A half-written directory would be taken for a good clone on the next delivery.
            shutil.rmtree(where, ignore_errors=True)
            raise CloneFailed(repo, f"clone exited {done.returncode}: {done.stderr.strip()[:160]}")
    done = subprocess.run(
        [
            "git",
            "-C",
            str(where),
            "fetch",
            "--prune",
            "origin",
            "+refs/heads/*:refs/remotes/origin/*",
            *refspecs(
                None if pull_refs is None else present(where, pull_refs, fetch_timeout_s, env)
            ),
        ],
        capture_output=True,
        text=True,
        timeout=fetch_timeout_s,
        env=env,
    )
    if done.returncode != 0:
        # NOT a fallback to the stale clone. See the module docstring.
        # **THE TAIL, NOT THE HEAD.** git writes "From <url>" first and the real failure
        # last, so the leading characters are reliably the part that says nothing.
        tail = done.stderr.strip()[-300:]
        raise CloneFailed(repo, f"fetch exited {done.returncode}: ...{tail}")
    return where


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
