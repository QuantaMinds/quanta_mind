"""Verification of A20's pre-registered metric: disagreement by changed-lines quartile.

WHAT: Asserts the quartile cuts, the denominator, and that an unmeasured size is its own
      band rather than the smallest one.
WHY:  A20 makes step 5's consistency gate blocking and requires its attrition be read BY
      SIZE. The metric decides something: a rate rising across quartiles makes A16's
      stratified RR the only quotable result and forces A17's bounds to be computed over
      the size-stratified exclusion. A metric that decides that much is asserted rather
      than eyeballed once.

      The unmeasured case has its own test because folding `changed_lines = -1` into Q1
      would place every PR whose size we failed to read into the band least likely to
      disagree -- the direction that hides the trend the metric exists to find.
IMPORTS: phase0.pilot.{quartile,attempt}.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from phase0.pilot.attempt import Attempt
from phase0.pilot.quartile import by_changed_lines


def _attempt(index: int, lines: int, stage: str = "") -> Attempt:
    return Attempt(
        pr_id=str(index),
        repo="o/r",
        admitted=not stage,
        stage=stage,
        category="integrity" if stage else "",
        commit_count=1,
        corpus_py_files=1,
        derived_files=1,
        changed_symbols=1,
        changed_lines=lines,
    )


def test_cut_points_come_from_the_data_and_are_reported() -> None:
    """Quartiles move with the corpus, so the boundary is published rather than implied."""
    result = by_changed_lines([_attempt(i, lines) for i, lines in enumerate([1, 2, 3, 4])])

    assert result["cut_points"] == {"q1": 1, "q2": 2, "q3": 3}
    quartiles = result["quartiles"]
    assert isinstance(quartiles, dict)
    assert [quartiles[q]["n"] for q in ("Q1", "Q2", "Q3", "Q4")] == [1, 1, 1, 1]


def test_rate_denominator_is_every_attempt_in_the_band() -> None:
    """ "How often did the gate fire on PRs this size", not "what share of rejections
    were this size" -- the second moves with the size distribution and says nothing."""
    attempts = [
        _attempt(0, 10),
        _attempt(1, 20),
        _attempt(2, 1000, stage="file_set"),
        _attempt(3, 2000, stage="file_set"),
    ]

    result = by_changed_lines(attempts)
    quartiles = result["quartiles"]
    assert isinstance(quartiles, dict)

    assert quartiles["Q1"]["disagreement_rate"] == 0.0
    assert quartiles["Q4"]["disagreement_rate"] == 1.0
    assert quartiles["Q4"]["file_set_rejections"] == 1


def test_a_rejection_at_another_stage_is_not_a_disagreement() -> None:
    """A20 names the `file_set` gate specifically. `parent_commit` is a different fact."""
    attempts = [_attempt(0, 10), _attempt(1, 20, stage="parent_commit")]

    quartiles = by_changed_lines(attempts)["quartiles"]
    assert isinstance(quartiles, dict)

    # Named, not `all(...)`: an empty mapping satisfies `all` vacuously, so the version
    # of this test that used one would have passed had the bands never been built.
    # Two attempts populate two bands, so the band set is pinned here as well: it is the
    # denominator the zeros are counted over, and a silently empty one proves nothing.
    assert {band: quartiles[band]["file_set_rejections"] for band in quartiles} == {
        "Q1": 0,
        "Q3": 0,
    }


def test_unmeasured_size_is_its_own_band_not_the_smallest() -> None:
    """A PR whose size we could not read is not a small PR."""
    attempts = [_attempt(0, 10), _attempt(1, 20), _attempt(2, -1, stage="file_set")]

    result = by_changed_lines(attempts)
    quartiles = result["quartiles"]
    assert isinstance(quartiles, dict)

    assert result["unmeasured"] == 1
    assert sum(int(band["n"]) for band in quartiles.values()) == 2
    assert all(band["file_set_rejections"] == 0 for band in quartiles.values())


def test_no_measured_sizes_reports_nothing_rather_than_zero() -> None:
    """An empty result and a measured rate of zero are different claims."""
    result = by_changed_lines([_attempt(0, -1), _attempt(1, -1)])

    assert result["quartiles"] == {}
    assert result["cut_points"] is None
    assert result["unmeasured"] == 2
