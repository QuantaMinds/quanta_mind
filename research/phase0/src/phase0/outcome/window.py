"""Which commits the outcome scan is allowed to look at, and on which branch.

WHAT: Resolves the branch a PR merged into, checks the merge commit is actually on it,
      and yields the commits inside the window.
WHY:  Split from `scan_outcome.py` because deciding WHERE to look and deciding WHAT
      counts are different jobs, and the first one was silently wrong.

      The scan walked `repo.iter_commits()`, which starts at HEAD. 15.5% of the corpus
      merges into `dev`, `develop` or a feature branch, so for those PRs the merge commit
      and everything after it sat outside the walk and every one came back CLEAN. Those
      repositories are the ones with a release process, so the instrument was
      systematically scoring the more process-mature projects as unbroken -- a false
      negative that left no trace, moved no exclusion count, and would not appear in any
      bound computed over declared exclusions.

      `base_ref_of` returns None rather than falling back to HEAD. A fallback would
      reintroduce the same bug in a narrower band and be harder to find the second time.
IMPORTS: GitPython. Nothing from phase0.
CONSUMED BY: scan_outcome.py; tests/test_scan_outcome.py.
"""

from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from git import Commit, Repo
from git.exc import GitError, ODBError

GIT_LOOKUP_ERRORS = (GitError, ODBError, ValueError)
MAX_COMMITS = 2000


class Exclusion(Enum):
    """Why the window could not be walked.

    Each value is a category somebody counts, not a message somebody reads. The two
    branch cases are deliberately separate: a base branch deleted after merge is
    ordinary repository hygiene, whereas a merge commit that is not an ancestor of the
    branch it merged into is a rewritten history. Folding them together would report one
    rate for two populations and lose the distinction that says which.
    """

    NONE = "none"
    UNPARSEABLE_MERGED_AT = "unparseable_merged_at"
    UNREADABLE_CLONE = "unreadable_clone"
    BASE_REF_MISSING = "base_ref_missing"
    MERGE_UNREACHABLE = "merge_unreachable"


def base_ref_of(repo: Repo, base_ref: str) -> str | None:
    """The remote-tracking ref the PR merged into, or None when it is gone.

    None is never silently replaced by HEAD. A fallback would reintroduce the exact bug
    this function exists to fix, only in a narrower band and harder to see.
    """
    if not base_ref:
        return "HEAD"
    for candidate in (f"origin/{base_ref}", base_ref):
        try:
            repo.commit(candidate)
        except GIT_LOOKUP_ERRORS:
            continue
        return candidate
    return None


def reachable(repo: Repo, sha: str, ref: str) -> bool:
    """Whether `sha` is an ancestor of `ref`. False when either cannot be resolved."""
    try:
        return bool(repo.is_ancestor(repo.commit(sha), repo.commit(ref)))
    except GIT_LOOKUP_ERRORS:
        return False


def merge_on_base(clone: Path, merge_sha: str, base_ref: str) -> str:
    """ "yes" | "no" | "unknown" -- is this merge commit on the branch it merged into?

    Three answers, not two, and the third is the point. `reachable` collapses "not an
    ancestor" and "could not resolve either end" into one False, which is the right shape
    for the scan (both mean the window cannot be walked) and the wrong shape for a
    prevalence count, where "no" is a fact about the repository and "unknown" is a fact
    about us.

    Takes a path and owns the handle, because it is called before the admission gate where
    no Repo is open yet, and because Windows keeps pack files mapped until one is closed --
    a leaked handle here would block the clone's own removal later.
    """
    if not merge_sha or not base_ref:
        return "unknown"
    try:
        repo = Repo(clone)
    except GIT_LOOKUP_ERRORS:
        return "unknown"
    with closing(repo):
        ref = base_ref_of(repo, base_ref)
        if ref is None:
            return "unknown"  # branch gone; that is `base_ref_missing`, counted there
        try:
            return "yes" if repo.is_ancestor(repo.commit(merge_sha), repo.commit(ref)) else "no"
        except GIT_LOOKUP_ERRORS:
            return "unknown"


def candidates(
    repo: Repo, start: datetime, end: datetime, exclude: str, ref: str = "HEAD"
) -> list[Commit]:
    """Commits landing strictly after the merge and within the window, ON `ref`."""
    found: list[Commit] = []
    try:
        walk = repo.iter_commits(ref, max_count=MAX_COMMITS)
    except GIT_LOOKUP_ERRORS:
        return found

    for commit in walk:
        when = commit.committed_datetime
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        if when > end:
            continue
        if when <= start:
            break  # history is newest-first; everything below is out of window
        if exclude and commit.hexsha.startswith(exclude[:7]):
            continue
        found.append(commit)
    return found
