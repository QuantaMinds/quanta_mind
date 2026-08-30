"""Verification that the session token is never stored and that expired is not unknown.

WHAT: Drives `store/accounts` against a real store — recording, issuing, expiry, revocation.
WHY:  **A STOLEN DATABASE MUST NOT HAND ANYONE A LIVE SESSION.** Only the SHA-256 of a token is
      written; `issue()` returns the token once and cannot return it again. The test that matters
      is the one asserting the raw token appears NOWHERE in the file, because a hash that is
      computed and then also stored alongside the original is a mistake nothing else would catch.

      **EXPIRED AND UNKNOWN ARE DIFFERENT ANSWERS.** Both refuse, and folding them together would
      show "sign in again" to somebody whose token was never valid, and "no such session" to
      somebody whose session simply aged out.
IMPORTS: pytest, quantamind.store.{accounts,schema}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from quantamind.store.accounts import SESSION_HOURS, State, issue, remember, revoke, whose
from quantamind.store.schema import open_store

NOW = 1_700_000_000


@pytest.fixture
def conn(tmp_path: Path) -> sqlite3.Connection:
    conn = open_store(tmp_path / "s.db")
    remember(conn, "dhanush", 4242, at=NOW)
    return conn


def test_the_raw_token_is_nowhere_in_the_database(conn: sqlite3.Connection, tmp_path: Path) -> None:
    """The property the whole design exists for, asserted on the bytes on disk."""
    token = issue(conn, "dhanush", at=NOW)
    conn.commit()

    on_disk = (tmp_path / "s.db").read_bytes()

    assert token.encode() not in on_disk, "the session token was written to the database"
    assert whose(conn, token, at=NOW).signed_in is True, "and yet it must still verify"


def test_a_valid_token_names_its_owner(conn: sqlite3.Connection) -> None:
    session = whose(conn, issue(conn, "dhanush", at=NOW), at=NOW + 60)

    assert (session.state, session.login) == (State.ACTIVE, "dhanush")
    assert "signed in as dhanush" in session.why()


def test_an_expired_session_is_not_an_unknown_one(conn: sqlite3.Connection) -> None:
    token = issue(conn, "dhanush", at=NOW, hours=1)

    session = whose(conn, token, at=NOW + 3601)

    assert session.state is State.EXPIRED
    assert session.login == "dhanush", "an expired session still knows whose it was"
    assert session.signed_in is False


def test_a_forged_token_is_unknown_and_names_nobody(conn: sqlite3.Connection) -> None:
    session = whose(conn, "not-a-real-token", at=NOW)

    assert (session.state, session.login) == (State.UNKNOWN, "")
    assert session.signed_in is False


def test_two_sessions_get_different_tokens(conn: sqlite3.Connection) -> None:
    """A fixed token would verify for everybody. Cheap to get wrong, catastrophic."""
    assert issue(conn, "dhanush", at=NOW) != issue(conn, "dhanush", at=NOW)


def test_revoking_ends_exactly_one_session(conn: sqlite3.Connection) -> None:
    kept = issue(conn, "dhanush", at=NOW)
    going = issue(conn, "dhanush", at=NOW)

    assert revoke(conn, going) == 1
    assert whose(conn, going, at=NOW).state is State.UNKNOWN
    assert whose(conn, kept, at=NOW).signed_in is True, "revoking one ended another"


def test_revoking_nothing_returns_zero(conn: sqlite3.Connection) -> None:
    """Signing out a token that was never valid must not report success."""
    assert revoke(conn, "not-a-real-token") == 0


def test_a_session_cannot_be_issued_without_an_end(conn: sqlite3.Connection) -> None:
    """A credential with no expiry outlives every reason it was granted."""
    with pytest.raises(ValueError, match="positive number of hours"):
        issue(conn, "dhanush", at=NOW, hours=0)


def test_the_default_session_is_two_weeks() -> None:
    assert SESSION_HOURS == 24 * 14


def test_an_account_needs_a_login_and_a_real_id(conn: sqlite3.Connection) -> None:
    with pytest.raises(ValueError, match="login and a positive id"):
        remember(conn, "", 1, at=NOW)
    with pytest.raises(ValueError, match="login and a positive id"):
        remember(conn, "dhanush", 0, at=NOW)


def test_signing_in_again_does_not_move_first_seen(conn: sqlite3.Connection) -> None:
    remember(conn, "dhanush", 4242, at=NOW + 86_400)

    first = conn.execute("SELECT first_seen, last_seen FROM account WHERE login = ?", ("dhanush",))
    first_seen, last_seen = first.fetchone()

    assert int(first_seen) == NOW
    assert int(last_seen) == NOW + 86_400
