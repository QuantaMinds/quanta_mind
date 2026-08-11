"""Verification that a populated band is not mistaken for a representative one.

WHAT: Asserts what each commit-count band lost to clone failures, which repositories took
      it, and that all three clone-failure stage names count.
WHY:  Split from test_gradient.py, which asserts the TREND. This file asserts what the
      trend is computed over, and the distinction is the point: clone timeouts remove the
      largest repositories, and the largest repositories hold the multi-commit PRs. A flat
      failure rate in the 21+ band therefore means either "the mechanism is gone" or "the
      hard cases never arrived", and the two are identical in the gradient table.
IMPORTS: phase0.pilot.{gradient,attempt}.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from phase0.pilot.attempt import Attempt
from phase0.pilot.gradient import parent_gradient


def _rows(commits: int, total: int, failures: int) -> list[Attempt]:
    made = []
    for index in range(total):
        stage = "parent_commit" if index < failures else ""
        made.append(
            Attempt(
                pr_id=f"{commits}-{index}",
                repo="o/r",
                admitted=not stage,
                stage=stage,
                category="integrity" if stage else "",
                commit_count=commits,
                corpus_py_files=1,
                derived_files=1,
                changed_symbols=1,
            )
        )
    return made


def _lost(commits: int, total: int, repo: str = "big/repo") -> list[Attempt]:
    """Attempts in a band that never reached the rule, because the clone timed out."""
    return [
        Attempt(
            pr_id=f"lost-{commits}-{i}",
            repo=repo,
            admitted=False,
            stage="clone_failed",
            category="resource",
            commit_count=commits,
            corpus_py_files=1,
            derived_files=0,
            changed_symbols=0,
        )
        for i in range(total)
    ]


def test_a_band_reports_what_it_lost_to_clone_failures() -> None:
    """A populated band can still be unrepresentative, and the two look identical without this.

    Clone timeouts remove the largest repositories, and the largest repositories hold the
    multi-commit PRs. So a flat failure rate in the 21+ band means either "the mechanism is
    gone" or "the hard cases never arrived" — and only the share lost distinguishes them.
    """
    attempts = _rows(30, 5, 0) + _lost(30, 7, repo="getsentry/sentry")

    band = parent_gradient(attempts)["bands"]["21+"]

    assert band["failure_rate"] == 0.0
    assert band["lost_to_clone_failure"] == 7
    assert band["repos_lost"] == ["getsentry/sentry"]
    assert band["share_lost"] == 0.5833
    assert band["distinct_repos_present"] == 1


def test_a_band_that_lost_nothing_says_so_with_a_zero() -> None:
    """Zero lost is a measurement. An absent key would read as "not checked"."""
    band = parent_gradient(_rows(1, 6, 1))["bands"]["1"]

    assert band["lost_to_clone_failure"] == 0
    assert band["share_lost"] == 0.0
    assert band["repos_lost"] == []


def test_both_clone_failure_stages_count_as_lost() -> None:
    """A timeout and a deleted repository are different exclusions, equally unreachable.

    They are split at the source because a timeout selects on repository SIZE -- an 11.5x
    median difference, which is the study's own confounder -- while a repository that no
    longer exists selects on nothing and has no size to measure. For "did this band reach
    the rule at all" they are the same, and a journal written before the split says
    `clone_failed`, so all three names must count.
    """
    rows = _rows(30, 5, 0) + _lost(30, 1, repo="legacy/clone-failed")
    for stage, repo in (("clone_timeout", "a/timeout"), ("repo_gone", "b/deleted")):
        rows.append(
            Attempt(
                pr_id=f"{stage}-1",
                repo=repo,
                admitted=False,
                stage=stage,
                category="resource",
                commit_count=30,
                corpus_py_files=1,
                derived_files=0,
                changed_symbols=0,
            )
        )

    band = parent_gradient(rows)["bands"]["21+"]

    assert band["lost_to_clone_failure"] == 3
    assert band["repos_lost"] == ["a/timeout", "b/deleted", "legacy/clone-failed"]
