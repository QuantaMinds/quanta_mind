"""`quantamind migrate` — bring the stores up to this build's schema, deliberately.

WHAT: Loads settings, finds every store under `QUANTAMIND_DATABASE_PATH`, applies pending steps to
      each WITHOUT the version check, and reports what each one did. Any failure leaves that store
      exactly as it was and makes the command exit non-zero.
WHY:  **`open_store()` REFUSES A STORE AT THE WRONG VERSION RATHER THAN MIGRATING IT**, and that
      stays true. Migrating production data is an operator's decision made once against a backup,
      not something a process does because it happened to start -- so this is a command a person
      runs, and the only path to `store.migrations`.

      It connects with plain `sqlite3` rather than `open_store()` for the obvious reason: the store
      it is here to fix is exactly the one `open_store()` will not open.

      **IT MIGRATES EVERY STORE UNDER THE ROOT, AND UNTIL 2026-09-18 IT MIGRATED ONE FILE.**
      `QUANTAMIND_DATABASE_PATH` is a ROOT, not a database: `store/tenancy.py` puts `accounts.db`
      and `deliveries.db` beside the tenants and one `<owner>/<name>.db` per repository under it.
      The deployed service sets it to `/data/stores`, so the command did
      `sqlite3.connect("/data/stores")` against a DIRECTORY and died with an unhandled
      `OperationalError: unable to open database file`. **The documented way to migrate production
      could not migrate production**, and no test saw it because every test passed a single file.

      **A PARTIAL RUN IS REPORTED PER STORE AND IS SAFE TO REPEAT.** Each store is its own
      transaction and `migrations.pending()` returns nothing once a store is current, so re-running
      after a failure retries only what did not land. Stopping at the first failure would leave the
      operator guessing how much of a fleet moved.
IMPORTS: store.{migrations,tenancy}, types.settings. Rightmost layer.
CONSUMED BY: `serve/cli.py`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from quantamind.store import tenancy
from quantamind.store.migrations import MigrationFailed, migrate
from quantamind.types.settings import SettingsError, load


def stores_under(root: Path) -> list[Path]:
    """Every SQLite store this build owns beneath `root`, shared ones first.

    **A PLAIN FILE IS RETURNED AS ITSELF**, because a developer pointing the variable at one
    database is a real setup and refusing it would be a regression dressed as a fix.

    The shared stores come first deliberately: `accounts.db` is the one every request reads, so an
    operator watching the output learns the important store moved before the long tail of tenants.
    """
    if root.is_file():
        return [root]
    if not root.is_dir():
        return []
    found = [
        root / name for name in (tenancy.ACCOUNTS, tenancy.DELIVERIES) if (root / name).is_file()
    ]
    # **JOINED DIRECTLY, NOT THROUGH `tenancy.store_for`.** That function CREATES the owner
    # directory as a side effect, and a command whose job is to migrate what exists must not bring
    # a tenant into being by looking for one. `tenants()` already read these off the filesystem.
    found.extend(root / owner / f"{name}.db" for owner, name in tenancy.tenants(root))
    return found


def run_migrate() -> int:
    """`quantamind migrate` — apply pending schema steps to every configured store."""
    try:
        settings = load()
    except SettingsError as exc:
        print(f"configuration error: {exc}")
        return 1
    root = Path(settings.database_path)
    if not root.exists():
        print(f"{root} does not exist; nothing to migrate. It is created on first use.")
        return 0

    stores = stores_under(root)
    if not stores:
        # **NOT SILENCE, AND NOT SUCCESS EITHER.** An empty root is normal on a service that has
        # never been installed anywhere; a root spelled wrong looks exactly the same from here, so
        # the path is printed rather than left for the operator to infer from a bare "0 stores".
        print(f"[migrate] no stores under {root}; nothing to migrate.")
        return 0

    failed = 0
    for store in stores:
        conn = sqlite3.connect(store)
        try:
            done = migrate(conn)
        except MigrationFailed as exc:
            failed += 1
            print(f"[migrate] {store}: FAILED — {exc}")
            print(f"[migrate] {store}: left exactly as it was.")
            continue
        except sqlite3.Error as exc:
            # A file that is not a database, or one we cannot write. Named per store rather than
            # allowed to end the run: the rest of the fleet still needs migrating.
            failed += 1
            print(f"[migrate] {store}: FAILED — sqlite refused it: {exc}")
            continue
        finally:
            conn.close()
        print(f"[migrate] {store}: {done.sentence()}")

    print(f"[migrate] {len(stores) - failed}/{len(stores)} store(s) at this build's schema.")
    if failed:
        # **NON-ZERO, BECAUSE A DEPLOY SCRIPT READS THE EXIT CODE AND NOT THE LOG.** A partial
        # migration that exits 0 is a service that starts, refuses the stores that did not move,
        # and reports it nowhere the deploy could have caught.
        print(f"[migrate] {failed} store(s) did NOT move. Re-running retries only those.")
        return 1
    return 0
