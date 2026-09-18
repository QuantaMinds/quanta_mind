"""Every way reconciliation can fail to get an answer, and the nothing it must do about it.

WHAT: `reconcile()` against a REAL store when the forge times out, refuses, or replies in a shape
      we cannot read.
WHY:  **THE DANGEROUS DIRECTION IS THE ONE WITH NO CUSTOMER TO COMPLAIN.** Failing to withdraw
      costs us a review we are not paid for, and somebody eventually notices. Withdrawing wrongly
      stops a paying customer's reviews with no error anywhere — the endpoint is healthy, the
      comment simply never arrives. So the refusals get their own file, and it is longer than the
      file for the happy path.

      **AN EMPTY LISTING IS THE ONE THAT WOULD HAVE BEEN CATASTROPHIC.** A parsing mistake
      returning `()` would, on a naive set difference, withdraw every repository of every account
      in a single run — a correct-looking answer that empties the estate.

      Sabotage to check this file works: make `_one` withdraw on `CouldNotAsk` and
      `test_an_outage_withdraws_nothing` fails.
IMPORTS: quantamind.serve.reconcile, quantamind.ingest.installation_scope,
      quantamind.store.{installations,schema,tenancy}, quantamind.types.settings.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from quantamind.ingest.installation_scope import CouldNotAsk
from quantamind.serve.reconcile import reconcile
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


def test_an_outage_withdraws_nothing(tmp_path: Path) -> None:
    """A timeout is not a fact about the customer's repositories."""
    _installed(tmp_path, "acme", ["acme/widget", "acme/gadget"])

    def down(probe: str) -> tuple[str, ...]:
        raise CouldNotAsk("HTTP 503: upstream unavailable")

    report = reconcile(_settings(tmp_path), down)

    assert _may_review(tmp_path, "acme/widget") is True
    assert _may_review(tmp_path, "acme/gadget") is True
    assert report.withdrawn == 0
    assert report.unasked == 1
    assert "503" in report.accounts[0].unasked


def test_an_empty_listing_withdraws_nothing(tmp_path: Path) -> None:
    """The catastrophic one: `()` from a parsing mistake must not empty the estate."""
    _installed(tmp_path, "acme", ["acme/widget", "acme/gadget"])

    report = reconcile(_settings(tmp_path), lambda probe: ())

    assert _may_review(tmp_path, "acme/widget") is True
    assert _may_review(tmp_path, "acme/gadget") is True
    assert report.withdrawn == 0
    assert report.unasked == 1


def test_one_failing_account_does_not_stop_the_others(tmp_path: Path) -> None:
    """A per-account failure must not abort the estate-wide run."""
    _installed(tmp_path, "acme", ["acme/widget"])
    _installed(tmp_path, "zeta", ["zeta/thing", "zeta/other"])

    def selective(probe: str) -> tuple[str, ...]:
        if probe.startswith("acme/"):
            raise CouldNotAsk("rate limited")
        return ("zeta/thing",)

    report = reconcile(_settings(tmp_path), selective)

    assert _may_review(tmp_path, "acme/widget") is True, "the unreadable account was deprovisioned"
    assert _may_review(tmp_path, "zeta/other") is False, "the readable account was not reconciled"
    assert report.unasked == 1
    assert report.withdrawn == 1


def test_an_already_withdrawn_account_is_never_asked_about(tmp_path: Path) -> None:
    """A request that can only confirm what we already know is a request not worth making."""
    _installed(tmp_path, "acme", ["acme/widget"])
    conn = _conn(tmp_path)
    try:
        installations.withdraw(conn, "acme/widget", at=1_700_000_100)
    finally:
        conn.close()

    asked: list[str] = []

    def record(probe: str) -> tuple[str, ...]:
        asked.append(probe)
        return (probe,)

    report = reconcile(_settings(tmp_path), record)

    assert asked == []
    assert report.accounts == ()


def test_one_account_can_be_named(tmp_path: Path) -> None:
    """An operator chasing one customer must not walk the whole estate to do it."""
    _installed(tmp_path, "acme", ["acme/widget"])
    _installed(tmp_path, "zeta", ["zeta/thing"])

    asked: list[str] = []

    def record(probe: str) -> tuple[str, ...]:
        asked.append(probe)
        return ()

    reconcile(_settings(tmp_path), record, account="acme")

    assert asked == ["acme/widget"]
