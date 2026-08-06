"""A file-set shortfall is the repository's business, and gets a label, not a raise.

WHAT: Pins that deriving fewer `.py` files than GitHub lists produces a `file_set`
      rejection, that the corpus is never the denominator, and that a superset is
      handled the same way.
WHY:  An assertion used to raise `HarnessError` here. Its reasoning was that a shortfall
      could only mean file contents had failed to arrive — true under
      `--filter=blob:none`, where a diff over blobs that never fetched is EMPTY rather
      than wrong, and where `build_record` returned `no_python` from that emptiness
      before `verify_files` ever compared the lists.

      A31 abandoned that clone strategy and `guard:check_no_partial_clone` now rejects
      it, so the premise is gone. Left in place the assertion did the INVERSE harm: on
      the first full-clone run it fired on BerriAI/litellm#2313919432 — derived 2 of 4 —
      and halted the walk. The canonical pre-blobless journal rejects that same PR as
      `file_set/integrity`, a legitimate exclusion. A corpus fact had become a harness
      error, which is the bug it was written to prevent, arriving from the other side.

      The lesson kept from it: a check whose claim is true only under one configuration
      must be removed when that configuration goes, not left to assert something it can
      no longer know. `verify_files` compares the two lists and labels the disagreement;
      nothing claims to know the cause.

      The corpus-denominator test survives unchanged. The corpus over-attributes by
      design (A28: 92 files on three-file PRs), so gating on it would misfire on a KNOWN
      defect.
IMPORTS: phase0.github_pulls, phase0.pipeline.assemble, phase0.pipeline.rejection.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

from phase0.github_pulls import MergeInfo
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


def test_a_shortfall_is_labelled_file_set_and_does_not_halt_the_run(
    repo: tuple[Path, str, str],
) -> None:
    """GitHub names four `.py` files, the diff produced two. That is an exclusion.

    The regression test for a run that died at repository six of ninety. Under the old
    assertion this raised; the canonical full-clone journal shows the correct outcome is
    `file_set/integrity`, and a walk that halts on a legitimate exclusion measures
    nothing.
    """
    root, _, child = repo
    merge = _merge(child, ("pkg/mod.py", "pkg/a.py", "pkg/b.py", "pkg/c.py"))

    outcome = build_record(
        root,
        merge,
        pr_id="9",
        repo="acme/widget",
        merged_at=merge.merged_at,
        corpus_files=("pkg/mod.py",),
    )

    assert isinstance(outcome, Rejection)
    assert outcome.stage == "file_set"


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
