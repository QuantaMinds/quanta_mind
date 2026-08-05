"""Verification that the fix-versus-change comparison cannot report what it does not know.

WHAT: Asserts the base-branch split verdict, the clone-failure denominator correction,
      and that an unanswerable comparison returns "unavailable" rather than a number.
WHY:  This module produces figures that go into Results, and every assertion here guards
      against the same failure the study is about: a well-formed number standing in for
      an absent measurement.

      The empty-arm case is the sharpest. With no non-default-branch units scanned, the
      gap is not zero and the fix is not "corrective" — it is unmeasured. A verdict of
      `corrective` computed from an empty arm would be exactly the false CLEAN that
      started all of this, one level up in the analysis.

      The clone-failure case is the one that would silently mislead. The baseline counted
      clone failures at repository level with no PR rows; the current runner emits one row
      per PR. Differencing those denominators reports a corpus shift that is really a
      definition change.
IMPORTS: phase0.pilot.{compare,attempt}.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from phase0.pilot.attempt import Attempt
from phase0.pilot.compare import compare

BASELINE: dict = {
    "admission_rate": 0.5,
    "records_built": 1,
    "prs_attempted": 2,
    "rejected_by_stage": {"parent_commit": 1},
    "attrition_by_commit_count": {"1": {"n": 2, "admitted": 1, "admission_rate": 0.5}},
    "attrition_by_corpus_file_count": {"1-4": {"n": 2, "admitted": 1, "admission_rate": 0.5}},
}


def _row(
    index: int,
    *,
    outcome: str = "",
    on_default: bool = True,
    stage: str = "",
    repo: str = "o/r",
) -> Attempt:
    return Attempt(
        pr_id=str(index),
        repo=repo,
        admitted=not stage,
        stage=stage,
        category="resource" if stage else "",
        commit_count=1,
        corpus_py_files=1,
        derived_files=1,
        changed_symbols=1,
        outcome=outcome,
        base_is_default=on_default,
        changed_lines=10,
    )


def test_a_material_gap_becomes_a_stratum() -> None:
    """Two rates far apart mean two populations, not one measured twice."""
    attempts = [
        _row(0, outcome="broke", on_default=False),
        _row(1, outcome="broke", on_default=False),
        _row(2, outcome="clean"),
        _row(3, outcome="clean"),
    ]

    rate = compare(BASELINE, attempts)["breakage_rate"]
    assert isinstance(rate, dict)

    assert rate["default_branch"] == 0.0
    assert rate["other_branch"] == 1.0
    assert rate["verdict"] == "stratum"


def test_matching_rates_read_as_corrective() -> None:
    """When the split agrees, the fix moved no population and that can be said."""
    attempts = [
        _row(0, outcome="broke", on_default=False),
        _row(1, outcome="clean", on_default=False),
        _row(2, outcome="broke"),
        _row(3, outcome="clean"),
    ]

    rate = compare(BASELINE, attempts)["breakage_rate"]
    assert isinstance(rate, dict)
    assert rate["verdict"] == "corrective"


def test_an_empty_arm_is_unmeasured_not_corrective() -> None:
    """No units off the default branch means the question was not answered.

    Reporting `corrective` here would be a well-formed verdict standing in for an absent
    measurement — the study's own subject, arriving in its analysis code.
    """
    attempts = [_row(0, outcome="broke"), _row(1, outcome="clean")]

    rate = compare(BASELINE, attempts)["breakage_rate"]
    assert isinstance(rate, dict)

    assert rate["other_branch"] is None
    assert rate["absolute_gap"] is None
    assert rate["verdict"] is None


def test_clone_failures_are_removed_before_composition_is_compared() -> None:
    """The baseline never recorded them as rows, so leaving them in compares denominators.

    A resource failure is attrition with a cause and stays in the run's own report; it is
    dropped only for the comparison, and the count of what was dropped is published.
    """
    attempts = [
        _row(0, outcome="clean"),
        _row(1, stage="clone_failed", repo="big/repo"),
        _row(2, stage="clone_failed", repo="big/repo"),
    ]

    composition = compare(BASELINE, attempts)["composition"]
    assert isinstance(composition, dict)

    assert composition["clone_failed_rows_removed"] == 2
    assert composition["clone_failed_repos"] == ["big/repo"]
    # One admitted of one comparable attempt, not one of three.
    assert composition["admission_rate_new"] == 1.0


def test_churn_says_unavailable_rather_than_zero() -> None:
    """Without a per-PR baseline, "no churn" and "cannot tell" are different claims."""
    result = compare(BASELINE, [_row(0, outcome="clean")])["churn"]
    assert isinstance(result, dict)

    assert result["available"] is False
    assert "newly_admitted" not in result


def test_churn_separates_the_two_directions() -> None:
    """A net-flat corpus and a corpus with large two-way churn are not the same corpus."""
    before = [_row(0, stage="parent_commit"), _row(1, outcome="clean")]
    after = [_row(0, outcome="clean"), _row(1, stage="file_set")]

    result = compare(BASELINE, after, before)["churn"]
    assert isinstance(result, dict)

    assert (result["newly_admitted"], result["newly_rejected"], result["net"]) == (1, 1, 0)
    assert result["newly_rejected_detail"] == ["o/r#1->file_set"]
