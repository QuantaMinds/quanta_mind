"""Verification that the gradient check reports a trend only when there is one to report.

WHAT: Asserts the monotone verdict, the minimum band size, and that too few usable bands
      returns None rather than "flattened".
WHY:  A28 replaced a detection rule that read the corpus file list with one that reads
      commit subjects. The evidence that it WORKED is not that attrition fell — attrition
      falls whether the recovered parents are right or wrong. Correctness is settled by
      hand-verifying parents against `merge_commit_sha`'s first parent. This module
      settles the other half: whether the mechanism is gone, which shows as failure no
      longer climbing with commit count.

      The refusal cases carry the weight. A band of two PRs yields a rate of 0.0 or 0.5 on
      noise and would decide the verdict; fewer than two usable bands answers nothing at
      all. Returning "gradient flattened" from either would be a well-formed reassurance
      about a measurement that was never made — the thing this instrument keeps producing
      and the reason it is being rebuilt.
IMPORTS: phase0.pilot.{gradient,attempt}.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from phase0.pilot.attempt import Attempt
from phase0.pilot.gradient import MIN_BAND_N, parent_gradient


def _rows(commits: int, total: int, failures: int) -> list[Attempt]:
    """`total` attempts in one commit-count band, `failures` of them parent_commit."""
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


def test_a_rising_gradient_says_the_mechanism_may_remain() -> None:
    """Failure still climbing with size means a file-set dependence survives somewhere."""
    attempts = _rows(1, 10, 1) + _rows(3, 10, 4) + _rows(10, 10, 7)

    result = parent_gradient(attempts)

    assert result["still_rises_with_size"] is True
    assert result["verdict"] == "mechanism may remain"


def test_a_flat_gradient_is_reported_as_flattened() -> None:
    """The outcome A28 predicts: detection no longer reads anything size-correlated."""
    attempts = _rows(1, 10, 1) + _rows(3, 10, 1) + _rows(10, 10, 0)

    result = parent_gradient(attempts)

    assert result["still_rises_with_size"] is False
    assert result["verdict"] == "gradient flattened"


def test_a_thin_band_is_reported_but_kept_out_of_the_trend() -> None:
    """Two PRs give a rate of 0.0 or 0.5 on noise; that must not decide the verdict."""
    attempts = _rows(1, 10, 1) + _rows(3, 10, 1) + _rows(30, 2, 2)

    result = parent_gradient(attempts)
    bands = result["bands"]
    assert isinstance(bands, dict)

    assert bands["21+"]["n"] == 2
    assert bands["21+"]["failure_rate"] == 1.0
    assert bands["21+"]["counted_in_trend"] is False
    # The 100% band is visible, and excluded from the trend that would have flipped.
    assert result["bands_in_trend"] == ["1", "2-5"]
    assert result["verdict"] == "gradient flattened"


def test_too_few_usable_bands_answers_nothing() -> None:
    """One band cannot show a trend, and "flattened" would be a false reassurance."""
    attempts = _rows(1, 10, 1) + _rows(3, 2, 0)

    result = parent_gradient(attempts)

    assert result["still_rises_with_size"] is None
    assert result["verdict"] is None
    assert result["bands_in_trend"] == ["1"]


def test_the_band_threshold_is_fixed_not_chosen_after_the_fact() -> None:
    """Pinned so it cannot be lowered once the bands are in front of us."""
    assert MIN_BAND_N == 5


def test_an_empty_corpus_reports_no_rate() -> None:
    """Zero attempts is not a zero failure rate."""
    result = parent_gradient([])

    assert result["pooled_failure_rate"] is None
    assert result["bands"] == {}
    assert result["verdict"] is None


def test_a_perfectly_flat_gradient_is_not_rising() -> None:
    """Equal rates across bands is the outcome A28 predicts, not a warning.

    A monotone test written with `>=` alone answers True here, so the check would report
    "mechanism may remain" on exactly the evidence that the mechanism is gone. An alarm
    that fires on success is one nobody keeps heeding.
    """
    attempts = _rows(1, 10, 2) + _rows(3, 10, 2) + _rows(10, 10, 2)

    result = parent_gradient(attempts)

    assert [b["failure_rate"] for b in result["bands"].values()] == [0.2, 0.2, 0.2]
    assert result["still_rises_with_size"] is False
    assert result["verdict"] == "gradient flattened"


def test_a_dip_then_a_rise_is_not_monotone() -> None:
    """"Rises monotonically" means every step, not merely a higher endpoint."""
    attempts = _rows(1, 10, 5) + _rows(3, 10, 1) + _rows(10, 10, 6)

    result = parent_gradient(attempts)

    assert result["still_rises_with_size"] is False
