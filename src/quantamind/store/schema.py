"""The versioned SQLite schema, and the version gate that refuses to open a database it would break.

WHAT: `SCHEMA_VERSION`, the DDL for every table, `create()` to apply it, and `open_store()` which
      opens an existing database only when its version matches.
WHY:  **The outcome history is the asset.** Everything else here records what we did; `outcome`
      records whether it was right, and it accumulates over months of a customer's traffic. There
      is no delete-and-reindex path in production, so the schema is append-only and versioned, and
      opening a database written by a different version raises instead of guessing.

      **Three columns exist from the first row because append-only cannot backfill them:**

      - `shadow_pick` stores a RANKED LIST with scores and percentiles, never a top pick. The
        allocator funds ranks 1-3 and top-3 recall is what decides whether allocation loses
        defects — **top-3 for a candidate ranker cannot be computed from a top-1 record**, and the
        firing threshold cannot be re-derived without the percentile.
      - `request` stores token counts per call, including `cache_read_tokens`. **Cost is derived
        from them and never stored as cents**: prices change and token counts do not, cents cannot
        separate a cache read from fresh input, and they round away shallow calls costing fractions
        of a cent.
      - `outcome` carries `rule_version` and `fix_subject`, the inputs to re-derive it. The
        attribution rule has already been corrected once — file overlap to symbol overlap, which
        changed 67.9% of verdicts — and without a version stamp nobody can tell which rule labelled
        which row.

      **`ranked_unit` holds EVERY changed unit, including cold ones.** Cold rows are the coverage
      line's content and shadow evaluation's denominator; storing only the funded subset silently
      removes both.

      **No table stores source code.** `finding.body` quotes at most a few lines; `unit_path` and
      `unit_name` are identifiers. A telemetry table that accumulates customer source is a breach
      waiting for a date.
IMPORTS: types (nothing else; `store` sits second in the layer order).
CONSUMED BY: store.touches and every other store module; nothing outside `store/` opens a database.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from quantamind.store import drift
from quantamind.store.tables import TABLES

# Bump on ANY change to the DDL below, and write a migration. There is no in-place edit.
SCHEMA_VERSION = 7

# `finding` and `claim` exist because adding a table later is a migration, and the schema is
# append-only. NOTHING WRITES TO THEM: `infer/` is closed on evidence and publishes no findings.


class SchemaVersionMismatch(RuntimeError):
    """The database on disk was written by a different schema version.

    Raised rather than migrated silently. A store opened under the wrong assumptions produces
    rankings that are wrong in ways no test downstream can see.
    """

    def __init__(self, path: Path, found: int, expected: int) -> None:
        self.path, self.found, self.expected = path, found, expected
        super().__init__(
            f"{path}: schema version {found}, this build expects {expected}. "
            "Write a migration; there is no delete-and-reindex path."
        )


def create(conn: sqlite3.Connection) -> None:
    """Apply the schema to a connection and stamp its version. Safe to call on an applied store."""
    conn.execute("PRAGMA foreign_keys = ON")
    for ddl in TABLES:
        conn.execute(ddl)
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.commit()


def version(conn: sqlite3.Connection) -> int:
    """The schema version stamped on this database. Zero means never initialised."""
    row = conn.execute("PRAGMA user_version").fetchone()
    return int(row[0]) if row else 0


def open_store(path: Path) -> sqlite3.Connection:
    """Open or create the store at `path`, refusing a database this build would corrupt.

    A fresh file is created and stamped. An existing file whose version differs raises
    `SchemaVersionMismatch` — it is never migrated in place and never opened anyway.
    """
    fresh = not path.exists()
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    if fresh or version(conn) == 0:
        create(conn)
        return conn
    found = version(conn)
    if found != SCHEMA_VERSION:
        conn.close()
        raise SchemaVersionMismatch(path, found, SCHEMA_VERSION)
    # The version matching is not evidence the tables match: it is a number a human maintains.
    differences = drift.differences(conn)
    if differences:
        conn.close()
        raise drift.SchemaDrift(path, differences)
    return conn
