"""`quantamind dashboard` — what we commented on, whether it merged, what production said.

WHAT: Loads settings, resolves the repository, and prints the outcome table for it.
WHY:  **THE ONE REPORT IN THIS PRODUCT THAT DOES NOT DEPEND ON A COMMENT BEING RIGHT.** Whether a
      finding was good is a judgement, and four blind pools put our raw findings at 66.7-82.1%
      wrong. Whether the change we pointed at later merged and later broke is an outcome, true
      regardless of how good the sentence was.
IMPORTS: render.dashboard, store.{lifecycle,schema}, types.settings. Rightmost layer.
CONSUMED BY: `serve/cli.py`.
"""

from __future__ import annotations

from pathlib import Path

from quantamind.render.dashboard import table
from quantamind.store.lifecycle import board
from quantamind.store.schema import open_store
from quantamind.types.settings import SettingsError, load


def run_dashboard(repo: str, limit: int) -> int:
    """`quantamind dashboard` — the outcome table for one repository."""
    try:
        settings = load()
    except SettingsError as exc:
        print(f"configuration error: {exc}")
        return 1
    path = Path(settings.database_path)
    if not path.exists():
        print(f"{path} does not exist; no reviews have been recorded.")
        return 1
    conn = open_store(path)
    try:
        found = conn.execute("SELECT id FROM repo WHERE name = ?", (repo,)).fetchone()
        if found is None:
            print(f"{repo} has no recorded reviews in {path}.")
            return 1
        print(table(board(conn, int(found[0]), limit), repo))
    finally:
        conn.close()
    return 0
