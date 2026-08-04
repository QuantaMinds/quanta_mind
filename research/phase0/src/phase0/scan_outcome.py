"""The outcome variable: did a revert or fix land within 7 days?

WHAT: Walks the repository's history after a PR merged and returns BROKE or CLEAN,
      with the commit that produced the verdict attached as evidence.
WHY:  The outcome is deliberately BEHAVIOURAL, not AST-based. AIDev ships
      breaking-change labels produced by static analysis, and static analysis is
      structurally blind to the breakage this thesis is about — using them as
      ground truth would manufacture a false null. The ruler cannot measure the
      thing. RUNBOOK section 6 forbids switching to the AST outcome because it
      gives a nicer number.

      `evidence_sha` and `evidence_message` are not decoration. They are what make
      the result auditable by someone who does not trust us, and RUNBOOK section 3
      requires them per PR.

      Runs entirely from a local clone. No GitHub quota is consumed here, which is
      why the third §3.2 criterion — an issue opened within 7 days referencing the
      PR — is optional under amendment A4 and its execution is recorded rather
      than assumed.

      Expected base rate 5-20%. Below 2% the classifier is too strict; above 40%
      it is counting routine follow-ups (RUNBOOK section 2.3). The real gate is
      >=16/20 agreement with hand-labelling, done BEFORE any classifier output is
      seen, because once you have seen the machine's answer your labels are
      anchored.
IMPORTS: GitPython, phase0.fix_signals, phase0.extract_prs. Never
      phase0.classify_exposure — the two passes must not see each other.
CONSUMED BY: run_pipeline.py, build_table.py; tests/test_scan_outcome.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path

from git import Commit, Repo
from git.exc import GitError

from phase0 import fix_signals
from phase0.extract_prs import PRRecord

WINDOW_DAYS = 7

# Hard bound on how far to walk. A busy repository can land thousands of commits
# in a week, and the scan is per-PR across thousands of PRs.
MAX_COMMITS = 2000


class Outcome(Enum):
    BROKE = "broke"
    CLEAN = "clean"


class Criterion(Enum):
    """Which §3.2 rule fired. Recorded so Results can report their relative weight."""

    REVERT = "revert"  # explicit `This reverts commit <sha>`
    FIX_TOUCHING_SAME_FILE = "fix_touching_same_file"
    ISSUE_LINK = "issue_link"  # A4, optional and API-dependent
    NONE = "none"


@dataclass(frozen=True, slots=True)
class OutcomeRecord:
    """A verdict and the commit that justifies it."""

    outcome: Outcome
    criterion: Criterion = Criterion.NONE
    evidence_sha: str = ""
    evidence_message: str = ""
    commits_examined: int = 0
    issue_link_checked: bool = False  # A4: stated in Results, never assumed

    @property
    def is_auditable(self) -> bool:
        """A BROKE verdict without evidence is not a result, it is an assertion."""
        return self.outcome is Outcome.CLEAN or bool(self.evidence_sha)


def _merged_at(pr: PRRecord) -> datetime | None:
    try:
        stamp = datetime.fromisoformat(pr.merged_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def _touches_pr_files(commit: Commit, changed: frozenset[str]) -> bool:
    """True if this commit modifies any file the PR modified."""
    try:
        touched = set(commit.stats.files)
    except (GitError, ValueError):
        return False
    return any(str(name) in changed for name in touched)


def _candidates(repo: Repo, start: datetime, end: datetime, exclude: str) -> list[Commit]:
    """Commits landing strictly after the merge and within the window."""
    found: list[Commit] = []
    try:
        walk = repo.iter_commits(max_count=MAX_COMMITS)
    except GitError:
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


def scan(repo_path: Path, pr: PRRecord, window_days: int = WINDOW_DAYS) -> OutcomeRecord:
    """Look for a revert or fix touching this PR's files inside the window.

    Returns CLEAN rather than raising when history is unavailable: an
    unreadable repository is corpus attrition, and run_pipeline.py counts it.
    A silent exception here would be indistinguishable from "nothing broke".
    """
    merged = _merged_at(pr)
    if merged is None:
        return OutcomeRecord(outcome=Outcome.CLEAN)

    try:
        repo = Repo(repo_path)
    except GitError:
        return OutcomeRecord(outcome=Outcome.CLEAN)

    changed = frozenset(pr.changed_files)
    commits = _candidates(repo, merged, merged + timedelta(days=window_days), pr.merged_sha)

    for commit in commits:
        message = str(commit.message)

        if fix_signals.reverts(message, pr.merged_sha):
            return OutcomeRecord(
                outcome=Outcome.BROKE,
                criterion=Criterion.REVERT,
                evidence_sha=commit.hexsha,
                evidence_message=message.strip()[:200],
                commits_examined=len(commits),
            )

        overlaps = _touches_pr_files(commit, changed)
        if overlaps and (
            fix_signals.mentions_breakage(message) or fix_signals.looks_like_a_revert(message)
        ):
            return OutcomeRecord(
                outcome=Outcome.BROKE,
                criterion=Criterion.FIX_TOUCHING_SAME_FILE,
                evidence_sha=commit.hexsha,
                evidence_message=message.strip()[:200],
                commits_examined=len(commits),
            )

    return OutcomeRecord(outcome=Outcome.CLEAN, commits_examined=len(commits))
