"""An unchecked base branch is excluded from both arms, never counted as off-default.

WHAT: That `report` puts `base_on_default="unknown"` rows in neither rate, reports the
      count, and that the two rates are computed over their own denominators.
WHY:  `base_is_default` was a BOOL, so `not base_is_default` swept an unchecked
      repository into the off-default arm. `default_branch` returns "" on a `gh` timeout,
      which compared to `base_ref` gives False -- indistinguishable from a genuine merge
      into a non-default branch, in the variable the analysis stratifies on.

      This is the same shape as the missing-`gh` crash the run now refuses, at one-repo
      granularity rather than all-repos, and the same shape as UNSCANNABLE being kept out
      of the clean cell. It is the first instance of this defect class caught BEFORE it
      produced a wrong number.
IMPORTS: phase0.pilot.attempt, phase0.pilot.report.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from phase0.pilot.attempt import Attempt
from phase0.pilot.report import report


def _row(pr_id: str, outcome: str, on_default: str) -> Attempt:
    return Attempt(
        pr_id=pr_id,
        repo="a/b",
        admitted=True,
        stage="",
        category="",
        commit_count=1,
        corpus_py_files=1,
        derived_files=1,
        changed_symbols=1,
        outcome=outcome,
        base_on_default=on_default,
    )


def test_unknown_base_is_in_neither_rate_and_is_counted() -> None:
    """Three scanned rows, one unchecked: each rate sees one row, not two."""
    summary = report(
        [
            _row("1", "broke", "yes"),
            _row("2", "clean", "no"),
            _row("3", "broke", "unknown"),
        ],
        clone_failures=0,
        repos=1,
    )
    assert summary["scanned_on_default"] == 1
    assert summary["scanned_off_default"] == 1
    assert summary["base_branch_unknown"] == 1
    assert summary["breakage_rate_default_branch"] == 1.0
    assert summary["breakage_rate_other_branch"] == 0.0
    # The unknown row still counts toward the pooled rate: it was scanned, and only the
    # base-branch STRATIFICATION is unavailable for it.
    assert summary["outcome_scanned"] == 3
    assert summary["outcome_broke"] == 2


def test_an_unknown_row_would_have_moved_the_off_default_rate_as_a_bool() -> None:
    """The regression, stated as the number the old coding would have produced.

    Under `not base_is_default` the unknown row lands in off-default, making that rate
    1/2 = 0.5 instead of 0/1 = 0.0 -- a fabricated off-default breakage from a repository
    whose branch was never looked up.
    """
    summary = report(
        [_row("1", "clean", "no"), _row("2", "broke", "unknown")],
        clone_failures=0,
        repos=1,
    )
    assert summary["breakage_rate_other_branch"] == 0.0
    assert summary["scanned_off_default"] == 1
    assert summary["base_branch_unknown"] == 1
