"""When the installation row is written, and what may un-write it.

WHAT: The ordering between answering a delivery and recording its rows, and the one caller allowed
      to clear `removed_at`.
WHY:  **BOTH DEFECTS HERE WERE FOUND BY RUNNING IT, NOT BY READING IT.** Signed deliveries against
      a live endpoint: install two repositories, remove one, uninstall. Both the removal and the
      uninstall answered `withdrawn: []` and reported success.

      Two causes, and they compound. The rows were written by `onboarding.admit()` — the SLOW half,
      after the reply, after four GitHub calls and a ~31s clone-and-index per repository — so a
      removal inside that window found nothing to remove. And `record()` cleared `removed_at` on
      every write, so the install's own late warm-up then resurrected whatever had been removed.

      Neither was reachable while `store/installations.withdraw()` had no caller, which is why no
      test caught them and why `test_reinstalling_after_removal_clears_the_removal` was passing
      while asserting the bug.

      Sabotage: drop `reinstate` from `record()`'s upsert condition and
      `test_a_late_warm_up_does_not_resurrect_a_removal` fails; move `claim()` back after the
      answer and `test_the_rows_exist_before_the_delivery_is_answered` fails.
IMPORTS: quantamind.serve.{installation_event,webhook_github}, quantamind.store.installations,
      quantamind.types.settings.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantamind.serve.installation import onboarding as warm_module
from quantamind.serve.installation.installation_event import settle
from quantamind.serve.webhook_github import interpret
from quantamind.store import installations, schema, tenancy
from quantamind.types.settings import Settings


def _refuse(repo: str) -> Any:
    """`facts_for` raises on an unreadable repository; `admit` warms it anyway and says so."""
    raise RuntimeError(f"stubbed: no network for {repo}")


def _settings(root: Path) -> Settings:
    return Settings(database_path=str(root), clone_root=str(root / "clones"))


def _accounts(root: Path) -> Any:
    return schema.open_store(tenancy.shared(root, tenancy.ACCOUNTS))


def _installed(root: Path, account: str, repos: list[str]) -> None:
    """Put real rows in a real store, the way `onboarding.admit` does."""
    conn = _accounts(root)
    try:
        for repo in repos:
            installations.record(conn, account, repo, at=1_700_000_000, eligible=True)
    finally:
        conn.close()


def _may_review(root: Path, repo: str) -> bool:
    conn = _accounts(root)
    try:
        return installations.entitled(conn, repo).may_review
    finally:
        conn.close()


class _Answers(list[tuple[int, dict[str, Any]]]):
    """Records what `settle` answered. A list so the assertions read as one value."""

    def __call__(self, status: int, payload: dict[str, Any]) -> None:
        self.append((status, payload))


def _delivery(event: str, body: dict[str, Any]) -> Any:
    """Through the real parser, so a payload shape change breaks this rather than sliding by."""
    return interpret(event, json.dumps(body).encode())


def test_a_late_warm_up_does_not_resurrect_a_removal(tmp_path: Path) -> None:
    """Found by running it, not by reading it.

    `admit()` records the installation row AFTER the delivery is answered — four GitHub calls and a
    ~31s clone-and-index per repository later. `record()`'s upsert cleared `removed_at`
    unconditionally, so an install's own slow warm-up landing after a removal silently undid it.
    Unreachable while `withdraw()` had no caller; live the moment it got one.
    """
    _installed(tmp_path, "acme", ["acme/widget"])
    conn = _accounts(tmp_path)
    try:
        installations.withdraw(conn, "acme/widget", at=2000)
        assert installations.entitled(conn, "acme/widget").may_review is False
        # What the late warm-up does: refresh eligibility, assert nothing about coverage.
        installations.record(conn, "acme", "acme/widget", at=3000, eligible=True)
        assert installations.entitled(conn, "acme/widget").may_review is False
        # What a genuine reinstall does, which must still work.
        installations.record(conn, "acme", "acme/widget", at=4000, reinstate=True)
        assert installations.entitled(conn, "acme/widget").may_review is True
    finally:
        conn.close()


def test_the_rows_exist_before_the_delivery_is_answered(tmp_path: Path, monkeypatch: Any) -> None:
    """A removal arriving during a warm-up must find rows to remove.

    The answer callback asserts mid-flight: by the time we reply, the `installation` rows must
    already be there. They used to be written by the slow half, so a removal inside that window
    withdrew nothing and reported success.
    """
    monkeypatch.setattr(warm_module, "ensure", lambda repo, root, token=None: tmp_path / "clone")
    monkeypatch.setattr(warm_module, "facts_for", lambda repo: _refuse(repo))

    decision = _delivery(
        "installation",
        {
            "action": "created",
            "installation": {"id": 42, "account": {"login": "acme"}},
            "repositories": [{"full_name": "acme/widget"}],
        },
    )
    seen: list[bool] = []

    def answer(status: int, payload: dict[str, Any]) -> None:
        seen.append(_may_review(tmp_path, "acme/widget"))

    settle(decision, _settings(tmp_path), answer)

    assert seen == [True], "the installation row did not exist when the delivery was answered"
