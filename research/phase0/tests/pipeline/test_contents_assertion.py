"""A diff that fetched no contents must raise, never take an exclusion label.

WHAT: Pins the shortfall assertion in `assemble.build_record` — that deriving fewer
      `.py` files than GitHub lists raises `HarnessError`, that the corpus is never
      used as the denominator, and that a superset is still the repository's business.
WHY:  This is the bug the assertion exists for, and it shipped once.

      `--filter=blob:none` supplies file CONTENTS only by lazy fetch. A diff over blobs
      that never arrived is EMPTY rather than wrong, and `build_record` returned
      `no_python` from that emptiness before `verify_files` ever compared the two lists.
      On the eight recovered repositories that produced twelve rejections at
      `derived=0` — three of them labelled `no_python` where GitHub lists 104, 65 and 40
      `.py` files — and seventeen of seventeen scored PRs reading CLEAN. A harness
      failure wearing a corpus label, which is the same shape as the `RLIMIT_AS` defect.

      The shortfall case is tested rather than only the zero case on purpose: deriving
      12 of 104 is the same failure at 88% severity, and a zero-check passes it.

      The corpus-denominator test guards the fix against itself. The corpus
      over-attributes by design (A28: 92 files on three-file PRs), so asserting against
      it would raise on a KNOWN defect and the assertion would be turned off again.
IMPORTS: pytest, phase0.github_pulls, phase0.graph.run_graph, phase0.pipeline.assemble.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0.github_pulls import MergeInfo
from phase0.graph.run_graph import HarnessError
from phase0.pipeline.assemble import build_record
from phase0.pipeline.rejection import Rejection


def _merge(sha: str, api_files: tuple[str, ...]) -> MergeInfo:
    return MergeInfo(
        pr_id="9",
        number=9,
        merged=True,
        merge_commit_sha=sha,
        merged_at="2025-06-24T22:46:29Z",
        base_ref="main",
        commit_count=1,
        api_files=api_files,
    )


def test_deriving_fewer_py_files_than_github_lists_raises(repo: tuple[Path, str, str]) -> None:
    """The blobless failure: GitHub names four .py files, the diff produced two."""
    root, _, child = repo
    merge = _merge(child, ("pkg/mod.py", "pkg/a.py", "pkg/b.py", "pkg/c.py"))

    with pytest.raises(HarnessError) as raised:
        build_record(
            root,
            merge,
            pr_id="9",
            repo="acme/widget",
            merged_at=merge.merged_at,
            corpus_files=("pkg/mod.py",),
        )

    # The message must name the mechanism, or the next person reads it as corpus noise.
    assert "did not reach the working tree" in str(raised.value)
    assert "not an exclusion" in str(raised.value)


def test_the_corpus_is_never_the_denominator(repo: tuple[Path, str, str]) -> None:
    """A28's over-attribution must not be able to fire this assertion.

    The corpus names forty `.py` files against a two-file diff, which is the documented
    defect, not a failed fetch. Asserting against it would raise on every such PR and the
    assertion would be disabled — so this pins that the check needs GitHub's list.
    """
    root, _, child = repo
    inflated = tuple(f"pkg/ghost{i}.py" for i in range(40))
    outcome = build_record(
        root,
        _merge(child, api_files=()),  # GitHub's list unavailable
        pr_id="9",
        repo="acme/widget",
        merged_at="2025-06-24T22:46:29Z",
        corpus_files=inflated,
    )
    # A value about the repository, never a raise about us. Shape detection refuses it
    # first -- forty attributed files against a two-file merge is neither squash nor
    # rebase -- which is the correct reading of A28's over-attribution.
    assert isinstance(outcome, Rejection)
    assert outcome.stage == "parent_commit"
    assert "neither squash nor rebase" in outcome.reason


def test_a_superset_still_belongs_to_verify_files(repo: tuple[Path, str, str]) -> None:
    """Deriving MORE than GitHub lists is a fact about the walk, not a failed fetch.

    Guards the direction of the comparison. `!=` instead of `<` would route the
    indirect-merge case here and lose the `file_set` rejection A27 added.
    """
    root, _, child = repo
    outcome = build_record(
        root,
        _merge(child, ("pkg/mod.py",)),  # one file listed; the diff shows two
        pr_id="9",
        repo="acme/widget",
        merged_at="2025-06-24T22:46:29Z",
        corpus_files=("pkg/mod.py",),
    )
    assert getattr(outcome, "stage", "") == "file_set"
