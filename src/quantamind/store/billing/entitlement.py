"""What the billing service last said about an account, and how long ago it said it.

WHAT: `record()` writes one account's coverage; `covering(conn, forge, account, now)` reads it back
      as a `Coverage` that says what we were told AND whether the telling is still fresh.
WHY:  **AN ABSENT ROW IS FREE, NOT PAID AND NOT REFUSED.** An account installed before billing
      existed has no row, and nothing here backfills one. Reading absence as paid would grant an
      entitlement nobody bought; reading it as refused would switch off every existing customer at
      their next delivery. Free is the only reading that invents nothing.

      **`stale` IS A FACT, NOT A VERDICT.** This module reports that the billing service has not
      spoken since `grace_until`; it does not decide what to do about that. `gate.py` does, and it
      degrades rather than refusing — a push that never arrived is our failure, and withdrawing a
      paying customer's reviews to punish our own outage is the wrong way round.

      **`(forge, account)` IS THE KEY.** A Bitbucket workspace `acme` and a GitHub organisation
      `acme` are different customers who may both install us, and a row that cannot tell them
      apart bills one for the other.

      **THE WHOLE ROW IS REPLACED, NEVER PATCHED.** Each push carries the complete standing of an
      account as the billing service knows it. Merging fields would let a stale push resurrect a
      tier the newest one dropped, and `as_of` is what a caller compares to decide which is newer.
IMPORTS: stdlib only (enum, dataclasses, sqlite3). The store layer.
CONSUMED BY: `store/billing/gate.py`, `serve/web/entitlement_route.py`.
"""

from __future__ import annotations

import enum
import sqlite3
from dataclasses import dataclass

FREE = "free"


class State(enum.Enum):
    """How an account stands with the billing service. No value is a default for another."""

    NONE = "none"
    """No row. Never subscribed, or installed before billing existed."""

    ACTIVE = "active"
    TRIALING = "trialing"
    """Paying-equivalent: the trial has not ended and the card is on file."""

    PAST_DUE = "past_due"
    """A payment failed. Still a customer — Stripe retries for weeks."""

    CANCELLED = "cancelled"


_BY_VALUE = {one.value: one for one in State}


@dataclass(frozen=True, slots=True)
class Coverage:
    """What we were told, and whether it is still fresh. Never a bare tier string."""

    tier: str
    state: State
    seats_included: int | None
    reason: str
    as_of: int
    valid_through: int | None
    grace_until: int | None
    stale: bool
    """The billing service has not spoken since `grace_until`. A fact; `gate.py` decides."""

    @property
    def paid(self) -> bool:
        """Whether this account is entitled to what a paid tier buys, right now."""
        return self.state in (State.ACTIVE, State.TRIALING)


def record(
    conn: sqlite3.Connection,
    forge: str,
    account: str,
    *,
    tier: str,
    state: State,
    as_of: int,
    seats_included: int | None = None,
    payment_ref: str = "",
    reason: str = "",
    valid_through: int | None = None,
    grace_until: int | None = None,
) -> None:
    """Replace this account's coverage with what the billing service just said."""
    if not forge.strip() or not account.strip():
        raise ValueError(f"coverage needs a forge and an account, got {forge!r} {account!r}")
    if not tier.strip():
        raise ValueError(f"coverage for {forge}/{account} names no tier")
    conn.execute(
        "INSERT INTO entitlement (forge, account, tier, state, seats_included, payment_ref,"
        " reason, as_of, valid_through, grace_until)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(forge, account) DO UPDATE SET"
        " tier = excluded.tier, state = excluded.state, seats_included = excluded.seats_included,"
        " payment_ref = excluded.payment_ref, reason = excluded.reason, as_of = excluded.as_of,"
        " valid_through = excluded.valid_through, grace_until = excluded.grace_until",
        (
            forge,
            account,
            tier,
            state.value,
            seats_included,
            payment_ref,
            reason,
            as_of,
            valid_through,
            grace_until,
        ),
    )
    conn.commit()


def covering(conn: sqlite3.Connection, forge: str, account: str, *, now: int) -> Coverage:
    """This account's standing. Never raises on a missing row — absence is Free."""
    row = conn.execute(
        "SELECT tier, state, seats_included, reason, as_of, valid_through, grace_until"
        " FROM entitlement WHERE forge = ? AND account = ?",
        (forge, account),
    ).fetchone()
    if row is None:
        return Coverage(FREE, State.NONE, None, "no subscription on record", 0, None, None, False)
    tier, state, seats, reason, as_of, valid_through, grace_until = row
    return Coverage(
        tier=str(tier),
        # **AN UNRECOGNISED STATE IS NOT `ACTIVE`.** A value this build does not know came from a
        # newer billing service, and reading it as paid would hand out the paid tier on a typo.
        state=_BY_VALUE.get(str(state), State.NONE),
        seats_included=None if seats is None else int(seats),
        reason=str(reason or ""),
        as_of=int(as_of),
        valid_through=None if valid_through is None else int(valid_through),
        grace_until=None if grace_until is None else int(grace_until),
        stale=grace_until is not None and now > int(grace_until),
    )
