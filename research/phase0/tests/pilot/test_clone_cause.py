"""Four clone causes, kept apart -- and the substring bug that collapsed two of them.

WHAT: Known-answer tests for `clone_failure_stage` and for the star count
      `rows_for_clone_failure` records on every row it writes.
WHY:  Neither was covered. The suite returned the same result whether
      `clone_failure_stage` distinguished four causes or two, and whether the `stars`
      parameter was read or discarded -- which is why both defects survived a 200-repo
      walk. Split from `test_unmeasured_covariates.py` at its 200-line cap.
IMPORTS: phase0.handlabel.select, phase0.pilot.{clone_cause,covariates},
      phase0.pipeline.worktree.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from phase0.handlabel.select import Candidate
from phase0.pilot.clone_cause import clone_failure_stage, rows_for_clone_failure
from phase0.pipeline.worktree import CloneFailed

CORPUS_FILES = ("a/b.py", "a/c.py", "README.md")


def _candidate(pr_id: int = 1) -> Candidate:
    return Candidate(
        pr_id=pr_id,
        repo="o/r",
        number=pr_id,
        merged_at="2026-03-01T12:00:00Z",
        title="t",
        commit_shas=("s",),
        changed_files=CORPUS_FILES,
    )


def test_a_clone_failure_row_records_the_repository_size_it_was_handed() -> None:
    """`stars` was ACCEPTED AND NEVER READ here, hardcoding -1 on every failure row.

    Nothing covered it, which is why it survived: the suite returned the same result
    whether the parameter was used or discarded. This is the known-answer test that
    tells those apart.

    It matters because these rows are exactly the ones whose size decides whether
    `clone_failure_stage`'s four-way split does anything. Measured off the parquet at 139
    repositories the class medians are 16,245 / 1,618 / 590 / 166 stars against a 449
    baseline — so the split is real, and the journal could not show it because every row
    it applies to said NOT MEASURED.
    """
    rows = rows_for_clone_failure(
        [_candidate(1), _candidate(2)],
        [],
        CloneFailed("o/r: clone exceeded 900s"),
        {"o/r": 4321},
    )

    assert [r.stars for r in rows] == [4321, 4321]
    assert [r.stage for r in rows] == ["clone_timeout", "clone_timeout"]


def test_a_repository_absent_from_the_star_table_stays_unmeasured() -> None:
    """-1 survives as a real state. Absent is NOT MEASURED, never "zero stars"."""
    rows = rows_for_clone_failure(
        [_candidate(1)], [], CloneFailed("o/r: remote: Repository not found."), {}
    )

    assert [r.stars for r in rows] == [-1]
    assert rows[0].stage == "repo_gone"


def test_a_missing_git_lfs_is_our_machine_not_a_missing_repository() -> None:
    """The known-answer test for the substring bug, which nothing covered.

    `git-lfs: command not found` contains "not found", so the single-substring classifier
    this replaced returned `repo_gone` -- putting a failure class whose median is 2,325
    stars into the bucket whose median is 194 and whose docstring says it "has no size to
    measure". Eight of fifteen failures in the 200-repository walk were misfiled this way.

    The ordering is the fix, so the ordering is what is asserted: the harness cause is
    tested BEFORE the "not found" cause and cannot be shadowed by it again.
    """
    lfs = CloneFailed(
        "AMICI-dev/AMICI: git-lfs filter-process: git-lfs: command not found "
        "fatal: the remote end hung up unexpectedly"
    )

    assert clone_failure_stage(lfs) == "git_lfs_absent"
    # The discriminating half: the same words, without git-lfs, must still be repo_gone.
    assert clone_failure_stage(CloneFailed("o/r: remote: Repository not found.")) == "repo_gone"


def test_each_clone_cause_is_recognised_and_they_are_distinct() -> None:
    """Four causes, four answers. A classifier collapsing any two fails here."""
    seen = {
        clone_failure_stage(CloneFailed("o/r: clone exceeded 900s")): "timeout",
        clone_failure_stage(CloneFailed("o/r: error: RPC failed; curl 56")): "transport",
        clone_failure_stage(CloneFailed("o/r: git-lfs: command not found")): "lfs",
        clone_failure_stage(CloneFailed("o/r: remote: Repository not found.")): "gone",
    }

    assert sorted(seen) == [
        "clone_timeout",
        "git_lfs_absent",
        "repo_gone",
        "transport_failure",
    ], "two causes collapsed into one stage"


def test_an_unrecognised_message_is_named_not_defaulted_to_a_cause() -> None:
    """ "We did not classify this" must not arrive wearing someone else's cause."""
    assert clone_failure_stage(CloneFailed("o/r: something nobody has seen")) == "clone_failed"
