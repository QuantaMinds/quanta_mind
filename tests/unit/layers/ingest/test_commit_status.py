"""The writer that can block a merge: what it sends, where it sends it, and what it refuses.

WHAT: Drives `ingest/publish/commit_status.post` with `github_api.call` replaced by a spy that
      records the path, method and body, and asserts on what would have gone over the wire.
WHY:  **A STATUS ON THE WRONG COMMIT BLOCKS NOTHING AND REPORTS SUCCESS.** Branch protection
      watches the head of the pull request; a status posted against any other commit is accepted by
      GitHub, invisible to the gate, and indistinguishable from a working one unless the path is
      asserted. The spy exists to make the URL checkable, not to avoid a network call.
IMPORTS: pytest, json, quantamind.ingest.github_api, quantamind.ingest.publish.commit_status.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json

import pytest

from quantamind.ingest import github_api
from quantamind.ingest.publish import commit_status

HEAD = "b" * 40


class _Spy:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, str]] = []

    def __call__(
        self, repo: str, path: str, *, method: str = "GET", body: str | None = None, **_: object
    ) -> bytes:
        self.calls.append((repo, path, method, body or ""))
        return b"{}"


def test_the_status_goes_to_the_head_sha_of_the_pull_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spy = _Spy()
    monkeypatch.setattr(commit_status.github_api, "call", spy)

    assert commit_status.post("acme/widgets", HEAD, "failure", "1 violation(s)") is True

    _repo, path, method, body = spy.calls[0]
    assert path == f"repos/acme/widgets/statuses/{HEAD}", (
        f"a status on the wrong commit blocks nothing and still returns True: {path}"
    )
    assert method == "POST"
    sent = json.loads(body)
    assert sent["state"] == "failure"
    assert sent["context"] == commit_status.CONTEXT


def test_a_state_github_does_not_accept_is_refused_here_not_discovered_as_a_422(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spy = _Spy()
    monkeypatch.setattr(commit_status.github_api, "call", spy)

    with pytest.raises(ValueError, match="not a status GitHub accepts"):
        commit_status.post("acme/widgets", HEAD, "blocked", "typo in the state")

    assert spy.calls == [], "a refused state must not reach the network at all"


def test_a_long_description_is_truncated_deliberately_rather_than_by_github(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spy = _Spy()
    monkeypatch.setattr(commit_status.github_api, "call", spy)

    commit_status.post("acme/widgets", HEAD, "success", "x" * 400)

    sent = json.loads(spy.calls[0][3])
    assert len(sent["description"]) == commit_status.DESCRIPTION_LIMIT


def test_a_refused_call_raises_and_names_the_repository_and_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _forbidden(*_: object, **__: object) -> bytes:
        raise github_api.ApiFailed("POST", f"repos/acme/widgets/statuses/{HEAD}", "403 Forbidden")

    monkeypatch.setattr(commit_status.github_api, "call", _forbidden)

    with pytest.raises(commit_status.StatusFailed) as caught:
        commit_status.post("acme/widgets", HEAD, "failure", "1 violation(s)")

    assert caught.value.repo == "acme/widgets"
    assert caught.value.head_sha == HEAD
