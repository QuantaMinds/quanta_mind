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

      Detection tries the SUBJECT SEQUENCE first and falls back to diff coverage
      only when the API gave us no subjects — see `pipeline/merge_shape.by_subject`.
      This docstring previously argued the opposite, that detection is by diff
      coverage and "a message-matching rule would silently reject every squashed
      multi-commit PR". That objection defeats matching a SINGLE message, which is
      why the rule matches a sequence of at least two: a squash produces exactly
      one commit and can never yield two consecutive subjects in order, whatever
      the repository's message setting.

      The correction matters beyond tidiness. The file rules compare against a file
      list the corpus supplies, and the corpus attributes 92 files to some
      three-file PRs, so they failed on exactly the PRs whose file lists were
      wrong — `parent_commit` became the largest exclusion at 17-70% across
      commit-count bands, differentially on patch size, which is the study's own
      confounder. A docstring asserting the corpus-dependent rule was the
      authoritative one is how that dependence stayed invisible.
IMPORTS: GitPython. phase0.pipeline.merge_shape for the corpus-free rule.
CONSUMED BY: pipeline/assemble.py, run_pipeline.py; tests/test_parent_commit.py.
"""

from __future__ import annotations

from pathlib import Path

from git import Commit, Repo
from git.exc import GitError, ODBError

from phase0.pipeline.merge_shape import (
    MergeShape,
    ParentResolution,
    ResolutionRule,
    by_subject,
)

# GitPython raises across two unrelated hierarchies. GitError covers command
# failures; BadName and BadObject derive from gitdb's ODBError, which is NOT a
# GitError and NOT a ValueError. Catching only the first two lets a malformed ref
# escape -- and merge_commit_sha arrives from an API payload, so malformed is a
# realistic input rather than a hypothetical one.
GIT_LOOKUP_ERRORS = (GitError, ODBError, ValueError)


def _files_of(commit: Commit) -> set[str]:
    try:
        return {str(name) for name in commit.stats.files}
    except GIT_LOOKUP_ERRORS:
        return set()


def resolve(
    repo_path: Path,
    merge_commit_sha: str,
    pr_files: frozenset[str],
    pr_commit_count: int,
    pr_commit_subjects: tuple[str, ...] = (),
) -> ParentResolution:
    """Apply A2's decision table to one merged PR.

    Returns AMBIGUOUS rather than guessing. An unresolvable parent is corpus
    attrition, reported alongside clone failures, because classifying against the
    wrong commit is worse than classifying nothing.
    """
    repo = None
    try:
        repo = Repo(repo_path)
        merge = repo.commit(merge_commit_sha)
        # GitPython resolves a Commit lazily: repo.commit() returns an object and
        # only raises on first attribute access. Touching parents HERE keeps the
        # failure inside this handler. A commit deleted or rewritten since the
        # 2025-08 snapshot is corpus attrition, and attrition must not crash a run.
        parents = merge.parents
    except GIT_LOOKUP_ERRORS as exc:
        return ParentResolution(
            MergeShape.AMBIGUOUS,
            "",
            reason=f"commit unavailable: {exc}",
            rule=ResolutionRule.UNRESOLVED,
        )
    finally:
        # Windows keeps the pack files mapped while a Repo is open, so the clone cannot
        # be deleted afterwards and 1.6 GB accumulated over 41 repositories. Closing is
        # a no-op on POSIX and the difference between finishing and filling the disk on
        # Windows -- at hour thirty of a multi-day run, which is when it would show up.
        if repo is not None:
            repo.close()

    if not parents:
        return ParentResolution(
            MergeShape.AMBIGUOUS,
            "",
            reason="root commit has no parent",
            rule=ResolutionRule.UNRESOLVED,
        )

    # 1. A true merge commit. Unambiguous: the first parent is trunk.
    if len(parents) >= 2:
        return ParentResolution(
            MergeShape.MERGE_COMMIT,
            parents[0].hexsha,
            steps_walked=1,
            rule=ResolutionRule.MERGE_PARENTS,
        )

    # 2. Subjects when we have them: authoritative, and independent of the corpus file
    #    list that the file rules below depend on.
    from_subjects = by_subject(merge, pr_commit_subjects, max(pr_commit_count, 1))
    if from_subjects is not None:
        return from_subjects

    # 3 and 4 both have one parent; diff coverage tells them apart.
    # A46: these are TWO claims, not one, and only the second is a measurement.
    # `covered >= pr_files` tested a list we have; `not pr_files` returns SQUASH with
    # nothing to test against at all. They are recorded under different rules so the
    # next reader can count them apart -- the collapse non-negotiable 3 forbids is
    # exactly what one shared verdict here would be.
    covered = _files_of(merge)
    if not pr_files:
        return ParentResolution(
            MergeShape.SQUASH,
            parents[0].hexsha,
            steps_walked=1,
            reason="no file list to test against; assumed squash",
            rule=ResolutionRule.NO_FILE_LIST,
        )
    if covered >= pr_files:
        return ParentResolution(
            MergeShape.SQUASH,
            parents[0].hexsha,
            steps_walked=1,
            reason="single commit covers the PR's whole file set",
            rule=ResolutionRule.FILE_COVERAGE,
        )

    # 3. Rebase: walk back over the replayed commits.
    current = merge
    steps = 0
    limit = max(pr_commit_count, 1)
    while steps < limit:
        if not current.parents:
            return ParentResolution(
                MergeShape.AMBIGUOUS,
                "",
                steps,
                "ran out of history",
                rule=ResolutionRule.FILE_COVERAGE,
            )
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
            rule=ResolutionRule.FILE_COVERAGE,
        )
    if steps >= limit and current.parents and _files_of(current) <= pr_files:
        return ParentResolution(
            MergeShape.AMBIGUOUS,
            "",
            steps,
            f"walk exceeded the PR's {limit} commits",
            rule=ResolutionRule.FILE_COVERAGE,
        )

    return ParentResolution(
        MergeShape.REBASE,
        current.hexsha,
        steps,
        "walked back replayed commits",
        rule=ResolutionRule.FILE_COVERAGE,
    )
