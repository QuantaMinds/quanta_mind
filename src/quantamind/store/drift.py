"""Compare the schema on disk to the one this build creates, because the version number cannot.

WHAT: `differences()` lists every way a stored database's schema differs from this build's DDL, and
      `SchemaDrift` is what `open_store()` raises when that list is non-empty.
WHY:  **`CREATE TABLE IF NOT EXISTS` is silent about a table that already exists with the wrong
      shape, and `SCHEMA_VERSION` is bumped by hand.** Together they let a store open cleanly while
      missing a column: `version()` reports a match, `create()` changes nothing, and the first wrong
      answer arrives later as data rather than as an error. A store opened under the wrong
      assumptions produces rankings wrong in ways nothing downstream can see.

      **The expected shape is DERIVED, not written down.** It comes from applying this build's DDL
      to a throwaway in-memory database and reading `sqlite_master` back, because a second
      hand-maintained copy of the schema is a second thing to forget to update — which is the
      failure this module exists to catch.
IMPORTS: store.schema (its DDL). Nothing to its right.
CONSUMED BY: store.schema.open_store.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path


class SchemaDrift(RuntimeError):
    """The tables on disk are not the tables this build creates, whatever the version says."""

    def __init__(self, path: Path, found: list[str]) -> None:
        self.path, self.found = path, found
        super().__init__(
            f"{path}: the stored schema is not the one this build creates — "
            f"{'; '.join(found[:4])}. Write a migration and bump SCHEMA_VERSION; "
            "the store is not opened."
        )


def shape(conn: sqlite3.Connection) -> dict[str, str]:
    """{object name: its CREATE statement}, as SQLite itself recorded it."""
    return {
        str(name): " ".join(str(sql).split())
        for name, sql in conn.execute("SELECT name, sql FROM sqlite_master WHERE sql IS NOT NULL")
        if not str(name).startswith("sqlite_")
    }


def expected() -> dict[str, str]:
    """What this build's DDL produces, read back from a throwaway database."""
    from quantamind.store.schema import TABLES

    probe = sqlite3.connect(":memory:")
    try:
        for ddl in TABLES:
            probe.execute(ddl)
        return shape(probe)
    finally:
        probe.close()


def fingerprint() -> str:
    """A stable digest of this build's schema, for cheap comparison and for logs."""
    want = expected()
    joined = "\n".join(f"{name}={want[name]}" for name in sorted(want))
    return hashlib.sha256(joined.encode()).hexdigest()[:16]


def differences(conn: sqlite3.Connection) -> list[str]:
    """Every way the stored schema differs from this build's. Empty means identical."""
    have, want = shape(conn), expected()
    out = [f"missing {name}" for name in sorted(set(want) - set(have))]
    out += [f"unexpected {name}" for name in sorted(set(have) - set(want))]
    out += [f"{name} differs" for name in sorted(set(have) & set(want)) if have[name] != want[name]]
    return out
