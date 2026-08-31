"""What a repository's reviews cost, read from a REAL store with rows this test put there.

WHAT: Drives `store/costs.spent` against a store created by `store.schema.open_store`, with review
      rows inserted directly, and asserts the counts and the refusals.
WHY:  **THE COLUMNS WERE WRITTEN SINCE A5 AND NOTHING READ THEM**, so the first reader has no
      existing behaviour to compare against and every number here has to come from rows a test can
      point at. A mock would have proved only that the function returns a dataclass.

      **THE TWO ZEROS ARE THE POINT.** "No reviews" and "reviews that consulted no model" both
      total zero and mean opposite things, so they are asserted apart. A reader that collapsed them
      would report a product that costs nothing when in fact it has never run.
IMPORTS: pytest, sqlite3, quantamind.store.{costs,schema,tenancy}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from quantamind.store import tenancy
from quantamind.store.costs import Costs, NothingRecorded, spent
from quantamind.store.schema import open_store


@pytest.fixture
def conn(tmp_path: Path) -> sqlite3.Connection:
    made = open_store(tenancy.store_for(tmp_path, "acme", "widgets"))
    made.execute(
        "INSERT INTO repo (host, name, first_seen) "
        "VALUES ('github.com', 'acme/widgets', 1700000000)"
    )
    made.commit()
    return made


def _repo_id(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT id FROM repo WHERE name = 'acme/widgets'").fetchone()[0])


def _review(conn: sqlite3.Connection, pr: int, *, requests: int = 0, out: int = 0) -> None:
    conn.execute(
        "INSERT INTO review (repo_id, pr_number, head_sha, created_at, fire_decision, "
        "  request_count, tokens_in, tokens_out) VALUES (?, ?, ?, 1700000000, 0, ?, ?, ?)",
        (_repo_id(conn), pr, str(pr) * 40, requests, out * 2, out),
    )
    conn.commit()


def test_a_repository_with_no_reviews_reports_none_rather_than_zero_cost(
    conn: sqlite3.Connection,
) -> None:
    got = spent(conn, _repo_id(conn))

    assert (got.reviews, got.billed, got.requests, got.tokens_out) == (0, 0, 0, 0)
    with pytest.raises(NothingRecorded):
        _ = got.per_review


def test_reviews_that_consulted_no_model_are_counted_but_not_billed(
    conn: sqlite3.Connection,
) -> None:
    """The second zero. Two reviews ran; the allocator read nothing, which is a decision."""
    _review(conn, 1)
    _review(conn, 2)

    got = spent(conn, _repo_id(conn))

    assert got.reviews == 2, "the reviews themselves must still be counted"
    assert got.billed == 0
    with pytest.raises(NothingRecorded, match="not the same as a cost of zero"):
        _ = got.per_review


def test_the_mean_is_over_billed_reviews_not_over_all_reviews(conn: sqlite3.Connection) -> None:
    """The value, not the mechanism: dividing by 4 instead of 2 halves the answer silently."""
    _review(conn, 1, requests=3, out=6000)
    _review(conn, 2, requests=1, out=2000)
    _review(conn, 3)
    _review(conn, 4)

    got = spent(conn, _repo_id(conn))
    per_requests, per_tokens = got.per_review

    assert (got.reviews, got.billed) == (4, 2)
    assert per_requests == 2.0, f"4 requests over 2 billed reviews is 2.0, got {per_requests}"
    assert per_tokens == 4000.0, (
        f"8000 output tokens over 2 billed reviews is 4000, got {per_tokens} — dividing by all "
        "four reviews would report 2000 and understate what a paid review costs"
    )


def test_another_repositorys_reviews_are_not_counted(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO repo (host, name, first_seen) VALUES ('github.com', 'acme/other', 1700000000)"
    )
    other = int(conn.execute("SELECT id FROM repo WHERE name = 'acme/other'").fetchone()[0])
    conn.execute(
        "INSERT INTO review (repo_id, pr_number, head_sha, created_at, fire_decision, "
        "  request_count, tokens_out) VALUES (?, 9, ?, 1700000000, 0, 5, 9999)",
        (other, "9" * 40),
    )
    conn.commit()
    _review(conn, 1, requests=1, out=100)

    got = spent(conn, _repo_id(conn))

    assert got.requests == 1, f"another repository's spend leaked in: {got}"
    assert got.tokens_out == 100


def test_counts_that_contradict_each_other_are_refused() -> None:
    with pytest.raises(ValueError, match="more billed reviews than reviews"):
        Costs(reviews=1, billed=2, requests=0, tokens_in=0, tokens_out=0)
    with pytest.raises(ValueError, match="cannot both be right"):
        Costs(reviews=1, billed=0, requests=0, tokens_in=0, tokens_out=5)
