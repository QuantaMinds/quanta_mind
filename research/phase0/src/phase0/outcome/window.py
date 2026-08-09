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

      The walk is bounded by DATE, never by a commit count. It was capped at 2000
      commits from the tip, and commits landing AFTER the window end consumed that
      budget, so in a repository that had since landed more than 2000 commits the walk
      was exhausted before reaching the window: `candidates` returned an empty list and
      the PR scored CLEAN having examined nothing. Measured on the human arm, 60 of 191
      scanned PRs were truncated this way and broke at 0.00% against 33.59% for the
      rest. Re-scanned under a date bound, 23 of those 60 were BROKE and the two
      partitions became statistically indistinguishable (Fisher p = 0.52), so the cap
      accounted for the whole gap. A count cap is a selector on repository VELOCITY,
      which tracks size -- the study's own confounder, entering through our command.

      An unreadable walk RAISES rather than returning an empty list, because "no commits
      landed in the window" and "the walk could not run" are different facts and CLEAN
      is only honest about the first.
IMPORTS: GitPython. Nothing from phase0.
CONSUMED BY: outcome/scan.py; tests/outcome/test_scan.py.
"""

from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from git import Commit, Repo
from git.exc import GitError, ODBError

GIT_LOOKUP_ERRORS = (GitError, ODBError, ValueError)

# Git's own date format for --since/--until. Committer date is what the walk filters on
# and what `candidates` re-checks, so the two cannot disagree about which day it is.
_GIT_DATE = "%Y-%m-%dT%H:%M:%S%z"


class WindowUnreadable(Exception):
    """The commit walk could not run. NOT the same as a window containing no commits.

    Returning `[]` for both is what made the count cap invisible: the caller could not
    tell "nothing landed here" from "we never looked", and scored CLEAN either way.
    """


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
    WINDOW_UNREADABLE = "window_unreadable"
    # The base branch is gone, the merge IS in the default branch's history, and it
    # arrived there outside the window. A fact about the DATA: walking the default branch
    # instead would measure a different week from the one this PR lived in.
    BASE_REF_WINDOW_SHIFTED = "base_ref_window_shifted"
    # The base branch is gone and the merge is not in the default branch's history at all.
    # A fact about US, which is why it is not called `unreachable`: a squash-merged feature
    # branch and an abandoned one are INDISTINGUISHABLE here. A squash writes a new commit,
    # so the PR's own merge sha is absent either way, and separating the two would need
    # content matching -- inferring an arrival date from a diff that may have been modified
    # in the squash, introduced independently, or arrived by another path. That is
    # manufactured precision, so the two facts are merged and the name says so.
    BASE_REF_UNRESOLVABLE = "base_ref_unresolvable"


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
    """Commits landing strictly after the merge and within the window, ON `ref`.

    Raises WindowUnreadable when the walk cannot run. An empty list therefore means one
    thing only: the window is genuinely empty.
    """
    found: list[Commit] = []
    try:
        # Git bounds the walk by committer date. No max_count: a count cap consumes its
        # budget on commits after the window and can be exhausted before reaching it,
        # which reads as an empty window rather than as a truncated walk.
        walk = repo.iter_commits(
            ref, since=start.strftime(_GIT_DATE), until=end.strftime(_GIT_DATE)
        )
    except GIT_LOOKUP_ERRORS as exc:
        raise WindowUnreadable(f"cannot walk {ref}: {exc}") from exc

    try:
        for commit in walk:
            when = commit.committed_datetime
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            # Re-checked rather than trusted: --since/--until is inclusive at the start
            # and the window is open there, so the merge's own second must not qualify.
            # `continue`, never `break` -- a break would reintroduce an ordering
            # assumption that the date bound has already made unnecessary.
            if when > end or when <= start:
                continue
            if exclude and commit.hexsha.startswith(exclude[:7]):
                continue
            found.append(commit)
    except GIT_LOOKUP_ERRORS as exc:
        # Mid-walk failure. Half a window is not a window, and the commits already
        # collected would score CLEAN on the strength of the ones never read.
        raise WindowUnreadable(f"walk of {ref} failed after {len(found)} commits: {exc}") from exc
    return found
