"""Coverage read back from a REAL store, including every absence that must not become a grant.

WHAT: `store/billing/entitlement.record` and `covering`, against a real SQLite store at schema v8.
WHY:  **THE EXPENSIVE MISTAKES HERE ARE BOTH SILENT.** Reading an absent row as paid hands out a
      tier nobody bought, and reading it as refused switches off every customer who installed
      before billing existed. Neither produces an error; both produce a number somebody bills on.
      So absence, an unknown state string and staleness each get their own case.

      **STALENESS IS ASSERTED AS A FACT, NOT AS A DECISION.** `covering()` reports it; nothing here
      asserts what a review does about it, because that belongs to `gate.py` and asserting it in
      two places is how the two come to disagree.
IMPORTS: quantamind.store.billing.entitlement, quantamind.store.schema.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3

import pytest

from quantamind.store.billing.entitlement import FREE, Coverage, State, covering, record
from quantamind.store.schema import create

NOW = 1_700_000_000


@pytest.fixture
def conn() -> sqlite3.Connection:
    made = sqlite3.connect(":memory:")
    create(made)
    return made


def test_an_account_we_have_never_heard_of_is_free(conn: sqlite3.Connection) -> None:
    """Absence is Free. Not paid, not refused, and nothing is written to make it so."""
    got = covering(conn, "github", "stranger", now=NOW)

    assert got == Coverage(
        FREE, State.NONE, None, "no subscription on record", 0, None, None, False
    )
    assert got.paid is False
    assert conn.execute("SELECT COUNT(*) FROM entitlement").fetchone()[0] == 0


def test_a_paid_account_reads_back_whole(conn: sqlite3.Connection) -> None:
    record(
        conn,
        "github",
        "acme",
        tier="team",
        state=State.ACTIVE,
        as_of=NOW,
        seats_included=25,
        payment_ref="sub_123",
        valid_through=NOW + 86_400,
        grace_until=NOW + 604_800,
    )
    got = covering(conn, "github", "acme", now=NOW)

    assert (got.tier, got.state, got.seats_included) == ("team", State.ACTIVE, 25)
    assert got.paid is True
    assert got.stale is False


def test_a_trial_is_paying_equivalent(conn: sqlite3.Connection) -> None:
    """The card is on file and the trial has not ended; withholding here would be a bug."""
    record(conn, "github", "acme", tier="team", state=State.TRIALING, as_of=NOW)

    assert covering(conn, "github", "acme", now=NOW).paid is True


@pytest.mark.parametrize("state", [State.PAST_DUE, State.CANCELLED, State.NONE])
def test_an_unpaid_state_is_not_paid(conn: sqlite3.Connection, state: State) -> None:
    record(conn, "github", "acme", tier="team", state=state, as_of=NOW)

    assert covering(conn, "github", "acme", now=NOW).paid is False


def test_the_same_name_on_two_forges_is_two_customers(conn: sqlite3.Connection) -> None:
    """The reason the key is `(forge, account)` and not `account`."""
    record(conn, "github", "acme", tier="team", state=State.ACTIVE, as_of=NOW)
    record(conn, "bitbucket", "acme", tier=FREE, state=State.NONE, as_of=NOW)

    assert covering(conn, "github", "acme", now=NOW).tier == "team"
    assert covering(conn, "bitbucket", "acme", now=NOW).tier == FREE


def test_a_newer_push_replaces_the_row_whole(conn: sqlite3.Connection) -> None:
    """Fields are not merged: a stale push must not leave half of an old tier behind."""
    record(conn, "github", "acme", tier="team", state=State.ACTIVE, as_of=NOW, seats_included=25)
    record(conn, "github", "acme", tier=FREE, state=State.CANCELLED, as_of=NOW + 10)

    got = covering(conn, "github", "acme", now=NOW + 10)
    assert (got.tier, got.state) == (FREE, State.CANCELLED)
    assert got.seats_included is None, "a field the newer push omitted survived from the older one"
    assert conn.execute("SELECT COUNT(*) FROM entitlement").fetchone()[0] == 1


def test_an_unknown_state_is_not_read_as_active(conn: sqlite3.Connection) -> None:
    """A value from a newer billing service must not grant the paid tier on a typo."""
    record(conn, "github", "acme", tier="team", state=State.ACTIVE, as_of=NOW)
    conn.execute("UPDATE entitlement SET state = 'gold_plated'")
    conn.commit()

    got = covering(conn, "github", "acme", now=NOW)
    assert got.state is State.NONE
    assert got.paid is False


def test_staleness_is_reported_once_grace_has_passed(conn: sqlite3.Connection) -> None:
    record(
        conn,
        "github",
        "acme",
        tier="team",
        state=State.ACTIVE,
        as_of=NOW,
        grace_until=NOW + 100,
    )

    assert covering(conn, "github", "acme", now=NOW + 99).stale is False
    assert covering(conn, "github", "acme", now=NOW + 101).stale is True


def test_no_grace_window_is_never_stale(conn: sqlite3.Connection) -> None:
    """`grace_until` absent means the billing service set no deadline, not a deadline of zero."""
    record(conn, "github", "acme", tier="team", state=State.ACTIVE, as_of=NOW)

    assert covering(conn, "github", "acme", now=NOW + 10_000_000).stale is False


@pytest.mark.parametrize(
    ("forge", "account", "tier"),
    [("", "acme", "team"), ("github", "", "team"), ("github", "acme", "  ")],
)
def test_a_row_keyed_on_nothing_is_refused(
    conn: sqlite3.Connection, forge: str, account: str, tier: str
) -> None:
    with pytest.raises(ValueError):
        record(conn, forge, account, tier=tier, state=State.ACTIVE, as_of=NOW)
