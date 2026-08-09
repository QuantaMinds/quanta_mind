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
IMPORTS: GitPython, phase0.extract_prs, and its siblings phase0.outcome.{signals,
      conclusion,window}. Never phase0.classify_exposure — the two passes must not see
      each other.
CONSUMED BY: run_pipeline.py, analysis/build_table.py, controls/gate.py,
      handlabel/draw.py; tests/outcome/test_scan.py.
"""

from __future__ import annotations

from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from git import Commit, Repo
from git.exc import GitError, ODBError

from phase0.extract_prs import PRRecord
from phase0.outcome import signals
from phase0.outcome.arrival import resolve_deleted_base
from phase0.outcome.conclusion import Criterion, Outcome, OutcomeRecord
from phase0.outcome.window import (
    Exclusion,
    WindowUnreadable,
    base_ref_of,
    candidates,
    reachable,
)

# See parent_commit.py: BadName/BadObject derive from gitdb's ODBError, which is
# neither a GitError nor a ValueError, so a narrower catch lets them escape.
GIT_LOOKUP_ERRORS = (GitError, ODBError, ValueError)

WINDOW_DAYS = 7

# There is deliberately no commit-count bound here. This module used to declare a
# second `MAX_COMMITS = 2000` that nothing read -- `window.py` held the live one -- so
# the constant that looked authoritative, in the file where the walk appears to happen,
# could be edited with no effect and no failing test. The bound is a DATE and it lives
# with the walk. See `window.py` for what the count cap cost.


def _merged_at(pr: PRRecord) -> datetime | None:
    try:
        stamp = datetime.fromisoformat(pr.merged_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def _touches_pr_files(commit: Commit, changed: frozenset[str]) -> bool:
    """True if this commit is substantially about the files the PR modified.

    The git extraction lives here; the rule lives in `signals.is_focused`.
    """
    try:
        touched = frozenset(str(name) for name in commit.stats.files)
    except GIT_LOOKUP_ERRORS:
        return False
    return signals.is_focused(touched, changed)


def scan(repo_path: Path, pr: PRRecord, window_days: int = WINDOW_DAYS) -> OutcomeRecord:
    """Look for a revert or fix touching this PR's files inside the window.

    Returns UNSCANNABLE, never CLEAN, when the history cannot be read. The two were the
    same value until 15.5% of the corpus turned out to merge off the default branch,
    which the walk never visited.
    """
    merged = _merged_at(pr)
    if merged is None:
        return OutcomeRecord(
            Outcome.UNSCANNABLE,
            evidence_message="unparseable merged_at",
            exclusion=Exclusion.UNPARSEABLE_MERGED_AT,
        )

    repo = None
    try:
        repo = Repo(repo_path)
    except GIT_LOOKUP_ERRORS as exc:
        return OutcomeRecord(
            Outcome.UNSCANNABLE,
            evidence_message=f"unreadable clone: {exc}",
            exclusion=Exclusion.UNREADABLE_CLONE,
        )

    # `closing` rather than a finally: the scan has several early returns and each
    # one must release the handle. Windows keeps pack files mapped while a Repo is
    # open, so a missed close means the clone cannot be deleted afterwards.
    with closing(repo):
        ref = base_ref_of(repo, pr.base_ref)
        if ref is None:
            # The branch was deleted, which is ordinary hygiene for a `feature/x` base.
            # Never defaulted to HEAD -- that fallback is the original bug. The default
            # branch is substituted ONLY when the merge demonstrably arrived there inside
            # this PR's own window; otherwise the reason is counted and the PR excluded.
            substitute, why = resolve_deleted_base(
                repo_path, pr.merged_sha, merged, merged + timedelta(days=window_days)
            )
            if substitute is None:
                return OutcomeRecord(
                    Outcome.UNSCANNABLE,
                    evidence_message=f"base branch {pr.base_ref!r} no longer exists",
                    exclusion=Exclusion(why),
                )
            ref = substitute
        if pr.merged_sha and not reachable(repo, pr.merged_sha, ref):
            # A separate category from a missing branch, because it is a different fact
            # about the repository. agentops#811, #817, #818 and #819 merged into `dev`
            # and their merge commits are not ancestors of it -- force-push, branch
            # recreation, or an indirect merge. The branch exists and the merge is not on
            # it, so the window cannot be walked and guessing another branch would be
            # inventing the answer.
            return OutcomeRecord(
                Outcome.UNSCANNABLE,
                evidence_message=f"merge commit is not reachable from {ref}",
                exclusion=Exclusion.MERGE_UNREACHABLE,
            )
        changed = frozenset(pr.changed_files)
        try:
            commits = candidates(
                repo, merged, merged + timedelta(days=window_days), pr.merged_sha, ref
            )
        except WindowUnreadable as exc:
            # UNSCANNABLE, never CLEAN. A walk that could not run says nothing about
            # whether this PR broke anything, and CLEAN would claim it did not.
            return OutcomeRecord(
                Outcome.UNSCANNABLE,
                evidence_message=str(exc)[:200],
                exclusion=Exclusion.WINDOW_UNREADABLE,
            )

        for commit in commits:
            message = str(commit.message)

            if signals.reverts(message, pr.merged_sha):
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
                signals.mentions_breakage(signals.subject(message))
                or signals.looks_like_a_revert(message)
            ):
                return OutcomeRecord(
                    outcome=Outcome.BROKE,
                    criterion=Criterion.FIX_TOUCHING_SAME_FILE,
                    evidence_sha=commit.hexsha,
                    evidence_message=message.strip()[:200],
                    commits_examined=len(commits),
                )

        return OutcomeRecord(outcome=Outcome.CLEAN, commits_examined=len(commits))
