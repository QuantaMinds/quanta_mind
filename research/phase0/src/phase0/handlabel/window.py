"""The seven days after a merge — the evidence, and whether we could read it.

WHAT: Walks a clone's history for commits landing inside the window after a selected
      PR merged, excluding the PR's own commits, and returns them together with a typed
      statement of whether the history was readable at all.
WHY:  Split from `sheet.py` because walking git history and rendering markdown are two
      concerns, and because the distinction this module exists to preserve is not a
      rendering detail.

      The first version returned a bare list, so a repository that failed to clone and a
      genuinely quiet week were the same empty list. Then thirteen of thirteen clones
      failed — GitPython's `kill_after_timeout` is unsupported on Windows — and the sheet
      rendered twenty PRs as having no activity. A labeller would have marked twenty
      clean; the classifier returns CLEAN on unreadable history for its own reasons; the
      gate would have reported 20/20 PASS on zero data. That is AGENTS.md rule 3 broken
      inside the package whose purpose is to keep the gate honest.

      Like `sheet.py`, this module must not import `scan_outcome` or `fix_signals`. The
      window bound is restated rather than imported for that reason and pinned by test.
IMPORTS: GitPython, phase0.handlabel.select.
CONSUMED BY: sheet.py, scripts/make_handlabel_sheet.py; tests/test_handlabel.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from git import Repo

# Via git.exc, not gitdb.exc: gitdb ships no py.typed marker. parent_commit.py:34 does
# the same, and pins why BadName/BadObject need ODBError rather than GitError.
from git.exc import GitError, ODBError

from phase0.handlabel.select import Candidate

# Must equal scan_outcome.WINDOW_DAYS. Pinned by test_handlabel.py rather than imported,
# because importing scan_outcome here is exactly what this package must not do.
WINDOW_DAYS = 7
MAX_COMMITS = 4000
GIT_LOOKUP_ERRORS = (GitError, ODBError, ValueError)


@dataclass(frozen=True, slots=True)
class WindowCommit:
    """One commit inside the window, as the labeller sees it."""

    sha: str
    when: str
    author: str
    message: str
    touched_pr_files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Window:
    """Commits in the window, or a typed statement that we could not look."""

    commits: tuple[WindowCommit, ...] = ()
    available: bool = True
    reason: str = ""

    @property
    def is_labellable(self) -> bool:
        """A PR whose history we could not read must not be labelled or scored."""
        return self.available


def unavailable(reason: str) -> Window:
    """Constructor for the failure case, so callers cannot express it as an empty list."""
    return Window(commits=(), available=False, reason=reason)


def _merged_at(candidate: Candidate) -> datetime | None:
    try:
        stamp = datetime.fromisoformat(candidate.merged_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def window_commits(repo_path: Path, candidate: Candidate) -> Window:
    """Commits landing in the window after the merge, oldest first.

    Commits belonging to the PR itself are excluded, matching the scanner: a PR cannot
    be its own fix. Every failure path returns `unavailable(...)` with a reason, never
    an empty window.
    """
    start = _merged_at(candidate)
    if start is None:
        return unavailable(f"unparseable merged_at: {candidate.merged_at!r}")
    end = start + timedelta(days=WINDOW_DAYS)
    own = {sha[:7] for sha in candidate.commit_shas}
    changed = set(candidate.changed_files)

    try:
        repo = Repo(repo_path)
        walk = list(repo.iter_commits(max_count=MAX_COMMITS))
    except GIT_LOOKUP_ERRORS as exc:
        return unavailable(f"history unreadable at {repo_path}: {exc}")

    found: list[WindowCommit] = []
    for commit in walk:
        when = commit.committed_datetime
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        if when > end:
            continue
        if when <= start:
            break  # newest-first; everything below is out of window
        if commit.hexsha[:7] in own:
            continue
        try:
            touched = tuple(sorted(set(map(str, commit.stats.files)) & changed))
        except GIT_LOOKUP_ERRORS:
            touched = ()
        found.append(
            WindowCommit(
                sha=commit.hexsha,
                when=when.isoformat(),
                author=str(commit.author),
                message=str(commit.message).strip(),
                touched_pr_files=touched,
            )
        )
    return Window(commits=tuple(reversed(found)), available=True)
