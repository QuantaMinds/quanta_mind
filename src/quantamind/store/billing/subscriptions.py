"""One account's subscription as Stripe last told us, and the refusal that keeps it current.

WHAT: `record(conn, subscription)` writes one row and returns what it did; `current(conn, account)`
      reads the account's subscription, or None; `Recorded` says whether the write landed and why
      it did not.
WHY:  **STRIPE DOES NOT GUARANTEE DELIVERY ORDER, AND THE ROW THIS PROTECTS IS AN ENTITLEMENT.**
      A `customer.subscription.updated` carrying `canceled` can arrive after the `active` that
      superseded it -- a retry of an older event, or two deliveries racing through the same socket.
      A plain upsert would take the last one to arrive and switch off a live customer, and nothing
      downstream could tell that from a genuine cancellation. So the write carries Stripe's own
      `created` and an older event does not overwrite a newer one.

      **THE REFUSAL IS RETURNED, NEVER SILENT.** `AGENTS.md` rule 14 asks what a check outputs when
      the thing it checks is broken; if a stale write and a fresh write both returned None, the
      ordering guard would be indistinguishable from an ordering guard that does nothing. `Recorded`
      carries `stored` and the reason, the caller logs it, and the sabotage in
      `docs/plans/feat-stripe-checkout-and-entitlement.md` can tell a working guard from a deleted
      one.

      **NOTHING HERE PARSES A WEBHOOK.** It takes a `types/billing.Subscription`, which is a record
      built from an authenticated delivery. A store module that knew Stripe's payload shape would
      be the place somebody later writes a row from a request body, which is the one thing the
      whole row exists to prevent.

      **THE ACCOUNT IS A GITHUB LOGIN AND THE KEY IS `(account, subscription_id)`.** One account
      can hold more than one subscription over time -- they cancel, they come back -- and a key of
      `account` alone would erase the first one, which is the record that they were ever a
      customer. `current()` picks the newest by Stripe's timestamp.
IMPORTS: stdlib sqlite3, and `types/billing.py`. The store layer reads types and nothing else.
CONSUMED BY: `serve/web/billing_route.py`, and `verify/tier_request.py` through its caller.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from quantamind.types.billing import Standing, Subscription, standing

COLUMNS = (
    "account, subscription_id, customer_id, price_id, standing, seats, "
    "amount_cents, currency, current_period_end, event_at"
)


@dataclass(frozen=True, slots=True)
class Recorded:
    """What `record()` did. **A refusal is a result, not a silence.**"""

    stored: bool
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.stored and not self.reason:
            raise ValueError("a refused write must say why; a caller cannot log 'False'")


def record(conn: sqlite3.Connection, subscription: Subscription) -> Recorded:
    """Write one subscription. **An event older than the stored one is refused, not applied.**

    Idempotent on a redelivery: Stripe retries the same event for three days, and re-applying an
    event with the same `event_at` writes the same values, so the `>=` is deliberate. It is `>=`
    rather than `>` so that a redelivery repairs a row somebody edited by hand, which is the only
    way the two can disagree.
    """
    if not subscription.account.strip():
        raise ValueError(
            f"a subscription needs the account it belongs to, got {subscription.account!r}. "
            "It is carried through checkout as client_reference_id; an empty one means the "
            "session was created without it and the payment cannot be attributed."
        )
    cursor = conn.execute(
        f"INSERT INTO subscription ({COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(account, subscription_id) DO UPDATE SET"
        " customer_id = excluded.customer_id, price_id = excluded.price_id,"
        " standing = excluded.standing, seats = excluded.seats,"
        " amount_cents = excluded.amount_cents, currency = excluded.currency,"
        " current_period_end = excluded.current_period_end, event_at = excluded.event_at"
        " WHERE excluded.event_at >= subscription.event_at",
        (
            subscription.account,
            subscription.subscription_id,
            subscription.customer_id,
            subscription.price_id,
            subscription.standing.value,
            subscription.seats,
            subscription.amount_cents,
            subscription.currency,
            subscription.current_period_end,
            subscription.event_at,
        ),
    )
    conn.commit()
    if cursor.rowcount:
        return Recorded(True)
    held = conn.execute(
        "SELECT event_at, standing FROM subscription WHERE account = ? AND subscription_id = ?",
        (subscription.account, subscription.subscription_id),
    ).fetchone()
    # **THE STORED EVENT IS NAMED IN THE REASON.** "Out of order" alone sends an operator to
    # Stripe's dashboard to work out which two events raced; the timestamps say it here.
    return Recorded(
        False,
        f"event at {subscription.event_at} is older than the stored {held[0]} "
        f"({held[1]}), so it was not applied"
        if held
        else f"the write affected no row and none is stored for "
        f"{subscription.account}/{subscription.subscription_id}",
    )


def _row(row: tuple[object, ...]) -> Subscription:
    """One database row as a `Subscription`. **An unknown standing raises**; see `types/billing`."""
    return Subscription(
        account=str(row[0]),
        subscription_id=str(row[1]),
        customer_id=str(row[2]),
        price_id=str(row[3]),
        standing=standing(str(row[4])),
        # **`int(str(...))`, NOT A CAST OR AN IGNORE.** `fetchone()` is typed as returning
        # objects, and silencing that with `Any` would also silence a column that came back as
        # text after a migration went sideways. Going through `str` converts what is actually
        # there and raises on anything that is not a number.
        seats=int(str(row[5])),
        amount_cents=int(str(row[6])),
        currency=str(row[7]),
        current_period_end=int(str(row[8])),
        event_at=int(str(row[9])),
    )


def current(conn: sqlite3.Connection, account: str) -> Subscription | None:
    """The account's newest subscription, or None when it has never had one.

    **None MEANS "NEVER HAD ONE", WHICH IS NOT "CANCELLED".** A cancelled subscription is a row
    with `Standing.CANCELED` and the caller can see the date; returning None for both would make an
    account that left indistinguishable from one that never arrived, and those are different
    answers to a customer asking why they were charged.
    """
    row = conn.execute(
        f"SELECT {COLUMNS} FROM subscription WHERE account = ? ORDER BY event_at DESC LIMIT 1",
        (account,),
    ).fetchone()
    return None if row is None else _row(row)


def paid(conn: sqlite3.Connection, account: str) -> tuple[bool, str]:
    """Whether the account is paying, and the sentence saying how we know. Never a bare bool.

    The sentence is returned rather than logged here because this module cannot know whether the
    caller is answering an operator, a route or a test, and a store that prints is a store that
    prints during `just check`.
    """
    held = current(conn, account)
    if held is None:
        return False, f"{account} has no subscription on record"
    if held.standing is Standing.PAST_DUE:
        # **NAMED SEPARATELY BECAUSE IT IS THE ONE A HUMAN SHOULD SEE.** Everything else is a
        # settled state; this one is a customer whose card is being retried right now.
        return False, (
            f"{account} is past due, paid through {held.current_period_end}; "
            f"Stripe is retrying and has not given up"
        )
    return held.paid, held.sentence()
