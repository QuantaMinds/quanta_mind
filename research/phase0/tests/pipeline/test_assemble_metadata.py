"""Merge METADATA refusals: a PR that never merged, and one with no merge commit.

WHAT: `build_record` must refuse both before it resolves a parent or reads a file set.
WHY:  Split from `test_assemble.py` at the 200-line cap. That file tests whether a
      FILE SET disagreement is refused; this one tests whether MERGE METADATA is refused
      first. Two concerns, and the order matters: a merged PR with a null
      `merge_commit_sha` is a real GitHub state, and falling through would either
      dereference nothing or land in an unrelated bucket.
IMPORTS: phase0.pipeline.{assemble,rejection}, tests/pipeline/conftest.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0.github_pulls import MergeInfo
from phase0.pipeline.assemble import build_record
from phase0.pipeline.rejection import Rejection

# `build_record` REQUIRES `arm` -- it had a `"human"` default, and six call sites in the
# sibling file omitted it, each silently producing a human-arm record.
PACKAGE = Path(__file__).resolve().parents[2] / "data" / "AIDev_BC_Analyser.zip"

ARM = "agent"


def test_an_unmerged_pr_is_refused_before_anything_else(tmp_path: Path) -> None:
    merge = MergeInfo(
        pr_id="3",
        number=3,
        merged=False,
        merge_commit_sha="",
        merged_at="",
        base_ref="main",
        commit_count=0,
    )
    outcome = build_record(
        tmp_path,
        merge,
        pr_id="3",
        repo="acme/widget",
        merged_at="",
        arm=ARM,
        corpus_files=("pkg/mod.py",),
    )
    assert isinstance(outcome, Rejection) and outcome.stage == "merge_metadata"


@pytest.mark.skipif(not PACKAGE.is_file(), reason="replication package not downloaded")
def test_a_merged_pr_with_no_merge_commit_is_named(tmp_path: Path) -> None:
    """A real GitHub state, and not the same claim as an unresolvable parent."""
    merge = MergeInfo(
        pr_id="5",
        number=5,
        merged=True,
        merge_commit_sha="",
        merged_at="2025-06-24T22:46:29Z",
        base_ref="main",
        commit_count=1,
    )
    outcome = build_record(
        tmp_path,
        merge,
        pr_id="5",
        repo="acme/widget",
        merged_at=merge.merged_at,
        arm=ARM,
        corpus_files=("pkg/mod.py",),
    )
    assert isinstance(outcome, Rejection)
    assert outcome.stage == "no_merge_sha" and outcome.category == "resource"
