"""What a signed-in person sees: their repositories, and one repository's two reports.

WHAT: `home(conn_for, login)` lists the repositories an account installed. `repository(...)`
      renders one repository's compliance table and outcome board. Both return HTML.
WHY:  **AN ACCOUNT SEES ITS OWN REPOSITORIES AND NOTHING ELSE, AND THAT IS CHECKED PER REQUEST.**
      The path carries an owner and a name, and a path is whatever the browser sends. `mine()`
      answers from the installation rows rather than from the URL, so asking for somebody else's
      repository returns the same 404 as asking for one that does not exist — a different answer
      would confirm it exists.

      **THE TWO REPORTS ARE THE CLI'S, SHOWN RATHER THAN REBUILT.** `quantamind compliance` and
      `quantamind dashboard` already decide what those tables say. A second rendering would be a
      second judgement, and the one that drifts.

      **IT IS ONE QUERY, AND IT WAS O(TENANTS).** `installation` rows were written beside the
      tenant they named, so listing an account meant opening every tenant store on every page.
      An installation is an account-level fact; it now lives once, in the store beside the
      tenants, and the list is a single indexed read.
IMPORTS: render.{page,dashboard,compliance_table}, store.{compliance,installations,lifecycle}.
CONSUMED BY: `serve/web/routes.py`.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path

from quantamind.render import page as html
from quantamind.render.compliance_table import table as rule_table
from quantamind.render.dashboard import table as outcome_table
from quantamind.store import tenancy
from quantamind.store.compliance import standing
from quantamind.store.lifecycle import board
from quantamind.store.schema import open_store

BOARD_LIMIT = 100
Opener = Callable[[Path], sqlite3.Connection]


def mine(root: Path, login: str, *, opener: Opener = open_store) -> list[str]:
    """Every repository this account installed and has not removed, sorted.

    **THE ANSWER COMES FROM THE INSTALLATION ROWS, NEVER FROM THE PATH.** A browser controls the
    path; it does not control what an account installed.
    """
    conn = opener(tenancy.shared(root, tenancy.ACCOUNTS))
    try:
        rows = conn.execute(
            "SELECT repo FROM installation WHERE account = ? AND removed_at IS NULL ORDER BY repo",
            (login,),
        ).fetchall()
    finally:
        conn.close()
    return [str(row[0]) for row in rows]


def home(root: Path, login: str, *, opener: Opener = open_store) -> str:
    """The list. An account with nothing installed is told so, not shown an empty page."""
    repos = mine(root, login, opener=opener)
    body = [f"<h1>QuantaMind</h1><p>Signed in as {html.escaped(login)}.</p>"]
    if not repos:
        body.append(
            "<p>No repository is installed on this account yet. Installing the GitHub App on a "
            "repository is what puts it here.</p>"
        )
    else:
        items = "".join(f"<li>{html.link('/r/' + repo, repo)}</li>" for repo in repos)
        body.append(f"<h2>{len(repos)} repository(ies)</h2><ul>{items}</ul>")
    return html.page("QuantaMind", "".join(body))


def repository(root: Path, login: str, repo: str, *, opener: Opener = open_store) -> str | None:
    """One repository's two reports, or None when it is not this account's.

    **None IS THE SAME ANSWER FOR "NOT YOURS" AND "DOES NOT EXIST".** Distinguishing them would
    confirm the existence of a repository to somebody who may not know it is there.
    """
    if repo not in mine(root, login, opener=opener):
        return None
    owner, _, name = repo.partition("/")
    conn = opener(tenancy.store_for(root, owner, name))
    try:
        found = conn.execute("SELECT id FROM repo WHERE name = ?", (repo,)).fetchone()
        if found is None:
            reports = "<p>Nothing has been reviewed on this repository yet.</p>"
        else:
            repo_id = int(found[0])
            reports = html.pre(rule_table(standing(conn, repo_id), repo)) + html.pre(
                outcome_table(board(conn, repo_id, BOARD_LIMIT), repo)
            )
    finally:
        conn.close()
    return html.page(
        repo,
        f"<p>{html.link('/', '← all repositories')}</p><h1>{html.escaped(repo)}</h1>{reports}",
    )
