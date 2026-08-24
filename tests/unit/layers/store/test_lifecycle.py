"""What became of a change after we spoke, and the three ways that record could lie.

WHAT: Exercises `observe`, `signal` and `board` against a real store, asserting that production
      history is appended rather than overwritten, that never-observed stays distinguishable from
      observed-healthy, and that a board too small to read says so.
WHY:  **AN OUTCOME LEDGER THAT QUIETLY OVERWRITES IS WORSE THAN NONE.** "Still running" is a claim
      about an instant; if a later observation replaces an earlier one, the only evidence of what
      the service looked like BEFORE it broke is gone -- which is the exact interval an incident
      review needs.

      **AND A DASHBOARD THAT SHOWS A RATE OVER THREE OBSERVATIONS INVITES A CONCLUSION THE DATA
      CANNOT CARRY.** `thin()` is asserted here rather than trusted, because the failure mode is a
      number that looks fine.
IMPORTS: stdlib, quantamind.store.{lifecycle,schema}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3

import pytest

from quantamind.store import lifecycle as lc
from quantamind.store.schema import create


def store() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    create(conn)
    conn.execute("INSERT INTO repo (host, name, first_seen) VALUES ('github.com', 'a/b', 1)")
    for n in range(1, 4):
        conn.execute(
            "INSERT INTO review (repo_id, pr_number, head_sha, created_at, fire_decision) "
            "VALUES (1, ?, ?, ?, 1)",
            (n, f"sha{n}", 100 + n),
        )
    conn.commit()
    return conn


def test_production_history_is_appended_never_overwritten() -> None:
    conn = store()
    lc.signal(conn, 1, at=10, state=lc.ProdState.HEALTHY, source="datadog")
    lc.signal(conn, 1, at=20, state=lc.ProdState.FAILING, source="datadog", detail="5xx")

    kept = conn.execute(
        "SELECT observed_at, state FROM prod_signal ORDER BY observed_at"
    ).fetchall()
    assert kept == [(10, "healthy"), (20, "failing")], (
        "the earlier observation was destroyed; the interval before the failure is the one an "
        "incident review needs"
    )
    row = next(r for r in lc.board(conn, 1).rows if r.review_id == 1)
    assert row.prod_state is lc.ProdState.FAILING, "the board must show the LATEST observation"


def test_never_observed_is_not_the_same_as_observed_healthy() -> None:
    conn = store()
    lc.signal(conn, 1, at=10, state=lc.ProdState.HEALTHY, source="datadog")
    rows = {r.review_id: r for r in lc.board(conn, 1).rows}

    assert rows[1].prod_state is lc.ProdState.HEALTHY
    assert rows[1].prod_observed_at == 10
    assert rows[2].prod_state is lc.ProdState.UNKNOWN, "never looked must not read as healthy"
    assert rows[2].prod_observed_at is None


def test_observing_twice_updates_rather_than_duplicating() -> None:
    conn = store()
    lc.observe(conn, 1, at=10, merge_state=lc.MergeState.OPEN)
    lc.observe(conn, 1, at=20, merge_state=lc.MergeState.MERGED, merged_at=15)

    assert conn.execute("SELECT COUNT(*) FROM lifecycle").fetchone()[0] == 1
    row = next(r for r in lc.board(conn, 1).rows if r.review_id == 1)
    assert row.merge_state is lc.MergeState.MERGED
    assert row.merged_at == 15


def test_a_posted_time_is_not_erased_by_a_later_merge_observation() -> None:
    conn = store()
    lc.observe(conn, 1, at=10, merge_state=lc.MergeState.OPEN, posted_at=5)
    lc.observe(conn, 1, at=20, merge_state=lc.MergeState.MERGED, merged_at=15)
    row = next(r for r in lc.board(conn, 1).rows if r.review_id == 1)
    assert row.posted_at == 5, "when we spoke is a fact; a later observation must not clear it"


def test_a_signal_with_no_source_is_refused() -> None:
    conn = store()
    with pytest.raises(ValueError, match="source"):
        lc.signal(conn, 1, at=10, state=lc.ProdState.FAILING, source="  ")


def test_a_board_too_small_to_read_says_so_and_a_large_one_does_not() -> None:
    conn = store()
    small = lc.board(conn, 1).thin()
    assert small is not None and "a rate needs at least 20" in small, (
        f"three rows cannot support a rate and must say which threshold they miss, got {small!r}"
    )

    for n in range(4, 30):
        conn.execute(
            "INSERT INTO review (repo_id, pr_number, head_sha, created_at, fire_decision) "
            "VALUES (1, ?, ?, ?, 1)",
            (n, f"sha{n}", 100 + n),
        )
    conn.commit()
    for n in range(1, 30):
        lc.signal(conn, n, at=10, state=lc.ProdState.HEALTHY, source="datadog")
    # The control: without it this test would pass by always reporting "too thin".
    assert lc.board(conn, 1).thin() is None, "29 observed changes must be readable"
