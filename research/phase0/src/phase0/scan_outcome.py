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
      why the third `PHASE0_PREREGISTRATION.md` “Outcome variable” criterion — an issue opened
      within 7 days referencing the
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

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path

from git import Commit, Repo
from git.exc import GitError, ODBError

from phase0 import fix_signals
from phase0.extract_prs import PRRecord
from phase0.outcome_window import base_ref_of, candidates, reachable

# See parent_commit.py: BadName/BadObject derive from gitdb's ODBError, which is
# neither a GitError nor a ValueError, so a narrower catch lets them escape.
GIT_LOOKUP_ERRORS = (GitError, ODBError, ValueError)

WINDOW_DAYS = 7

# Hard bound on how far to walk. A busy repository can land thousands of commits
# in a week, and the scan is per-PR across thousands of PRs.
MAX_COMMITS = 2000


class Outcome(Enum):
    BROKE = "broke"
    CLEAN = "clean"
    # We could not look. Distinct from CLEAN on purpose: the scan used to walk from the
    # clone's HEAD, so a PR merged into `dev` or a feature branch had its whole
    # post-merge history outside that walk and came back CLEAN. 15.5% of the corpus
    # merges off the default branch, and those repositories are the ones with a release
    # process -- so the instrument was systematically scoring the more process-mature
    # projects as unbroken. A false negative leaves no trace anywhere; an UNSCANNABLE
    # verdict is an exclusion somebody has to count.
    UNSCANNABLE = "unscannable"


class Criterion(Enum):
    """Which `PHASE0_PREREGISTRATION.md` “Outcome variable” rule fired. Recorded so Results can
    report
    their relative weight.
    """

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
    """True if this commit is substantially about the files the PR modified.

    The git extraction lives here; the rule lives in `fix_signals.is_focused`.
    """
    try:
        touched = frozenset(str(name) for name in commit.stats.files)
    except GIT_LOOKUP_ERRORS:
        return False
    return fix_signals.is_focused(touched, changed)


def scan(repo_path: Path, pr: PRRecord, window_days: int = WINDOW_DAYS) -> OutcomeRecord:
    """Look for a revert or fix touching this PR's files inside the window.

    Returns UNSCANNABLE, never CLEAN, when the history cannot be read. The two were the
    same value until 15.5% of the corpus turned out to merge off the default branch,
    which the walk never visited.
    """
    merged = _merged_at(pr)
    if merged is None:
        return OutcomeRecord(Outcome.UNSCANNABLE, evidence_message="unparseable merged_at")

    repo = None
    try:
        repo = Repo(repo_path)
    except GIT_LOOKUP_ERRORS as exc:
        return OutcomeRecord(Outcome.UNSCANNABLE, evidence_message=f"unreadable clone: {exc}")

    # `closing` rather than a finally: the scan has several early returns and each
    # one must release the handle. Windows keeps pack files mapped while a Repo is
    # open, so a missed close means the clone cannot be deleted afterwards.
    with closing(repo):
        ref = base_ref_of(repo, pr.base_ref)
        if ref is None:
            return OutcomeRecord(
                Outcome.UNSCANNABLE,
                evidence_message=f"base branch {pr.base_ref!r} no longer exists",
            )
        if pr.merged_sha and not reachable(repo, pr.merged_sha, ref):
            # agentops#811 and #817 merged into `dev` and their merge commits have no
            # common ancestor with it -- force-push, branch recreation, or an indirect
            # merge. Whatever the cause, the window cannot be walked from a branch the
            # merge is not on, and guessing another would be inventing the answer.
            return OutcomeRecord(
                Outcome.UNSCANNABLE,
                evidence_message=f"merge commit is not reachable from {ref}",
            )
        changed = frozenset(pr.changed_files)
        commits = candidates(repo, merged, merged + timedelta(days=window_days), pr.merged_sha, ref)

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
                # SUBJECT only. A squash merge concatenates every constituent commit
                # message into the body, so any feature branch containing one commit
                # that said "fix:" produced a body matching the pattern -- which made
                # the rule fire on large feature PRs as a class. `looks_like_a_revert`
                # keeps the whole message: `git revert` writes its marker in the body.
                fix_signals.mentions_breakage(fix_signals.subject(message))
                or fix_signals.looks_like_a_revert(message)
            ):
                return OutcomeRecord(
                    outcome=Outcome.BROKE,
                    criterion=Criterion.FIX_TOUCHING_SAME_FILE,
                    evidence_sha=commit.hexsha,
                    evidence_message=message.strip()[:200],
                    commits_examined=len(commits),
                )

        return OutcomeRecord(outcome=Outcome.CLEAN, commits_examined=len(commits))
