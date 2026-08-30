"""Verification that the calibration window widens for a thin repository and stops widening.

WHAT: Builds a real store, writes touches at controlled timestamps, and drives `window_for` and
      `baseline` across the sample-size boundary and the widening ceiling.
WHY:  **`store/calibration.py` HAD NO TESTS AND ALL THREE OF ITS CONSTANTS WERE FREELY MUTABLE.**
      Setting `MIN_CALIBRATION` to 0 makes every repository "calibrated" on whatever it has;
      setting `MAX_WINDOW_YEARS` to 0 or 9 changes how far back a floor may reach. Every tier of
      the suite stayed green for all six mutations.

      **THE NUMBERS ARE NOT ARBITRARY AND THE MODULE SAYS SO.** A 90th percentile from 71 points
      is estimated from about seven points above it, and `gin-gonic/gin` fired on 29.0% against a
      10% target on exactly that sample. Widening past four years compares a change against a
      codebase that no longer exists. A test that let either drift would let the firing rate
      drift with it.

      **THE COUNT IS RETURNED, NOT DISCARDED**, because a floor estimated from 40 changes and one
      from 400 are different claims. That is asserted directly: a thin repository must come back
      with its real, small count rather than a widened window pretending to be a full one.

      Values are written out rather than imported — `MIN_CALIBRATION - 1` reads the number under
      test and passes at any value.
IMPORTS: pytest, quantamind.store.schema, quantamind.store.touches, quantamind.store.calibration.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from quantamind.store import calibration
from quantamind.store.schema import open_store
from quantamind.store.touches import YEAR_SECONDS, UnboundedRankingError, ensure_repo

NOW = 1_700_000_000
MIN_SAMPLE, CEILING, OVER = 150, 4, 400
"""The shipped values, written out. See the module docstring on why they are not imported."""


def _store(tmp_path: Path) -> tuple[sqlite3.Connection, int]:
    conn = open_store(tmp_path / "s.db")
    return conn, ensure_repo(conn, "github.com", "o/r")


def _touches(conn: sqlite3.Connection, repo_id: int, *, count: int, oldest_year: int) -> None:
    """`count` distinct changes spread through the year ending `oldest_year` years before NOW."""
    start = NOW - YEAR_SECONDS * oldest_year
    conn.executemany(
        "INSERT INTO touch (repo_id, path, committed_at) VALUES (?, ?, ?)",
        [(repo_id, f"src/f{n % 7}.py", start + n * 97) for n in range(count)],
    )
    conn.commit()


def test_the_calibration_constants_are_the_measured_values() -> None:
    """Pinned to what the measurement produced, not to each other."""
    assert calibration.MIN_CALIBRATION == MIN_SAMPLE
    assert calibration.MAX_WINDOW_YEARS == CEILING
    assert calibration.RECENT_CHANGES == OVER


def test_a_repository_with_enough_recent_history_uses_one_year(tmp_path: Path) -> None:
    """The ordinary case: no widening when the first window already holds a usable sample."""
    conn, repo = _store(tmp_path)
    _touches(conn, repo, count=MIN_SAMPLE + 20, oldest_year=1)

    span, found = calibration.window_for(conn, repo, as_of=NOW)

    assert span == YEAR_SECONDS
    assert found == MIN_SAMPLE + 20


def test_a_thin_year_widens_until_the_sample_is_usable(tmp_path: Path) -> None:
    """Below the sample floor in one year, above it in two, so two years is what comes back."""
    conn, repo = _store(tmp_path)
    _touches(conn, repo, count=100, oldest_year=1)
    _touches(conn, repo, count=100, oldest_year=2)

    span, found = calibration.window_for(conn, repo, as_of=NOW)

    assert span == YEAR_SECONDS * 2, "the window did not widen for a sample of 100"
    assert found == 200


def test_widening_stops_at_the_ceiling_and_reports_the_short_sample(tmp_path: Path) -> None:
    """A sparse repository gets the widest allowed window and its REAL count, not a fabricated one.

    This is the assertion that fails if MAX_WINDOW_YEARS moves: at 9 the span would be larger,
    at 0 the loop would not run at all.
    """
    conn, repo = _store(tmp_path)
    for year in range(1, 9):
        _touches(conn, repo, count=10, oldest_year=year)

    span, found = calibration.window_for(conn, repo, as_of=NOW)

    assert span == YEAR_SECONDS * CEILING
    assert found == 40, f"reported {found} changes; the four-year window holds 40"


def test_a_repository_with_no_history_reports_zero_rather_than_raising(tmp_path: Path) -> None:
    """An empty store is a legitimate state, and must stay distinguishable from a failure."""
    conn, repo = _store(tmp_path)

    span, found = calibration.window_for(conn, repo, as_of=NOW)

    assert (span, found) == (YEAR_SECONDS * CEILING, 0)


def test_the_floor_is_computed_over_recent_changes_by_default(tmp_path: Path) -> None:
    """`baseline` with no `over` must still calibrate. At RECENT_CHANGES = 0 it reads nothing."""
    conn, repo = _store(tmp_path)
    _touches(conn, repo, count=MIN_SAMPLE + 50, oldest_year=1)

    floor = calibration.baseline(conn, repo, as_of=NOW)

    assert floor > 0, "the floor collapsed to zero on a repository with a full year of history"


def test_the_floor_refuses_a_timestamp_it_cannot_bound(tmp_path: Path) -> None:
    """The false-positive direction: a bad input is a refusal, never a quietly wrong floor."""
    conn, repo = _store(tmp_path)

    with pytest.raises(UnboundedRankingError, match="as_of must be a positive timestamp"):
        calibration.baseline(conn, repo, as_of=0)
