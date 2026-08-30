"""Who signed in, and the sessions that say so — with the token never written down.

WHAT: `remember(conn, login, github_id, at)` records an account. `issue()` mints a session and
      returns the token ONCE, storing only its hash. `whose(conn, token, at)` says who a token
      belongs to, or why it does not. `revoke()` ends one.
WHY:  **B2 — no user model existed, so nothing could be attributed to a person.** An installation
      keys on a GitHub account (`store/installations.py`); a session keys on a human who proved
      they control it.

      **THE TOKEN IS NEVER STORED, ONLY ITS HASH.** A stolen database must not hand anyone a live
      session. `issue()` returns the token to its caller once and cannot return it again, the same
      shape as a password reset — and the same reason `Settings.app_key_path` holds a path rather
      than a key.

      **EXPIRED AND UNKNOWN ARE DIFFERENT ANSWERS.** Both refuse, and a caller that could not tell
      them apart would show "sign in again" to somebody whose token was never valid and "not
      found" to somebody whose session simply aged out. `Session.state` says which.

      **A SESSION HAS AN END, WRITTEN AT ISSUE.** A credential with no expiry is one that outlives
      every reason it was granted, and "we will clean them up later" is not a mechanism.
IMPORTS: stdlib only. The store layer.
CONSUMED BY: `serve/web/signin.py`.
"""

from __future__ import annotations

import enum
import hashlib
import secrets
import sqlite3
from dataclasses import dataclass

SESSION_HOURS = 24 * 14
"""How long a session lives. Two weeks: long enough not to be a nuisance, short enough that a
leaked cookie is not a permanent key. Written at issue, never extended silently on use."""

TOKEN_BYTES = 32


class State(enum.Enum):
    """What a presented token is. Three values, and none is a default for another."""

    UNKNOWN = "unknown"
    """No such session. A forged token, or one revoked and gone."""

    EXPIRED = "expired"
    ACTIVE = "active"


@dataclass(frozen=True, slots=True)
class Session:
    """Who a token belongs to, and whether it still counts."""

    state: State
    login: str

    @property
    def signed_in(self) -> bool:
        return self.state is State.ACTIVE

    def why(self) -> str:
        if self.state is State.UNKNOWN:
            return "no such session"
        if self.state is State.EXPIRED:
            return f"the session for {self.login} has expired"
        return f"signed in as {self.login}"


def _hashed(token: str) -> str:
    """SHA-256 of the token. What the database holds, so the database holds no credential."""
    return hashlib.sha256(token.encode()).hexdigest()


def remember(conn: sqlite3.Connection, login: str, github_id: int, *, at: int) -> None:
    """Record an account, or refresh when it was last seen. `first_seen` never moves."""
    if not login.strip() or github_id <= 0:
        raise ValueError(f"an account needs a login and a positive id, got {login!r} {github_id}")
    conn.execute(
        "INSERT INTO account (login, github_id, first_seen, last_seen) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(login) DO UPDATE SET last_seen = excluded.last_seen, "
        "github_id = excluded.github_id",
        (login, github_id, at, at),
    )
    conn.commit()


def issue(conn: sqlite3.Connection, login: str, *, at: int, hours: int = SESSION_HOURS) -> str:
    """Mint a session and return its token ONCE. Only the hash is stored.

    **THE RETURN VALUE IS THE ONLY COPY.** Losing it means issuing another, which is the property
    that makes a database dump useless to whoever takes it.
    """
    if hours <= 0:
        raise ValueError(f"a session must last a positive number of hours, got {hours}")
    token = secrets.token_urlsafe(TOKEN_BYTES)
    conn.execute(
        "INSERT INTO session (token_hash, login, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (_hashed(token), login, at, at + hours * 3600),
    )
    conn.commit()
    return token


def whose(conn: sqlite3.Connection, token: str, *, at: int) -> Session:
    """Who this token belongs to, or why it does not count. Never raises on a bad token."""
    row = conn.execute(
        "SELECT login, expires_at FROM session WHERE token_hash = ?", (_hashed(token),)
    ).fetchone()
    if row is None:
        return Session(State.UNKNOWN, "")
    login, expires_at = str(row[0]), int(row[1])
    return Session(State.ACTIVE if at < expires_at else State.EXPIRED, login)


def revoke(conn: sqlite3.Connection, token: str) -> int:
    """End one session. Returns how many rows went, so signing out nothing is visible."""
    cursor = conn.execute("DELETE FROM session WHERE token_hash = ?", (_hashed(token),))
    conn.commit()
    return int(cursor.rowcount)
