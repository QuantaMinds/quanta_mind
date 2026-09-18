"""One function per schema version, and the ledger that says which is which.

WHAT: `_to_3` through `_to_9`, `STEPS` mapping a version to the step that reaches it, and
      `MigrationFailed`, which every step raises and `migrate()` turns into a rollback.
WHY:  **SPLIT OUT OF `migrations/__init__.py` WHEN VERSION 9 PUSHED IT PAST THE 200-LINE CAP.**
      The steps and the machinery that runs them are read at different times: a step is written
      once and then only ever read as history, while `migrate()` is read by anyone debugging a
      store that will not open. Nothing moved but the text.

      **A STEP SELECTS ITS TABLES BY NAME, NEVER BY A SUBSTRING OF THE DDL.** `statements_for`
      raises when a name matches nothing, so a renamed table fails the build rather than stamping
      a version onto a store it did not change.
IMPORTS: store.{schema,tables}. Nothing to its right.
CONSUMED BY: `store/migrations/__init__.py`.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable

from quantamind.store.schema import statements_for
from quantamind.store.tables import TABLES


class MigrationFailed(RuntimeError):
    """Carries the step that failed and why. The store is left untouched."""

    def __init__(self, step: int, reason: str) -> None:
        super().__init__(f"migration to version {step} failed: {reason}")
        self.step = step
        self.reason = reason


def _to_3(conn: sqlite3.Connection) -> None:
    """Add `lifecycle` and `prod_signal`. Existing rows are untouched; nothing is backfilled.

    A review recorded before this step has no lifecycle row, and that is the honest state: we do
    not know whether it merged. Inventing 'unknown' rows would make an absence of evidence
    indistinguishable from an observation that said so.
    """
    for statement in TABLES:
        if "lifecycle" in statement or "prod_signal" in statement:
            conn.execute(statement)


def _to_5(conn: sqlite3.Connection) -> None:
    """Add `rule_check`. **Nothing is backfilled, and that is the whole safety argument.**

    A review recorded before this step was never checked against a declared rule, because no rule
    engine existed when it ran. Writing "passed" rows for it would manufacture a compliance history
    that never happened — and a compliance history is precisely the artefact somebody would later
    show a regulator. An absent row means we did not check; it must never mean the check passed.

    The table is created from `TABLES` rather than written out again here, so a migrated store is
    byte-identical to a fresh one — which `test_schema_golden.py` asserts.
    """
    for statement in TABLES:
        if "rule_check" in statement:
            conn.execute(statement)


def _to_6(conn: sqlite3.Connection) -> None:
    """Add `installation`. **Nothing is backfilled, and `eligible` stays NULL for every store.**

    A repository installed before this table existed was never assessed against the free-tier
    rules, because no assessment ran. Writing 1 would grant an entitlement nobody checked; writing
    0 would refuse a customer we never looked at. NULL is the only honest value, and
    `store/installations.entitled` reads it as "unknown" rather than as either.

    Created from `TABLES` rather than written out again, so a migrated store is byte-identical to
    a fresh one — which `test_schema_golden.py` asserts.
    """
    for statement in TABLES:
        if "installation" in statement:
            conn.execute(statement)


def _to_7(conn: sqlite3.Connection) -> None:
    """Add `account` and `session`. **No session survives a migration, and none is invented.**

    There were no accounts before this step, so there is nothing to backfill and nobody to grant a
    session to. A migration that created one would be issuing a credential nobody asked for.
    """
    for statement in TABLES:
        if "account" in statement or "session" in statement:
            conn.execute(statement)


def _to_4(conn: sqlite3.Connection) -> None:
    """Add `touch_watermark`. Nothing is backfilled, and that is what keeps it safe.

    A store migrated from 3 has a touch index but no watermark, which `run_review` reads as "no
    watermark, read everything" -- the behaviour it had before this table existed. Inventing a
    watermark from the newest `committed_at` would be the timestamp bug this table exists to
    prevent, written into the migration.
    """
    for statement in TABLES:
        if "touch_watermark" in statement:
            conn.execute(statement)


def _to_8(conn: sqlite3.Connection) -> None:
    """Add `subscription`. **Nothing is backfilled: a backfilled row is an invented payment.**

    No account had a subscription before this step, because nothing in this product had ever spoken
    to a payment processor -- `verify/tier_request.py` refused to let a verdict even claim one. So
    there is no prior state to carry forward, and writing any row here would be this product
    asserting that somebody paid us on the strength of a migration having run.

    An account with no row is reported as having no subscription, which is true of every account
    that existed when this step ran.

    Created from `TABLES` rather than written out again, so a migrated store is byte-identical to a
    fresh one -- which `tests/unit/layers/store/test_schema_golden.py` asserts.

    **IT SELECTS BY TABLE NAME, NOT BY A SUBSTRING OF THE DDL.** `if "subscription" in statement`
    was correct only for as long as no other table's text contained that word; `statements_for`
    matches the name and raises when a name matches nothing, so a renamed table fails the build
    instead of migrating to an empty store. Same end state, so a store already at 8 is unaffected.
    """
    try:
        statements = statements_for("subscription")
    except ValueError as exc:
        raise MigrationFailed(8, str(exc)) from None
    for statement in statements:
        conn.execute(statement)


def _to_9(conn: sqlite3.Connection) -> None:
    """Add `entitlement`, `seat_use` and `forge_installation`. **Nothing is backfilled.**

    An account installed before billing existed has no entitlement row, and `store/billing/
    entitlement.covering` reads that absence as Free. Inventing a tier here would either grant one
    nobody bought or withdraw one nobody cancelled, and the row would look deliberate either way.
    """
    try:
        statements = statements_for("entitlement", "seat_use", "forge_installation")
    except ValueError as exc:
        raise MigrationFailed(9, str(exc)) from None
    for statement in statements:
        conn.execute(statement)


STEPS: dict[int, Callable[[sqlite3.Connection], None]] = {
    3: _to_3,
    4: _to_4,
    5: _to_5,
    6: _to_6,
    7: _to_7,
    8: _to_8,
    9: _to_9,
}
