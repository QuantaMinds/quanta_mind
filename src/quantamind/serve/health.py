"""Liveness that fails when the store is unreachable, rather than when the process is alive.

WHAT: `health()` opens the store, checks it can be read, and returns a verdict naming what failed.
WHY:  **A health check that reports the process is running tells you what the request already
      told you.** It has to touch the thing that actually breaks — the store — or it is a check
      whose output is identical whether the system works or not.

      **It opens the store rather than pinging it**, because `store.schema.open_store` is where
      version mismatch and schema drift are caught. A liveness probe that skipped those would
      report healthy on a database this build cannot safely write to, which is the exact state a
      deploy produces.

      **It checks the store EXISTS before opening it, and that is not pedantry.** `open_store`
      creates a missing database, so the first version of this probe reported `ok=True` for a path
      that did not exist — a deploy pointed at the wrong directory would have created an empty
      store, answered healthy, and served rankings computed over no history at all. Found by a test
      asserting the failure, not by the probe.
IMPORTS: store (schema, drift), types (Settings). Rightmost layer.
CONSUMED BY: the HTTP binding, and any orchestrator that needs a readiness signal.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from quantamind.store import drift, schema


@dataclass(frozen=True, slots=True)
class Health:
    """Whether we can serve, and if not, exactly what is wrong."""

    ok: bool
    detail: str

    def render(self) -> str:
        return f"{'ok' if self.ok else 'FAILING'}: {self.detail}"


def health(database_path: str) -> Health:
    """Whether the store this build needs is present, current and readable.

    Never raises: a liveness probe that throws gives an orchestrator a stack trace where it needed
    a verdict. Every failure becomes `ok=False` with the reason.
    """
    path = Path(database_path)
    if not path.exists():
        return Health(
            False,
            f"no store at {path}. Opening would CREATE an empty one and answer healthy, so this "
            "refuses instead: a process pointed at the wrong path must not look like a working one",
        )
    try:
        conn = schema.open_store(path)
    except schema.SchemaVersionMismatch as exc:
        return Health(False, f"schema version mismatch, so this build must not write: {exc}")
    except drift.SchemaDrift as exc:
        return Health(False, f"the stored schema is not the one this build creates: {exc}")
    except sqlite3.Error as exc:
        return Health(False, f"the store at {path} could not be opened: {exc}")
    except OSError as exc:
        return Health(False, f"the store at {path} is unreachable: {exc}")

    try:
        # Reading a row proves the file is a working database, not merely a file that opened.
        conn.execute("SELECT COUNT(*) FROM repo").fetchone()
    except sqlite3.Error as exc:
        return Health(False, f"the store opened but could not be read: {exc}")
    finally:
        conn.close()
    return Health(True, f"store at {path} is readable at schema v{schema.SCHEMA_VERSION}")
