"""What a review cost — and the two ways that number could lie.

WHAT: Exercises `types/spend.py` and `store/reviews.record_spend()` against a real store.
WHY:  **A COST THAT MIGHT BE AN UNDERCOUNT MUST NOT BE WRITTEN AS A TOTAL.** `serve/settle.py`
      asks the model per surviving finding through a path that reports no usage, so a review that
      settled anything spent more than we measured. Writing that as the cost would put a quietly
      low number on a dashboard and get priced from — and nobody reading it later could tell.

      **AND THE MODEL'S REASONING IS BILLED.** Vertex reports `thoughtsTokenCount` apart from the
      answer; a count of only the visible reply understates a review by most of it. One real
      summary measured 422 in and 1,631 out, almost all of the output thinking.
IMPORTS: store.{reviews,schema,touches}, types.spend.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3

import pytest

from quantamind.store import reviews, touches
from quantamind.store.schema import create
from quantamind.types.spend import Spend, measured

REPLY = {"usageMetadata": {"promptTokenCount": 422, "totalTokenCount": 2053}}


def _store() -> tuple[sqlite3.Connection, int]:
    conn = sqlite3.connect(":memory:")
    create(conn)
    repo_id = touches.ensure_repo(conn, "github.com", "o/r")
    conn.execute(
        "INSERT INTO review (repo_id, pr_number, head_sha, created_at, fire_decision)"
        " VALUES (?, 7, 'abc123', 1, 1)",
        (repo_id,),
    )
    conn.commit()
    return conn, repo_id


def test_the_models_own_reasoning_is_counted_as_output() -> None:
    """Thinking tokens are billed; counting only the reply understates the cost by most of it."""
    assert measured(REPLY, 16_114) == Spend(
        requests=1, tokens_in=422, tokens_out=1631, ms=16_114, complete=True
    )


def test_a_reply_with_no_usage_records_the_call_and_no_invented_tokens() -> None:
    """It was still paid for. Zero tokens is honest; a guessed number is not."""
    assert measured({}, 900) == Spend(requests=1, tokens_in=0, tokens_out=0, ms=900)


def test_incompleteness_is_contagious_when_costs_are_added() -> None:
    """A total containing one unmetered call is itself a floor."""
    total = Spend(1, 10, 20, 100).plus(Spend(1, 5, 5, 50, complete=False))

    assert total == Spend(2, 15, 25, 150, complete=False)


def test_tokens_without_a_request_cannot_be_constructed() -> None:
    with pytest.raises(ValueError, match="no request recorded"):
        Spend(requests=0, tokens_in=10)


def test_a_measured_cost_is_written_to_the_row() -> None:
    conn, _ = _store()

    assert reviews.record_spend(conn, 1, Spend(2, 422, 1631, 16_114)) is True

    row = conn.execute(
        "SELECT request_count, tokens_in, tokens_out, latency_ms FROM review WHERE id = 1"
    ).fetchone()
    assert tuple(row) == (2, 422, 1631, 16_114), (
        f"the cost columns still read {tuple(row)}. They have existed since the schema was written "
        "and nothing ever wrote them"
    )


def test_a_floor_is_refused_rather_than_written_as_a_total() -> None:
    """**THE ONE THAT WOULD GET PRICED FROM.** An undercount on a dashboard is worse than a gap."""
    conn, _ = _store()

    assert reviews.record_spend(conn, 1, Spend(2, 422, 1631, 16_114, complete=False)) is False

    row = conn.execute("SELECT request_count, tokens_out FROM review WHERE id = 1").fetchone()
    assert tuple(row) == (0, 0), "an incomplete cost was written as though it were the total"


def test_no_model_call_writes_nothing() -> None:
    conn, _ = _store()

    assert reviews.record_spend(conn, 1, Spend()) is False
