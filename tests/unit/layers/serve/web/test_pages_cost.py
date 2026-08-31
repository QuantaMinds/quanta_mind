"""What a repository's reviews cost, on the page, behind the same check as everything else.

WHAT: Drives `serve/web/pages.repository` with real review rows carrying real costs, and asserts
      the figure reaches the page and that another account cannot reach it.
WHY:  **SPLIT OUT OF `test_pages.py` WHEN THAT FILE HIT THE 200-LINE CAP**, and the concern is a
      real one rather than a convenient cut: these are the only tests here that put `review` rows
      into a tenant store, and the only ones about money.

      **A SECOND SURFACE WOULD BE A SECOND PLACE TO GET THE OWNERSHIP CHECK WRONG.** The cost
      report is shown inside `repository()`, behind the one `mine()` test, rather than on a route
      of its own. The last test holds that: it puts a cost on somebody else's repository and
      requires the page to stay `None`.
IMPORTS: pytest, quantamind.serve.web.pages, quantamind.store.{installations,tenancy,schema}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quantamind.serve.web import pages
from quantamind.store import installations, tenancy
from quantamind.store.schema import open_store

NOW = 1_700_000_000


def _install(root: Path, account: str, repo: str) -> None:
    owner, _, name = repo.partition("/")
    open_store(tenancy.store_for(root, owner, name)).close()
    conn = open_store(tenancy.shared(root, tenancy.ACCOUNTS))
    try:
        installations.record(conn, account, repo, at=NOW, eligible=True)
    finally:
        conn.close()


def _reviewed(root: Path, repo: str, *, requests: int, out: int) -> None:
    """Put one real review row, with a real cost, in the tenant's own store."""
    owner, _, name = repo.partition("/")
    conn = open_store(tenancy.store_for(root, owner, name))
    try:
        conn.execute(
            "INSERT INTO repo (host, name, first_seen) VALUES ('github.com', ?, ?)", (repo, NOW)
        )
        repo_id = int(conn.execute("SELECT id FROM repo WHERE name = ?", (repo,)).fetchone()[0])
        conn.execute(
            "INSERT INTO review (repo_id, pr_number, head_sha, created_at, fire_decision, "
            "  request_count, tokens_in, tokens_out) VALUES (?, 1, ?, ?, 0, ?, 0, ?)",
            (repo_id, "a" * 40, NOW, requests, out),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def root(tmp_path: Path) -> Path:
    _install(tmp_path, "dhanush", "acme/payments")
    _install(tmp_path, "someone-else", "rival/secret")
    return tmp_path


def test_the_repository_page_shows_what_its_reviews_cost(root: Path) -> None:
    """The value, not the presence of a heading: the figure has to come from the row."""
    _reviewed(root, "acme/payments", requests=3, out=6321)

    body = pages.repository(root, "dhanush", "acme/payments")

    assert body is not None
    assert "QuantaMind — cost, acme/payments" in body
    assert "6321" in body, "the recorded output tokens never reached the page"
    assert "Per BILLED review: 3.00 request(s), 6,321 output token(s)." in body


def test_a_repository_with_reviews_but_no_model_call_says_so_on_the_page(root: Path) -> None:
    """The two zeros reach the web view as different sentences, not one empty table."""
    _reviewed(root, "acme/payments", requests=0, out=0)

    body = pages.repository(root, "dhanush", "acme/payments")

    assert body is not None
    assert "none consulted a model" in body
    assert "not a cost of zero" in body


def test_the_cost_report_is_behind_the_same_ownership_check_as_the_others(root: Path) -> None:
    """Not just that the page refuses: that the figure appears on NO page this account can see."""
    _reviewed(root, "rival/secret", requests=9, out=99999)
    _reviewed(root, "acme/payments", requests=1, out=100)

    refused = pages.repository(root, "dhanush", "rival/secret")
    home = pages.home(root, "dhanush")
    own = pages.repository(root, "dhanush", "acme/payments")

    assert refused is None, "another account's repository page was served"
    assert "99999" not in home, f"another account's spend leaked onto the home page: {home}"
    assert own is not None and "99999" not in own, "another account's spend leaked onto our page"
    assert "rival/secret" not in home, "the existence of another account's repository was confirmed"
    assert "Per BILLED review: 1.00 request(s), 100 output token(s)." in own, (
        "our own figure stopped being shown, so the assertions above prove nothing"
    )
