"""The touch index against real SQLite, with the window boundary as the thing under test.

WHAT: Writes touches into an actual database and asserts the counts, the half-open window, that
      re-indexing does not double, and that a count without a bound is refused.
WHY:  **The exclusive upper bound is the product.** A ranking that can see the commit it is ranking
      is a lookup, and the error is invisible downstream: every score rises by one, the ordering
      often survives, and the retrospective simply looks better than it is.
IMPORTS: quantamind.store.schema, quantamind.store.touches, quantamind.types.touch.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quantamind.store import schema
from quantamind.store import touches as touch_store
from quantamind.types.touch import Touch

DAY = 86400


def _store(tmp_path: Path):
    conn = schema.open_store(tmp_path / "s.db")
    return conn, touch_store.ensure_repo(conn, "github.com", "a/b")


def test_the_window_excludes_the_change_itself(tmp_path: Path) -> None:
    conn, repo = _store(tmp_path)
    now = 1_700_000_000
    touch_store.index(conn, repo, [Touch("f.py", now - DAY), Touch("f.py", now)])
    got = touch_store.counts(conn, repo, ["f.py"], as_of=now)
    assert got["f.py"] == 1, (
        "a touch at exactly as_of is the change being ranked, not prior history"
    )


def test_the_window_includes_its_lower_bound(tmp_path: Path) -> None:
    conn, repo = _store(tmp_path)
    now = 1_700_000_000
    edge = now - touch_store.YEAR_SECONDS
    touch_store.index(conn, repo, [Touch("f.py", edge), Touch("f.py", edge - 1)])
    got = touch_store.counts(conn, repo, ["f.py"], as_of=now)
    assert got["f.py"] == 1, "the window is [as_of - window, as_of); the lower edge is inside it"


def test_a_path_with_no_history_scores_zero_rather_than_vanishing(tmp_path: Path) -> None:
    conn, repo = _store(tmp_path)
    touch_store.index(conn, repo, [Touch("a.py", 1_700_000_000 - DAY)])
    got = touch_store.counts(conn, repo, ["a.py", "never.py"], as_of=1_700_000_000)
    assert got["never.py"] == 0, (
        "never-touched is a score; the no-history case depends on seeing it"
    )


def test_reindexing_the_same_history_does_not_double_the_counts(tmp_path: Path) -> None:
    conn, repo = _store(tmp_path)
    now = 1_700_000_000
    history = [Touch("f.py", now - DAY), Touch("f.py", now - 2 * DAY)]
    touch_store.index(conn, repo, history)
    touch_store.index(conn, repo, history)
    got = touch_store.counts(conn, repo, ["f.py"], as_of=now)
    assert got["f.py"] == 2, f"re-indexing doubled the count to {got['f.py']}"


def test_a_count_without_a_usable_bound_is_refused(tmp_path: Path) -> None:
    conn, repo = _store(tmp_path)
    with pytest.raises(touch_store.UnboundedRankingError):
        touch_store.counts(conn, repo, ["f.py"], as_of=0)
    with pytest.raises(touch_store.UnboundedRankingError):
        touch_store.counts(conn, repo, ["f.py"], as_of=1_700_000_000, window=0)


def test_two_repositories_do_not_share_a_history(tmp_path: Path) -> None:
    conn, a = _store(tmp_path)
    b = touch_store.ensure_repo(conn, "github.com", "c/d")
    now = 1_700_000_000
    touch_store.index(conn, a, [Touch("f.py", now - DAY)])
    touch_store.index(conn, b, [Touch("f.py", now - DAY), Touch("f.py", now - 2 * DAY)])
    assert touch_store.counts(conn, a, ["f.py"], as_of=now)["f.py"] == 1
    assert touch_store.counts(conn, b, ["f.py"], as_of=now)["f.py"] == 2


def test_ensure_repo_is_idempotent(tmp_path: Path) -> None:
    conn, first = _store(tmp_path)
    assert touch_store.ensure_repo(conn, "github.com", "a/b") == first
