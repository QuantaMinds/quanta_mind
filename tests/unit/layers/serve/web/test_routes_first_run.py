"""The dashboard on a root that has never had an installation — the first thing an operator sees.

WHAT: Drives `serve/web/routes.get` against a store root that does not exist, for both browser
      paths, and asserts a page comes back and no store is created by the read.
WHY:  **THIS DROPPED THE CONNECTION.** `open_store` raised `sqlite3.OperationalError` on the
      missing `accounts.db`, and `do_GET` had no guard, so the stdlib handler closed the socket
      with no status at all. Reproduced against a real server: `GET /` returned nothing, while
      `GET /nonexistent` correctly returned 404 — so the working path failed and the broken path
      worked, which is why it read as "no such path" rather than as a crash.

      **AND IT MUST NOT BE FIXED BY CREATING THE STORE.** A read that provisions what it reads
      would leave a database behind for every visitor, including one who never signs in.
IMPORTS: pytest, quantamind.serve.web.routes, quantamind.types.settings.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

from quantamind.serve.web import routes
from quantamind.types.settings import Settings


def test_the_dashboard_answers_before_any_account_store_exists(tmp_path: Path) -> None:
    absent = tmp_path / "never-created"

    reply = routes.get("/", "", Settings(database_path=str(absent)))

    assert reply.status == 200, f"a fresh install dropped the connection, got {reply.status}"
    assert "sign in" in reply.body.lower(), reply.body[:200]
    assert not absent.exists(), (
        "reading the dashboard provisioned a store; every visitor would leave one behind"
    )


def test_a_repository_path_also_answers_before_any_account_store_exists(tmp_path: Path) -> None:
    absent = tmp_path / "never-created"

    reply = routes.get("/r/acme/widgets", "", Settings(database_path=str(absent)))

    assert reply.status == 200, f"got {reply.status}"
    assert not absent.exists()


def test_an_unknown_path_is_still_a_404(tmp_path: Path) -> None:
    """The contrast that made the original bug confusing: the broken path answered correctly."""
    reply = routes.get("/dashboard", "", Settings(database_path=str(tmp_path / "never-created")))

    assert reply.status == 404
