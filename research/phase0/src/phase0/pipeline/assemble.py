"""Corpus rows to `PRRecord`, with the file-set gate that A24 made blocking.

WHAT: Given a clone and one candidate PR, resolves the parent, re-derives the changed
      files and symbols from the tree, and refuses the PR when that disagrees with the
      corpus's own file list.
WHY:  Nothing built a `PRRecord` before this. Merge metadata, parent resolution and the
      measurement all existed, with no path from the dataset to the thing they consume.

      The order is forced by a circularity. Parent resolution needs a file list to tell
      a squash from a rebase, but the trustworthy list is `git diff parent..merged`,
      which needs the parent. So the corpus's list is used ONLY as a heuristic input to
      shape detection, the real list is re-derived once the parent is known, and the two
      are compared.

      That comparison is not a diagnostic. A24 measured the corpus attributing 92
      distinct `.py` files to a pull request that changed two, and more than 30 files to
      15.9% of PRs. Left unchecked it makes `scan_outcome` match almost any later
      commit, in proportion to how far the branch had diverged -- and since patch size
      already discriminates at AUC 0.957, that is the study's own confounder arriving
      disguised as measurement error.

      So a PR whose two file sets disagree is excluded and counted, never analysed. An
      excluded PR is a number in the attrition table; an analysed one with the wrong
      file set is a wrong answer nobody can see.
IMPORTS: phase0.{extract_prs,github_pulls,parent_commit}, pipeline.changed.
CONSUMED BY: run_pipeline.py; tests/test_assemble.py.
"""

from __future__ import annotations

from pathlib import Path

from phase0.extract_prs import PRRecord
from phase0.github_pulls import MergeInfo
from phase0.parent_commit import resolve
from phase0.pipeline.changed import (
    changed_python_files,
    module_name,
    source_at,
    symbols_touched,
    touched_line_ranges,
)
from phase0.pipeline.rejection import Rejection
from phase0.pipeline.verify_files import verify_files

# Share of the union the two file sets must share. Set from A24's measurement: the
# median PR has four files and agrees, while the long tail disagrees by an order of
# magnitude. Anything short of near-identity is a divergent base, not a rounding error.


def build_record(
    clone: Path,
    merge: MergeInfo,
    *,
    pr_id: str,
    repo: str,
    merged_at: str,
    corpus_files: tuple[str, ...],
    arm: str = "human",
    task_type: str = "",
    licence: str = "",
) -> PRRecord | Rejection:
    """One corpus row to a record, or a typed reason it cannot become one.

    `merge.commit_count` comes from the API rather than from the length of the corpus
    file list. A24 found the corpus attributing 92 files to a three-commit pull request,
    so a file count standing in for a commit count would mis-detect the merge shape on
    exactly those PRs whose file lists are wrong.
    """
    if not merge.merged:
        return Rejection(pr_id, "merge_metadata", "not merged: no post-merge window exists")
    if not merge.merge_commit_sha:
        # A merged PR with a null merge_commit_sha is a real, reported GitHub state.
        # Named, because falling through would either dereference nothing or land in an
        # unrelated bucket, and "we never had a merge commit" is not the same claim as
        # "we could not resolve its parent".
        return Rejection(pr_id, "no_merge_sha", "merged, but GitHub reports no merge commit")

    parent = resolve(
        clone,
        merge.merge_commit_sha,
        frozenset(corpus_files),
        merge.commit_count,
        merge.commit_subjects,
    )
    if not parent.is_resolved:
        return Rejection(pr_id, "parent_commit", parent.reason)

    derived = changed_python_files(clone, parent.parent_sha, merge.merge_commit_sha)
    if not derived:
        return Rejection(pr_id, "no_python", "no .py files between parent and merge")

    # Verify against GitHub's own file list when we have it, and the corpus's only when
    # we do not. Detection can be a heuristic; verification cannot. The corpus attributes
    # 92 files to some three-file PRs, so a gate built on it was checking the wrong thing
    # against the right diff.
    mismatch = verify_files(pr_id, merge, corpus_files, frozenset(derived))
    if mismatch is not None:
        return mismatch

    symbols: set[str] = set()
    for path in derived:
        ranges = touched_line_ranges(clone, parent.parent_sha, merge.merge_commit_sha, path)
        symbols |= symbols_touched(
            source_at(clone, parent.parent_sha, path), ranges, module_name(path)
        )

    if not symbols:
        # No exposure to measure, rather than an unexposed one. Import edits and
        # module-constant changes can and do break callers, so coding them UNEXPOSED
        # would put real breakage in the unexposed arm -- the same error that
        # manufactured RR 8.0 in the control corpus, arriving from the other side.
        return Rejection(
            pr_id,
            "no_symbols",
            f"{len(derived)} .py file(s) changed but no function body did; there is no "
            f"exposure to measure. The estimand covers function-body changes only.",
        )

    return PRRecord(
        pr_id=pr_id,
        repo=repo,
        language="python",
        parent_sha=parent.parent_sha,
        merged_sha=merge.merge_commit_sha,
        merged_at=merged_at,
        changed_files=derived,
        changed_symbols=tuple(sorted(symbols)),
        arm=arm,
        task_type=task_type,
        licence=licence,
        repo_id=repo,
        base_ref=merge.base_ref,
    )
