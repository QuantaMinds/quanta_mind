"""Reconciliation heals the drift a dropped removal delivery leaves behind.

WHAT: `stale()` exhaustively, and `reconcile()` against a REAL store with the forge listing
      injected, for the cases where the forge DID answer.
WHY:  **THE DANGEROUS DIRECTION IS THE ONE WITHOUT A CUSTOMER TO COMPLAIN.** Failing to withdraw
      costs us a review we are not paid for and somebody eventually notices. Withdrawing wrongly
      stops a paying customer's reviews with no error anywhere — the endpoint is healthy, the
      comment simply never arrives. So the "could not ask" cases outnumber the happy path here on
      purpose.

      **AN EMPTY LISTING IS THE ONE THAT WOULD HAVE BEEN CATASTROPHIC.** A parsing mistake that
      returned `()` would, on a naive set difference, withdraw every repository of every account
      in one run. It is treated as a failure to ask, and `test_an_empty_listing_withdraws_nothing`
      is what holds that.

      **THE REFUSAL HALF IS ITS OWN FILE** — `reconcile/test_refuses.py`. Every case here has an
      answer from the forge; every case there does not, and the two are opposite obligations.

      Sabotage to check this file works: make `stale()` compare bare names against full names and
      `test_a_dropped_removal_is_healed` fails.
IMPORTS: quantamind.serve.reconcile, quantamind.ingest.installation_scope,
      quantamind.store.{installations,schema,tenancy},
      quantamind.types.settings.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from quantamind.ingest.installation_scope import NotInstalled
from quantamind.serve.reconcile import reconcile, stale
from quantamind.store import installations, schema, tenancy
from quantamind.types.settings import Settings


def _settings(root: Path) -> Settings:
    return Settings(database_path=str(root))


def _conn(root: Path) -> sqlite3.Connection:
    return schema.open_store(tenancy.shared(root, tenancy.ACCOUNTS))


def _installed(root: Path, account: str, repos: list[str]) -> None:
    conn = _conn(root)
    try:
        for repo in repos:
            installations.record(conn, account, repo, at=1_700_000_000, eligible=True)
    finally:
        conn.close()


def _may_review(root: Path, repo: str) -> bool:
    conn = _conn(root)
    try:
        return installations.entitled(conn, repo).may_review
    finally:
        conn.close()


# ---------------------------------------------------------------- the pure comparison


@pytest.mark.parametrize(
    ("held", "listed", "expected"),
    [
        (("a/one", "a/two"), ("a/one", "a/two"), ()),
        (("a/one", "a/two"), ("a/one",), ("a/two",)),
        (("a/one",), ("a/one", "a/three"), ()),
        (("a/b", "a/c", "a/d"), ("a/c",), ("a/b", "a/d")),
    ],
)
def test_stale_names_only_what_we_hold_and_the_forge_does_not(
    held: tuple[str, ...], listed: tuple[str, ...], expected: tuple[str, ...]
) -> None:
    """A repository the forge lists that we do not hold is not our business to act on."""
    assert stale(held, listed) == expected


# ---------------------------------------------------------------- the drift it exists to find


def test_a_dropped_removal_is_healed(tmp_path: Path) -> None:
    """The case a missed `installation_repositories.removed` delivery leaves behind."""
    _installed(tmp_path, "acme", ["acme/widget", "acme/gadget"])

    report = reconcile(_settings(tmp_path), lambda probe: ("acme/widget",))

    assert _may_review(tmp_path, "acme/gadget") is False
    assert _may_review(tmp_path, "acme/widget") is True
    assert report.withdrawn == 1
    assert report.accounts[0].withdrawn == ("acme/gadget",)


def test_nothing_drifted_means_nothing_moves(tmp_path: Path) -> None:
    _installed(tmp_path, "acme", ["acme/widget", "acme/gadget"])

    report = reconcile(_settings(tmp_path), lambda probe: ("acme/widget", "acme/gadget"))

    assert report.withdrawn == 0
    assert _may_review(tmp_path, "acme/widget") is True
    assert _may_review(tmp_path, "acme/gadget") is True


def test_an_uninstalled_account_is_withdrawn_whole(tmp_path: Path) -> None:
    """`NotInstalled` is the one error that removes anything, and it removes everything."""
    _installed(tmp_path, "acme", ["acme/widget", "acme/gadget"])

    def gone(probe: str) -> tuple[str, ...]:
        raise NotInstalled("404")

    report = reconcile(_settings(tmp_path), gone)

    assert _may_review(tmp_path, "acme/widget") is False
    assert _may_review(tmp_path, "acme/gadget") is False
    assert report.accounts[0].gone is True
