"""Verification that the shape window is anchored to the change and is the length it claims.

WHAT: Pins the two spans `ingest/change_shape` reads over — the thirty days of churn before the
      change, and the three hundred changes its norms are drawn from — by inspecting the git
      arguments actually built rather than the numbers declared beside them.
WHY:  **THIS WINDOW HAS BEEN WRONG BEFORE, IN BOTH DIRECTIONS.** It was once computed as thirty
      days before the WALL CLOCK rather than before the change, so on a real clone it reached
      past the change into work that did not exist at review time and, on an old change, missed
      the churn entirely. `ending_at` was written to make that impossible, and the whole
      correctness argument is that at review time the future does not exist.

      **BOTH CONSTANTS WERE FREELY MUTABLE.** `change_shape` is covered only by `tests/live`, and
      mutating `RECENT_DAYS` to 0 or 61, or `SAMPLE` to 0 or 601, left every tier green. At
      `SAMPLE = 0` the git argument becomes `-0` and the norms are drawn from nothing.

      Thirty and three hundred are written out; reading the constants would pass at any value.
IMPORTS: pytest, quantamind.ingest.change_shape, quantamind.ingest.review_window.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from quantamind.ingest import change_shape
from quantamind.ingest.review_window import WindowUnreadable, ending_at

DAYS, DRAWN = 30, 300
"""The shipped spans, written out. See the module docstring."""

STAMP = "2026-03-15T12:00:00+00:00"


def test_the_churn_window_opens_thirty_days_before_the_change(tmp_path: Path) -> None:
    """`--since` is the change's own timestamp minus thirty days, and `--until` is the change."""
    window = ending_at(STAMP, change_shape.RECENT_DAYS, site="t")
    since = next(a for a in window.args if a.startswith("--since="))[len("--since=") :]
    until = next(a for a in window.args if a.startswith("--until="))[len("--until=") :]

    assert until == STAMP, "the window must close at the change, not at the wall clock"
    assert dt.datetime.fromisoformat(until) - dt.datetime.fromisoformat(since) == dt.timedelta(
        days=DAYS
    )


def test_an_unreadable_timestamp_refuses_rather_than_falling_back_to_now() -> None:
    """The failure that produced the original bug: a fallback to wall clock leaks the future."""
    with pytest.raises(WindowUnreadable):
        ending_at("not a timestamp", change_shape.RECENT_DAYS, site="t")


def test_the_norms_are_drawn_from_three_hundred_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    """The git argument carries the count. At SAMPLE = 0 this reads `-0` and draws from nothing."""
    seen: list[list[str]] = []

    def run(clone: Path, args: list[str]) -> str:
        seen.append(args)
        return ""

    monkeypatch.setattr(change_shape, "_run", run)
    change_shape._norms(Path("/clone"), "abc123")

    assert seen, "the norms were computed without asking git anything"
    assert f"-{DRAWN}" in seen[0], f"git was asked for {seen[0]}"


def test_the_norms_walk_back_from_the_change_not_from_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Drawing from HEAD would take the repository's 'normal' from work not yet written."""
    seen: list[list[str]] = []
    monkeypatch.setattr(change_shape, "_run", lambda clone, args: seen.append(args) or "")

    change_shape._norms(Path("/clone"), "abc123")

    assert seen[0][-1] == "abc123", "the log did not end at the change under review"
    assert "HEAD" not in seen[0]
