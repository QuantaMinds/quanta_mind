"""Resolving the commit a PR landed on — amendment A2.

WHAT: Turns a merge commit into the trunk state immediately before the PR, across
      all three of GitHub's merge strategies.
WHY:  The exposure variable is defined at the parent commit, so this decides what
      every measurement is taken against.

      NOT `base.sha`. That is the commit the PR was *opened* against, which for a
      long-lived PR can be weeks stale, and exposure would then be classified
      against a repository state that never immediately preceded the change. What
      the study needs is the state the change LANDED on, because that is the code
      that then broke.

      `merge_commit_sha^1` gives that for merge commits and squashes but NOT for
      rebases: GitHub replays each commit onto the base individually, with new
      SHAs and no merge commit, so for a PR of N>1 commits the first parent is the
      PR's own second-to-last commit.

      Detection is by DIFF COVERAGE, not by commit message. A squash commit's
      message is the PR title and body and matches no individual PR commit
      message, so a message-matching rule would silently reject every squashed
      multi-commit PR — the most common case on GitHub.
IMPORTS: GitPython. phase0.github_pulls for the merge metadata.
CONSUMED BY: extract_prs.py; tests/test_parent_commit.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from git import Commit, Repo
from git.exc import GitError


class MergeShape(Enum):
    """How the PR reached trunk. Decides which rule applies."""

    MERGE_COMMIT = "merge_commit"
    SQUASH = "squash"
    REBASE = "rebase"
    AMBIGUOUS = "ambiguous"  # excluded, and counted as corpus attrition


@dataclass(frozen=True, slots=True)
class ParentResolution:
    """The parent commit, and how it was decided."""

    shape: MergeShape
    parent_sha: str
    steps_walked: int = 0
    reason: str = ""

    @property
    def is_resolved(self) -> bool:
        return self.shape is not MergeShape.AMBIGUOUS and bool(self.parent_sha)


def _files_of(commit: Commit) -> set[str]:
    try:
        return {str(name) for name in commit.stats.files}
    except (GitError, ValueError):
        return set()


def resolve(
    repo_path: Path,
    merge_commit_sha: str,
    pr_files: frozenset[str],
    pr_commit_count: int,
) -> ParentResolution:
    """Apply A2's decision table to one merged PR.

    Returns AMBIGUOUS rather than guessing. An unresolvable parent is corpus
    attrition, reported alongside clone failures, because classifying against the
    wrong commit is worse than classifying nothing.
    """
    try:
        repo = Repo(repo_path)
        merge = repo.commit(merge_commit_sha)
        # GitPython resolves a Commit lazily: repo.commit() returns an object and
        # only raises on first attribute access. Touching parents HERE keeps the
        # failure inside this handler. A commit deleted or rewritten since the
        # 2025-08 snapshot is corpus attrition, and attrition must not crash a run.
        parents = merge.parents
    except (GitError, ValueError) as exc:
        return ParentResolution(MergeShape.AMBIGUOUS, "", reason=f"commit unavailable: {exc}")

    if not parents:
        return ParentResolution(MergeShape.AMBIGUOUS, "", reason="root commit has no parent")

    # 1. A true merge commit. Unambiguous: the first parent is trunk.
    if len(parents) >= 2:
        return ParentResolution(MergeShape.MERGE_COMMIT, parents[0].hexsha, steps_walked=1)

    # 2 and 3 both have one parent; diff coverage tells them apart.
    covered = _files_of(merge)
    if not pr_files or covered >= pr_files:
        return ParentResolution(
            MergeShape.SQUASH,
            parents[0].hexsha,
            steps_walked=1,
            reason="single commit covers the PR's whole file set",
        )

    # 3. Rebase: walk back over the replayed commits.
    current = merge
    steps = 0
    limit = max(pr_commit_count, 1)
    while steps < limit:
        if not current.parents:
            return ParentResolution(MergeShape.AMBIGUOUS, "", steps, "ran out of history")
        touched = _files_of(current)
        if not touched or not touched <= pr_files:
            break
        current = current.parents[0]
        steps += 1

    if steps == 0:
        return ParentResolution(
            MergeShape.AMBIGUOUS,
            "",
            0,
            "merge commit touches files outside the PR: neither squash nor rebase",
        )
    if steps >= limit and current.parents and _files_of(current) <= pr_files:
        return ParentResolution(
            MergeShape.AMBIGUOUS, "", steps, f"walk exceeded the PR's {limit} commits"
        )

    return ParentResolution(
        MergeShape.REBASE, current.hexsha, steps, "walked back replayed commits"
    )
