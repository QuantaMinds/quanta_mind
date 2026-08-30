"""Move a store from an older schema to this build's, one recorded step at a time.

WHAT: `pending(found)` lists the steps between a stored version and `SCHEMA_VERSION`.
      `migrate(conn)` applies them in a transaction and returns which ran. `STEPS` is the ledger.
WHY:  **`open_store()` REFUSES A STORE AT THE WRONG VERSION AND DOES NOT MIGRATE IT**, which is
      deliberate and stays that way. Migration is an operator's decision made once against a
      backup, not something a process does to production data because it happened to start. So
      this is reached only through `quantamind migrate`.

      **EACH STEP MUST LEAVE THE STORE IDENTICAL TO A FRESHLY CREATED ONE, AND THAT IS CHECKED
      RATHER THAN INTENDED.** `drift.differences()` runs at the end of `migrate()` and the
      transaction is rolled back if it reports anything. A migration that half-works produces a
      store whose version says one thing and whose tables say another -- exactly what `drift`
      exists to catch, arriving from the one direction that could create it deliberately.

      **STEP 2 -> 3 ADDS TABLES AND ALTERS NOTHING.** `ALTER TABLE ADD COLUMN` produces DDL text
      that differs from a fresh `CREATE` in ways nobody predicts -- SQLite splices the column in
      before the `UNIQUE` clause, on whatever line that lands on. The new facts therefore live in
      new tables, which is also the better model: `review` records a decision made at one instant,
      `lifecycle` and `prod_signal` record facts that arrive later and change.
IMPORTS: store.{drift,schema}. Nothing to its right.
CONSUMED BY: `serve/cli.py` behind `quantamind migrate`.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

from quantamind.store import drift
from quantamind.store.schema import SCHEMA_VERSION, version
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


STEPS: dict[int, Callable[[sqlite3.Connection], None]] = {3: _to_3, 4: _to_4, 5: _to_5, 6: _to_6}


@dataclass(frozen=True, slots=True)
class Migrated:
    """Which steps ran, and the version the store is at now."""

    steps: tuple[int, ...]
    version: int

    def sentence(self) -> str:
        if not self.steps:
            return f"already at version {self.version}; nothing to do"
        ran = ", ".join(str(s) for s in self.steps)
        return f"applied step(s) {ran}; store is at version {self.version}"


def pending(found: int) -> tuple[int, ...]:
    """Steps between `found` and this build's version. Empty when there is nothing to do."""
    if found > SCHEMA_VERSION:
        raise MigrationFailed(
            found,
            f"the store is at version {found} and this build creates {SCHEMA_VERSION}. "
            f"A newer store opened by an older build is not a migration, it is a downgrade, "
            f"and there is no path back.",
        )
    return tuple(step for step in sorted(STEPS) if found < step <= SCHEMA_VERSION)


def migrate(conn: sqlite3.Connection) -> Migrated:
    """Apply every pending step, or leave the store exactly as it was.

    The drift check at the end is the point: a step that runs without raising has still failed if
    the result is not what this build creates.
    """
    found = version(conn)
    steps = pending(found)
    if not steps:
        return Migrated((), found)

    try:
        for step in steps:
            missing = STEPS.get(step)
            if missing is None:
                raise MigrationFailed(step, "no step is recorded for this version")
            missing(conn)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        differences = drift.differences(conn)
        if differences:
            raise MigrationFailed(
                steps[-1],
                f"the migrated store does not match what this build creates: "
                f"{'; '.join(differences[:4])}",
            )
    except Exception:
        conn.rollback()
        raise
    conn.commit()
    return Migrated(steps, SCHEMA_VERSION)
