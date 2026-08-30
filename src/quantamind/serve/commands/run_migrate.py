"""`quantamind migrate` — bring an existing store up to this build's schema, deliberately.

WHAT: Loads settings, opens the configured store WITHOUT the version check, applies pending steps,
      and reports which ran. Leaves the store untouched on any failure.
WHY:  **`open_store()` REFUSES A STORE AT THE WRONG VERSION RATHER THAN MIGRATING IT**, and that
      stays true. Migrating production data is an operator's decision made once against a backup,
      not something a process does because it happened to start -- so this is a command a person
      runs, and the only path to `store.migrations`.

      It connects with plain `sqlite3` rather than `open_store()` for the obvious reason: the store
      it is here to fix is exactly the one `open_store()` will not open.
IMPORTS: store.migrations, types.settings. Rightmost layer.
CONSUMED BY: `serve/cli.py`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from quantamind.store.migrations import MigrationFailed, migrate
from quantamind.types.settings import SettingsError, load


def run_migrate() -> int:
    """`quantamind migrate` — apply pending schema steps to the configured store.

    Separate from `serve` and from `review` on purpose: `open_store()` refuses a store at the wrong
    version rather than migrating it, because migrating production data is an operator's decision
    made once against a backup, not something a process does because it happened to start.
    """
    try:
        settings = load()
    except SettingsError as exc:
        print(f"configuration error: {exc}")
        return 1
    path = Path(settings.database_path)
    if not path.exists():
        print(f"{path} does not exist; nothing to migrate. It is created on first use.")
        return 0
    conn = sqlite3.connect(path)
    try:
        done = migrate(conn)
    except MigrationFailed as exc:
        print(f"[migrate] {exc}\n[migrate] the store was left as it was.")
        return 1
    finally:
        conn.close()
    print(f"[migrate] {done.sentence()}")
    return 0
