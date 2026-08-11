"""Verification that a PR is refused when the corpus's file list is not the change.

WHAT: Pins the file-set gate, and pins that the corpus really does over-attribute on the
      pull request that exposed it.
WHY:  `scan_outcome` matches later commits by file overlap, so an inflated file list
      manufactures breakage in proportion to how far the branch had diverged. That is
      the study's own confounder arriving disguised as measurement error, which is why
      the gate excludes rather than warns.
IMPORTS: pytest, pandas, phase0.github_pulls, phase0.pipeline.assemble.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

from phase0.github_pulls import MergeInfo
from phase0.pipeline.assemble import build_record
from phase0.pipeline.rejection import Rejection
from phase0.pipeline.verify_files import MIN_FILE_AGREEMENT

PACKAGE = Path(__file__).resolve().parents[2] / "data" / "AIDev_BC_Analyser.zip"
ZENML_3757 = 2607442037


# Every call in this file builds an AGENT-arm record. Named once: `build_record` now
# REQUIRES `arm`, and six call sites here omitted it -- each of which produced a silent
# human-arm record under the old `arm: str = "human"` default.
ARM = "agent"


def _merge(sha: str, count: int = 1, api_files: tuple[str, ...] = ()) -> MergeInfo:
    return MergeInfo(
        pr_id="1",
        number=1,
        merged=True,
        merge_commit_sha=sha,
        merged_at="2025-06-24T22:46:29Z",
        base_ref="main",
        commit_count=count,
        api_files=api_files,
    )


def test_a_pr_whose_file_sets_disagree_is_refused(repo: tuple[Path, str, str]) -> None:
    """GitHub names files the diff denies, so the PR is excluded.

    Sized to clear shape detection and fail on the file set, because the two exclusions
    are different findings and a test that cannot tell them apart pins neither.

    The disagreement is now GITHUB's, not the corpus's. This test used to supply the
    inflated list as `corpus_files` and rely on `verify_files` falling back to it -- so it
    was pinning the fallback rather than the gate, and the fallback is gone.
    """
    root, _, child = repo
    listed = ("pkg/mod.py", "pkg/added.py", "src/other/a.py", "src/other/b.py")
    outcome = build_record(
        root,
        _merge(child, api_files=listed),
        pr_id="1",
        repo="acme/widget",
        merged_at="2025-06-24T22:46:29Z",
        arm=ARM,
        corpus_files=listed,
    )
    assert isinstance(outcome, Rejection)
    assert outcome.stage == "file_set"
    assert 0.0 <= outcome.agreement < MIN_FILE_AGREEMENT


def test_a_wildly_inflated_list_is_refused_at_shape_detection(
    repo: tuple[Path, str, str],
) -> None:
    """The real zenml case never reaches the file-set gate, and that is fine.

    A 92-file list on a 2-file change breaks `parent_commit`'s squash-versus-rebase test
    first. Both paths exclude and count the PR; recorded so a future reader does not
    assume the agreement gate is the only thing catching this.
    """
    root, _, child = repo
    inflated = (*(f"src/unrelated/f{i}.py" for i in range(60)), "pkg/mod.py")
    outcome = build_record(
        root,
        _merge(child),
        pr_id="1",
        repo="acme/widget",
        merged_at="2025-06-24T22:46:29Z",
        arm=ARM,
        corpus_files=inflated,
    )
    assert isinstance(outcome, Rejection) and outcome.stage == "parent_commit"


def test_an_honest_pr_becomes_a_record(repo: tuple[Path, str, str]) -> None:
    root, _, child = repo
    # api_files explicit: this passed with none only via the removed corpus fallback.
    outcome = build_record(
        root,
        _merge(child, api_files=("pkg/mod.py", "pkg/added.py")),
        pr_id="2",
        repo="acme/widget",
        merged_at="2025-06-24T22:46:29Z",
        arm=ARM,
        corpus_files=("pkg/mod.py", "pkg/added.py"),
    )
    assert not isinstance(outcome, Rejection), getattr(outcome, "reason", "")
    assert outcome.changed_files == ("pkg/added.py", "pkg/mod.py")
    assert outcome.changed_symbols == ("pkg.mod.Handler.validate",)
    assert outcome.parent_sha and outcome.repo_id == "acme/widget"


def test_the_corpus_file_list_for_zenml_3757_is_not_the_change() -> None:
    """The measurement behind A24, asserted rather than described.

    Fails if the package is ever replaced by one without the defect, which is worth
    knowing: the gate's threshold was chosen against this distribution.
    """
    with zipfile.ZipFile(PACKAGE) as archive:
        detail = pd.read_parquet(
            io.BytesIO(archive.read("AIDev_BC_Analyser/human_commit_detail.parquet"))
        )
    detail["pr_id"] = detail["pr_id"].astype("int64")
    attributed = {f for f in set(detail[detail.pr_id == ZENML_3757].filename) if f.endswith(".py")}
    assert len(attributed) > 50, "the package no longer over-attributes; revisit A24"
    assert "src/zenml/zen_server/routers/runs_endpoints.py" in attributed
    assert "docs/mkdocstrings_helper.py" in attributed


def test_a_superset_diff_is_refused_against_githubs_own_list(repo: tuple[Path, str, str]) -> None:
    """The indirect-merge failure: a confident, resolvable, WRONG parent.

    When a PR's commits land via another PR, `merge_commit_sha` belongs to that other
    PR. The subject sequence will not match, so it routes to squash and resolves a
    parent -- and if the other PR carried nothing else, the diff is a SUPERSET by only
    the files they share, which a ratio threshold waves through. Set equality is the
    only comparison that refuses it, so it is asserted directly.
    """
    root, _, child = repo
    merge = MergeInfo(
        pr_id="4",
        number=4,
        merged=True,
        merge_commit_sha=child,
        merged_at="2025-06-24T22:46:29Z",
        base_ref="main",
        commit_count=1,
        api_files=("pkg/mod.py",),  # GitHub says one file; the diff shows two
    )
    outcome = build_record(
        root,
        merge,
        pr_id="4",
        repo="acme/widget",
        merged_at=merge.merged_at,
        arm=ARM,
        corpus_files=("pkg/mod.py",),
    )
    assert isinstance(outcome, Rejection)
    assert outcome.stage == "file_set"
    assert "not equal" in outcome.reason and "merged indirectly" in outcome.reason
