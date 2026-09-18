"""Verification that an out-of-order Stripe delivery cannot switch off a live customer.

WHAT: Drives `store/subscriptions` against a real SQLite store — the write, the ordering refusal,
      the read, and what `paid()` says about a card that is being retried.
WHY:  **STRIPE DOES NOT GUARANTEE DELIVERY ORDER AND THE ROW IS AN ENTITLEMENT.** A retried
      `canceled` arriving after the `active` that superseded it would, under a plain upsert, cut
      off a paying customer — and nothing downstream could tell that from a real cancellation.
      **This is the defect the plan named as most likely to survive review**, because every
      hand-written test delivers events in the order the author was thinking in. So the
      out-of-order case is written first here, and it is written twice: once proving the stale
      write is refused, and once proving the row still holds the newer state afterwards.

      **A REFUSED WRITE RETURNS A REASON, AND THAT IS ASSERTED.** If a stale write and a fresh one
      both returned nothing, a deleted ordering guard would be indistinguishable from a working
      one — `AGENTS.md` rule 14's question, asked of this module.

      **`current()` RETURNING None MEANS "NEVER HAD ONE", NOT "CANCELLED".** Those are different
      answers to a customer asking why they were charged, so both are exercised.
IMPORTS: pytest, quantamind.store.{schema,subscriptions}, quantamind.types.billing.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from quantamind.store.billing.subscriptions import current, paid, record
from quantamind.store.schema import open_store
from quantamind.types.billing import Standing, Subscription

NOW = 1_700_000_000


@pytest.fixture
def conn(tmp_path: Path) -> sqlite3.Connection:
    return open_store(tmp_path / "s.db")


def sub(standing: Standing, *, event_at: int, seats: int = 3) -> Subscription:
    return Subscription(
        account="octocat",
        subscription_id="sub_1",
        customer_id="cus_1",
        price_id="price_1UGfiCGY5MuBVWoyiOyqLh6G",
        standing=standing,
        seats=seats,
        amount_cents=2900,
        currency="usd",
        current_period_end=NOW + 30 * 86_400,
        event_at=event_at,
    )


def test_an_older_event_does_not_overwrite_a_newer_one(conn: sqlite3.Connection) -> None:
    """A retried `canceled` arriving after the `active` that superseded it. The whole guard."""
    assert record(conn, sub(Standing.ACTIVE, event_at=NOW + 10)).stored is True

    late = record(conn, sub(Standing.CANCELED, event_at=NOW))

    assert late.stored is False
    assert "older than the stored" in late.reason
    held = current(conn, "octocat")
    assert held is not None and held.standing is Standing.ACTIVE, "the live customer survived"


def test_the_refusal_names_both_timestamps_so_an_operator_need_not_open_stripe(
    conn: sqlite3.Connection,
) -> None:
    record(conn, sub(Standing.ACTIVE, event_at=NOW + 10))

    late = record(conn, sub(Standing.CANCELED, event_at=NOW))

    assert f"event at {NOW} is older than the stored {NOW + 10}" in late.reason
    assert "(active)" in late.reason


def test_a_newer_event_replaces_the_standing(conn: sqlite3.Connection) -> None:
    record(conn, sub(Standing.ACTIVE, event_at=NOW))

    assert record(conn, sub(Standing.CANCELED, event_at=NOW + 1)).stored is True
    held = current(conn, "octocat")
    assert held is not None and held.standing is Standing.CANCELED


def test_a_redelivery_of_the_same_event_is_applied_rather_than_refused(
    conn: sqlite3.Connection,
) -> None:
    """Stripe retries the same event for three days. `>=`, so a redelivery repairs a hand edit."""
    record(conn, sub(Standing.ACTIVE, event_at=NOW, seats=3))
    conn.execute("UPDATE subscription SET seats = 99")
    conn.commit()

    again = record(conn, sub(Standing.ACTIVE, event_at=NOW, seats=3))

    assert again.stored is True
    held = current(conn, "octocat")
    assert held is not None and held.seats == 3


def test_an_account_with_no_row_reads_as_never_having_had_one(conn: sqlite3.Connection) -> None:
    assert current(conn, "octocat") is None
    assert paid(conn, "octocat") == (False, "octocat has no subscription on record")


def test_the_whole_row_survives_a_round_trip(conn: sqlite3.Connection) -> None:
    """Every column, not just the standing: a dropped column is silent until an invoice is wrong."""
    record(conn, sub(Standing.ACTIVE, event_at=NOW))

    held = current(conn, "octocat")

    assert held == sub(Standing.ACTIVE, event_at=NOW)


def test_past_due_is_reported_as_unpaid_but_named_as_a_retry(conn: sqlite3.Connection) -> None:
    """The one state where a human should look. "False" alone would hide it among cancellations."""
    record(conn, sub(Standing.PAST_DUE, event_at=NOW))

    is_paid, why = paid(conn, "octocat")

    assert is_paid is False
    assert "is past due" in why and "has not given up" in why


def test_trialing_counts_as_paying(conn: sqlite3.Connection) -> None:
    record(conn, sub(Standing.TRIALING, event_at=NOW))

    is_paid, why = paid(conn, "octocat")

    assert is_paid is True
    assert "trialing, 3 seat(s) at 29.00 USD" in why


def test_a_subscription_with_no_account_is_refused_at_the_write(conn: sqlite3.Connection) -> None:
    """A payment attached to nobody. The repair is a human reading two dashboards side by side."""
    orphan = Subscription(
        account="",
        subscription_id="sub_1",
        customer_id="cus_1",
        price_id="price_1",
        standing=Standing.ACTIVE,
        seats=1,
        amount_cents=2900,
        currency="usd",
        current_period_end=NOW,
        event_at=NOW,
    )

    with pytest.raises(ValueError, match="client_reference_id"):
        record(conn, orphan)


def test_the_newest_subscription_wins_when_an_account_has_had_two(conn: sqlite3.Connection) -> None:
    """They cancelled and came back. The first row is the record that they were ever a customer."""
    record(conn, sub(Standing.CANCELED, event_at=NOW))
    returning = Subscription(
        account="octocat",
        subscription_id="sub_2",
        customer_id="cus_1",
        price_id="price_1",
        standing=Standing.ACTIVE,
        seats=5,
        amount_cents=2900,
        currency="usd",
        current_period_end=NOW + 86_400,
        event_at=NOW + 100,
    )
    record(conn, returning)

    held = current(conn, "octocat")

    assert held is not None and held.subscription_id == "sub_2"
    kept = conn.execute("SELECT COUNT(*) FROM subscription").fetchone()[0]
    assert kept == 2, "the cancelled subscription is still on the record"
