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

from quantamind.store import drift, schema, tenancy


@dataclass(frozen=True, slots=True)
class Health:
    """Whether we can serve, and if not, exactly what is wrong."""

    ok: bool
    detail: str

    def render(self) -> str:
        return f"{'ok' if self.ok else 'FAILING'}: {self.detail}"


def health(database_path: str) -> Health:
    """Whether every tenant store under this root is present, current and readable.

    Never raises: a liveness probe that throws gives an orchestrator a stack trace where it needed
    a verdict. Every failure becomes `ok=False` with the reason.

    **`database_path` IS A ROOT, NOT A FILE.** Each repository gets its own store —
    `store/tenancy.py` explains why — so a probe that opened one file would be checking one tenant
    and reporting for all of them. It checks the root is writable and then opens EVERY store it
    finds, because a version mismatch in one tenant is a tenant this build must not write to.

    **NO TENANTS IS HEALTHY AND SAYS SO.** A freshly installed service has no stores and is working
    perfectly; reporting that as a failure would make "nobody has installed us yet" and "our
    storage is broken" the same alarm. It is a named state, not a silent pass.
    """
    root = Path(database_path)
    # **THE ROOT IS NOT CREATED HERE, AND THAT IS THE POINT.** Creating it would make a typo in
    # `QUANTAMIND_DATABASE_PATH` produce a fresh empty root and a healthy verdict -- a process
    # pointed at the wrong place looking exactly like a working one. The original single-store
    # check refused to create a missing file for this reason and the reason did not change when
    # the path became a directory. Provisioning storage is the operator's step; `tenancy.store_for`
    # creates each tenant's directory only once a real delivery has authenticated.
    if not root.is_dir():
        return Health(
            False,
            f"no store root at {root}. Creating it here would make a wrong path look healthy, so "
            "this refuses instead: provision the directory as part of deployment",
        )
    try:
        probe = root / ".writable"
        probe.write_text("")
        probe.unlink()
    except OSError as exc:
        return Health(False, f"the store root {root} is not writable: {exc}")

    found = tenancy.tenants(root)
    if not found:
        return Health(
            True,
            f"no tenants yet under {root}; the root is writable at schema v{schema.SCHEMA_VERSION}",
        )

    for owner, name in found:
        path = tenancy.store_for(root, owner, name)
        try:
            conn = schema.open_store(path)
        except schema.SchemaVersionMismatch as exc:
            return Health(
                False, f"{owner}/{name}: schema mismatch, this build must not write: {exc}"
            )
        except drift.SchemaDrift as exc:
            return Health(
                False, f"{owner}/{name}: stored schema is not the one this build creates: {exc}"
            )
        except (sqlite3.Error, OSError) as exc:
            return Health(False, f"{owner}/{name}: store could not be opened: {exc}")
        try:
            # Reading a row proves the file is a working database, not merely a file that opened.
            conn.execute("SELECT COUNT(*) FROM repo").fetchone()
        except sqlite3.Error as exc:
            return Health(False, f"{owner}/{name}: store opened but could not be read: {exc}")
        finally:
            conn.close()
    return Health(
        True,
        f"{len(found)} tenant store(s) under {root} readable at schema v{schema.SCHEMA_VERSION}",
    )
