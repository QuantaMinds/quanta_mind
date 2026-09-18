"""An uninstall must mark the rows removed. Until this existed, nothing did.

WHAT: `installation.deleted`, `installation.suspend` and `installation_repositories.removed`
      against a REAL store, asserting on the `installation` rows and on `entitled()` afterwards.
WHY:  **`store/installations.withdraw()` HAD NO CALLER IN `src/`.** It was written and tested in
      isolation and never wired, so `removed_at` stayed NULL forever, `State.REMOVED` was
      unreachable in production, and a customer who uninstalled went on being reviewed. Every test
      of `withdraw()` passed throughout — they called it directly, which is exactly the "a check
      that runs only where the thing it checks cannot happen" shape AGENTS.md rule 14 names.

      **THE ASSERTIONS ARE ON `entitled()`, NOT ON THE ROWCOUNT.** `withdraw()` returning 1 proves
      an UPDATE ran; it does not prove the reviewer will refuse. `may_review` is the thing that
      decides, so that is the thing asserted — a rowcount test would stay green if the read path
      and the write path ever disagreed about which column means removed.

      Sabotage to check this file works: delete the `withdraw` call in
      `serve/installation_event.settle` and `test_deleted_marks_every_repo_removed` fails.
IMPORTS: quantamind.serve.{installation_event,webhook_github}, quantamind.store.{installations,
      schema,tenancy}, quantamind.types.settings.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantamind.serve import onboarding as warm_module
from quantamind.serve.installation_event import settle
from quantamind.serve.webhook_github import interpret
from quantamind.store import installations, schema, tenancy
from quantamind.types.forge.delivery import Installed, Withdrawn
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


def test_deleted_is_read_as_a_withdrawal(tmp_path: Path) -> None:
    decision = _delivery(
        "installation",
        {"action": "deleted", "installation": {"id": 42, "account": {"login": "acme", "id": 7}}},
    )
    assert isinstance(decision, Withdrawn)
    assert decision.account == "acme"
    assert decision.action == "deleted"
    assert decision.installation_id == 42


def test_suspend_is_read_as_a_withdrawal(tmp_path: Path) -> None:
    """A suspended installation's token fails; leaving it covered makes us look broken."""
    decision = _delivery(
        "installation",
        {"action": "suspend", "installation": {"id": 42, "account": {"login": "acme"}}},
    )
    assert isinstance(decision, Withdrawn)
    assert decision.action == "suspend"


def test_deleted_marks_every_repo_removed(tmp_path: Path) -> None:
    """The one that was broken: an uninstall must reach every repository we hold for the account."""
    _installed(tmp_path, "acme", ["acme/widget", "acme/gadget"])
    assert _may_review(tmp_path, "acme/widget") is True
    assert _may_review(tmp_path, "acme/gadget") is True

    decision = _delivery(
        "installation",
        {"action": "deleted", "installation": {"id": 42, "account": {"login": "acme"}}},
    )
    answered = _Answers()
    settle(decision, _settings(tmp_path), answered)

    assert _may_review(tmp_path, "acme/widget") is False
    assert _may_review(tmp_path, "acme/gadget") is False
    assert answered == [(200, {"withdrawn": ["acme/gadget", "acme/widget"], "account": "acme"})]


def test_another_accounts_rows_are_untouched(tmp_path: Path) -> None:
    """A whole-account withdrawal reads OUR store; it must not spill past the account it names."""
    _installed(tmp_path, "acme", ["acme/widget"])
    _installed(tmp_path, "other", ["other/thing"])

    decision = _delivery(
        "installation",
        {"action": "deleted", "installation": {"id": 1, "account": {"login": "acme"}}},
    )
    settle(decision, _settings(tmp_path), _Answers())

    assert _may_review(tmp_path, "acme/widget") is False
    assert _may_review(tmp_path, "other/thing") is True


def test_removed_repositories_are_withdrawn_and_added_ones_survive(
    tmp_path: Path, monkeypatch: Any
) -> None:
    """One delivery carries both directions. Handling one and dropping the other loses a fact.

    **THE NETWORK IS STUBBED, THE STORE IS REAL.** This is the only case here that reaches
    `onboarding.admit`, which clones the added repository and asks GitHub four questions about it.
    Left alone the test would pass or fail on whether the runner has a network, and `acme/newthing`
    does not exist, so it would be asserting on an error path either way. Same seam
    `test_onboarding.py` uses.
    """
    monkeypatch.setattr(warm_module, "ensure", lambda repo, root, token=None: tmp_path / "clone")
    monkeypatch.setattr(warm_module, "facts_for", lambda repo: _refuse(repo))
    _installed(tmp_path, "acme", ["acme/widget", "acme/gadget"])

    decision = _delivery(
        "installation_repositories",
        {
            "action": "removed",
            "installation": {"id": 42, "account": {"login": "acme"}},
            "repositories_added": [{"full_name": "acme/newthing"}],
            "repositories_removed": [{"full_name": "acme/gadget"}],
        },
    )
    assert isinstance(decision, Installed)
    assert decision.repos == ("acme/newthing",)
    assert decision.no_longer_covered == ("acme/gadget",)

    answered = _Answers()
    settle(decision, _settings(tmp_path), answered)

    assert _may_review(tmp_path, "acme/gadget") is False
    assert _may_review(tmp_path, "acme/widget") is True
    assert answered[0][1]["withdrawn"] == ["acme/gadget"]


def test_a_withdrawal_that_matches_nothing_says_so(tmp_path: Path) -> None:
    """An account we hold no rows for must report zero, not a silent success."""
    decision = _delivery(
        "installation",
        {"action": "deleted", "installation": {"id": 9, "account": {"login": "stranger"}}},
    )
    answered = _Answers()
    settle(decision, _settings(tmp_path), answered)

    assert answered == [(200, {"withdrawn": [], "account": "stranger"})]
