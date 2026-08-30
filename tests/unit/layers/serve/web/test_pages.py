"""Verification that an account sees its own repositories and cannot ask for anybody else's.

WHAT: Drives `serve/web/pages` against real tenant stores — the list, one repository's reports,
      and the two ways a request for somebody else's repository can be answered.
WHY:  **THE PATH IS WHATEVER THE BROWSER SENDS.** `/r/acme/payments` is a claim, not a
      permission. `mine()` answers from the installation rows instead, and `repository()` returns
      None for a repository this account did not install — the same None as one that does not
      exist, because a different answer would confirm it is there.

      **AND EVERY NAME ON THE PAGE COMES FROM SOMEBODY ELSE.** A repository name arrives from
      GitHub. The escaping test uses a name carrying a script tag, because a page that
      interpolates it raw is an injection and nothing else in the suite would notice.

      **A REMOVED INSTALLATION DISAPPEARS FROM THE LIST**, which is the visible half of B5: a
      withdrawn customer stops seeing their repository, not merely stops being reviewed.
IMPORTS: pytest, quantamind.serve.web.pages, quantamind.store.*.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quantamind.serve.web import pages
from quantamind.store import installations, tenancy
from quantamind.store.schema import open_store
from quantamind.store.tenancy import TenantRefused

NOW = 1_700_000_000


def _install(root: Path, account: str, repo: str, *, removed: bool = False) -> None:
    """Record an installation where it now lives: once, beside the tenants."""
    owner, _, name = repo.partition("/")
    # **THE TENANT FILE IS CREATED, NOT JUST ITS DIRECTORY.** `store_for` makes the directory and
    # leaves the file absent, so `tenants()` — which globs `<root>/<owner>/*.db` — found NOTHING
    # and the open-count test below passed against an empty loop. A fixture with no tenants cannot
    # show that listing an account stopped reading every tenant.
    open_store(tenancy.store_for(root, owner, name)).close()
    conn = open_store(tenancy.shared(root, tenancy.ACCOUNTS))
    try:
        installations.record(conn, account, repo, at=NOW, eligible=True)
        if removed:
            installations.withdraw(conn, repo, at=NOW + 10)
    finally:
        conn.close()


@pytest.fixture
def root(tmp_path: Path) -> Path:
    _install(tmp_path, "dhanush", "acme/payments")
    _install(tmp_path, "dhanush", "acme/ledger")
    _install(tmp_path, "someone-else", "rival/secret")
    return tmp_path


def test_an_account_sees_only_its_own_repositories(root: Path) -> None:
    assert pages.mine(root, "dhanush") == ["acme/ledger", "acme/payments"]


def test_another_account_sees_only_theirs(root: Path) -> None:
    """The control. Without it, `mine` could return everything and the test above still pass."""
    assert pages.mine(root, "someone-else") == ["rival/secret"]


def test_an_account_with_nothing_installed_sees_an_empty_list(root: Path) -> None:
    assert pages.mine(root, "a-stranger") == []


def test_a_removed_installation_leaves_the_list(root: Path) -> None:
    _install(root, "dhanush", "acme/gone", removed=True)

    assert "acme/gone" not in pages.mine(root, "dhanush")


def test_the_home_page_names_the_signed_in_account_and_links_each_repository(root: Path) -> None:
    body = pages.home(root, "dhanush")

    assert "Signed in as dhanush" in body
    assert 'href="/r/acme/payments"' in body
    assert "rival/secret" not in body, "another account's repository reached the page"


def test_an_account_with_nothing_is_told_so_rather_than_shown_an_empty_page(root: Path) -> None:
    assert "No repository is installed" in pages.home(root, "a-stranger")


def test_somebody_elses_repository_answers_exactly_as_a_nonexistent_one(root: Path) -> None:
    """The property that matters, and it is INDISTINGUISHABILITY rather than refusal.

    A path is a claim, not a permission. If "not yours" and "does not exist" gave different
    answers, the difference would confirm to somebody that a repository is there — so the test
    compares the two answers to each other rather than each to None.
    """
    theirs = pages.repository(root, "dhanush", "rival/secret")
    absent = pages.repository(root, "dhanush", "nobody/nothing")
    owned = pages.repository(root, "dhanush", "acme/payments")

    assert theirs == absent, "the two answers differ, which tells a visitor the repository exists"
    assert theirs is None
    assert owned is not None, "the control: a repository this account owns still renders"


def test_a_repository_with_no_reviews_says_so(root: Path) -> None:
    body = pages.repository(root, "dhanush", "acme/payments")

    assert body is not None
    assert "Nothing has been reviewed" in body


def test_a_repository_name_carrying_markup_never_becomes_a_tenant(tmp_path: Path) -> None:
    """It cannot reach the page, because it cannot reach the disk.

    Written expecting to assert escaping and it refuses earlier than that: `store/tenancy.py`
    accepts `^[A-Za-z0-9][A-Za-z0-9._-]*$` and nothing else, so a name carrying markup is turned
    away at the storage boundary rather than rendered safely. Recorded as the real behaviour --
    a test asserting escaping here would have described a path that does not exist.
    """
    with pytest.raises(TenantRefused):
        _install(tmp_path, "dhanush", "acme/<script>alert(1)</script>")


def test_the_signed_in_login_is_escaped_too(root: Path) -> None:
    """The login comes from GitHub as well, and reaches the page in prose rather than a link."""
    body = pages.home(root, "<img src=x onerror=alert(1)>")

    assert "<img src=x" not in body
    assert "&lt;img" in body


def test_listing_an_account_opens_one_store_not_one_per_tenant(root: Path) -> None:
    """The fix. It was O(tenants) per page load; a hundred repositories meant a hundred opens.

    Counted rather than asserted in prose, because "it is faster now" is the kind of claim that
    survives a regression. The opener is the seam: `mine` may open the account store and nothing
    else, however many tenants exist beside it.
    """
    opened: list[Path] = []

    def counting(path: Path):
        opened.append(path)
        return open_store(path)

    _install(root, "dhanush", "acme/third")
    _install(root, "dhanush", "acme/fourth")

    pages.mine(root, "dhanush", opener=counting)

    assert len(opened) == 1, f"opened {len(opened)} stores to list one account"
    assert opened[0].name == tenancy.ACCOUNTS


def test_the_shared_layout_refuses_a_name_it_does_not_define(root: Path) -> None:
    """`shared()` takes a name this layout names, never caller text that could escape the root."""
    with pytest.raises(TenantRefused):
        tenancy.shared(root, "../../etc/passwd")
