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

from dataclasses import dataclass
from pathlib import Path

from phase0.extract_prs import PRRecord
from phase0.github_pulls import MergeInfo
from phase0.parent_commit import resolve
from phase0.pipeline.changed import (
    changed_python_files,
    file_agreement,
    module_name,
    source_at,
    symbols_touched,
    touched_line_ranges,
)

# Share of the union the two file sets must share. Set from A24's measurement: the
# median PR has four files and agrees, while the long tail disagrees by an order of
# magnitude. Anything short of near-identity is a divergent base, not a rounding error.
MIN_FILE_AGREEMENT = 0.6


# Why a PR left the corpus, at the level that decides how it is analysed. The three are
# different claims and must not be pooled into one attrition number.
#
#   resource   -- the unit exists, we could not obtain it. Missing data.
#   integrity  -- obtained, but the corpus's account of it cannot be trusted. Missing
#                 data, and the reason correlates with patch size, so A17's bounds
#                 must cover it rather than treat it as noise.
#   restricted -- nothing to measure. Not missing data: the estimand does not cover
#                 this unit, which narrows the claim rather than biasing it.
CATEGORIES: dict[str, str] = {
    # A repository we could not clone must produce a record per PR, not the absence of
    # one. Absent rows shrink the denominator, so the same corpus scanned twice gave 33
    # records once and 34 the next -- a 3% swing at that size, larger than several
    # effects the study needs to tell apart, and nothing reported it.
    "clone_failed": "resource",
    "merge_metadata": "resource",
    "parent_commit": "integrity",
    "file_set": "integrity",
    "no_python": "restricted",
    "no_symbols": "restricted",
}


@dataclass(frozen=True, slots=True)
class Rejection:
    """Why a PR did not become a record. Counted, never silently dropped."""

    pr_id: str
    stage: str
    reason: str
    agreement: float = -1.0

    @property
    def category(self) -> str:
        """`resource`, `integrity` or `restricted` -- see CATEGORIES."""
        return CATEGORIES.get(self.stage, "resource")


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
    if not merge.is_usable:
        return Rejection(pr_id, "merge_metadata", "unmerged, or no merge commit recorded")

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
    authority = merge.api_files or corpus_files
    source = "github" if merge.api_files else "corpus"
    corpus_py = frozenset(f for f in authority if f.endswith(".py"))
    agreement = file_agreement(corpus_py, frozenset(derived))
    if agreement < MIN_FILE_AGREEMENT:
        return Rejection(
            pr_id,
            "file_set",
            f"{source} lists {len(corpus_py)} .py files, the diff shows {len(derived)}; "
            f"agreement {agreement:.2f} < {MIN_FILE_AGREEMENT}. Analysing this PR would "
            f"scan a file set the change never touched.",
            agreement,
        )

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
    )
