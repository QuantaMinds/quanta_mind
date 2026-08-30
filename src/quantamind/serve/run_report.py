"""Print one repository's report — the outcome board, or the rule-compliance table.

WHAT: Loads settings, resolves the repository, and prints a report for it. `run_dashboard` is
      the outcome board; `run_compliance` is the rule table. Both do the same three things and
      differ only in what they render, so the resolution lives once in `_for_repo`.

      **THE STORE IS RESOLVED THROUGH `tenancy`, WHICH IT WAS NOT.** `database_path` is the
      tenancy ROOT -- `<root>/<owner>/<name>.db` -- to `review_delivery` and `health`, and this
      module still opened it as a single file. On any real deployment that is a directory, so
      `quantamind dashboard` raised `sqlite3.OperationalError: unable to open database file`
      rather than reporting anything. Found by building `compliance` on top of it and running it.

      **`store_for` IS CALLED ONLY AFTER THE TENANT IS KNOWN TO EXIST**, because it creates the
      directory. A read path that provisioned storage would answer "no reviews" while quietly
      inventing a tenant.
WHY:  **THE ONE REPORT IN THIS PRODUCT THAT DOES NOT DEPEND ON A COMMENT BEING RIGHT.** Whether a
      finding was good is a judgement, and four blind pools put our raw findings at 66.7-82.1%
      wrong. Whether the change we pointed at later merged and later broke is an outcome, true
      regardless of how good the sentence was.
IMPORTS: render.{dashboard,compliance_table}, store.{lifecycle,compliance,schema},
      types.settings.
      Rightmost layer.
SEE ALSO: `docs/plans/product/product-build.md` D5 — per repository, never per developer.
CONSUMED BY: `serve/cli.py`.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path

from quantamind.render.compliance_table import table as rule_table
from quantamind.render.dashboard import table
from quantamind.store import tenancy
from quantamind.store.compliance import standing
from quantamind.store.lifecycle import board
from quantamind.store.schema import open_store
from quantamind.types.settings import SettingsError, load


def _for_repo(repo: str, report: Callable[[sqlite3.Connection, int], str]) -> int:
    """Resolve settings, store and repository, then print what `report` builds. Shared on purpose.

    **A MISSING STORE AND A MISSING REPOSITORY ARE DIFFERENT ANSWERS**, and both are different
    from an empty report: "no reviews recorded" is a fact about this installation, not a clean
    compliance record.
    """
    try:
        settings = load()
    except SettingsError as exc:
        print(f"configuration error: {exc}")
        return 1
    root = Path(settings.database_path)
    if not root.is_dir():
        print(f"no store root at {root}; no reviews have been recorded.")
        return 1
    owner, _, name = repo.partition("/")
    if (owner, name) not in tenancy.tenants(root):
        print(f"{repo} has no store under {root}.")
        return 1
    conn = open_store(tenancy.store_for(root, owner, name))
    try:
        found = conn.execute("SELECT id FROM repo WHERE name = ?", (repo,)).fetchone()
        if found is None:
            print(f"{repo} has a store but no recorded reviews in it.")
            return 1
        print(report(conn, int(found[0])))
    finally:
        conn.close()
    return 0


def run_dashboard(repo: str, limit: int) -> int:
    """`quantamind dashboard` — the outcome table for one repository."""
    return _for_repo(repo, lambda conn, repo_id: table(board(conn, repo_id, limit), repo))


def run_compliance(repo: str) -> int:
    """`quantamind compliance` — every declared rule and what happened to it."""
    return _for_repo(repo, lambda conn, repo_id: rule_table(standing(conn, repo_id), repo))
