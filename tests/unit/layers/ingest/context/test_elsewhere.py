"""D6c: a source we cannot reach must not read as a change with no stated goal.

WHAT: `ingest/context/elsewhere.py` — the Jira and Slack readers, without a network call.
WHY:  **`Unreachable` IS THE EXPECTED ANSWER AND IT IS TYPED.** No token is configured for either
      system in any current deployment, so both decline before opening a socket. A product
      reporting that as a fault would report a fault to every customer who has not bought the
      integration; a product returning an empty string would print a change with no goal and let
      the reader assume the author gave none.

      **SLACK ANSWERS 200 WITH `ok: false`**, so the status code alone is not the answer. That is
      asserted here because reading only the code turns a refusal into an empty message — the exact
      shape this module exists to prevent.
IMPORTS: quantamind.ingest.context.elsewhere; stdlib json, unittest.mock.
CONSUMED BY: `just test-unit`.
"""

from __future__ import annotations

import io
import json
from typing import Any
from unittest import mock

import pytest

from quantamind.ingest.context.elsewhere import Elsewhere, Unreachable, jira, slack


class _Answer(io.BytesIO):
    def __enter__(self) -> _Answer:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _replies(payload: dict[str, Any]) -> Any:
    return lambda request, timeout=0: _Answer(json.dumps(payload).encode())


@pytest.mark.parametrize(
    ("base", "key", "token"),
    [
        ("", "P-1", "t"),
        ("https://x.atlassian.net", "", "t"),
        ("https://x.atlassian.net", "P-1", ""),
    ],
    ids=["no-base", "no-key", "no-token"],
)
def test_jira_without_configuration_declines_without_a_socket(
    base: str, key: str, token: str
) -> None:
    """**NOT_CONFIGURED IS NOT A FAULT**, and no request is made to discover it."""
    with mock.patch("urllib.request.urlopen", side_effect=AssertionError("opened a socket")):
        assert jira(base, key, token) is Unreachable.NOT_CONFIGURED


def test_jira_returns_the_summary_and_a_browse_url() -> None:
    """The positive path, or every negative test above proves only that nothing works."""
    payload = {"fields": {"summary": "Cache the weights", "description": "They re-download."}}
    with mock.patch("urllib.request.urlopen", _replies(payload)):
        got = jira("https://acme.atlassian.net/", "PROJ-42", "token")

    assert isinstance(got, Elsewhere)
    assert got.title == "Cache the weights"
    assert got.body == "They re-download."
    assert got.url == "https://acme.atlassian.net/browse/PROJ-42"


def test_jiras_document_tree_description_becomes_empty_not_a_guess() -> None:
    """**Jira v3 descriptions are a document tree.** Rendering one is a parser we have not written,
    and printing its JSON would be worse than printing nothing."""
    payload = {"fields": {"summary": "A title", "description": {"type": "doc", "content": []}}}
    with mock.patch("urllib.request.urlopen", _replies(payload)):
        got = jira("https://acme.atlassian.net", "PROJ-42", "token")

    assert isinstance(got, Elsewhere)
    assert got.title == "A title"
    assert got.body == ""


def test_plain_http_is_refused_rather_than_downgraded() -> None:
    """**THE TOKEN IS IN THE HEADER.** A URL without a scheme must not put it on the wire clear."""
    with mock.patch("urllib.request.urlopen", side_effect=AssertionError("opened a socket")):
        assert jira("http://acme.atlassian.net", "PROJ-42", "token") is Unreachable.REFUSED


def test_slack_ok_false_is_a_refusal_not_an_empty_message() -> None:
    """**SLACK ANSWERS 200 AND SAYS NO IN THE BODY.**"""
    with mock.patch("urllib.request.urlopen", _replies({"ok": False, "error": "not_in_channel"})):
        assert slack("C123", "1700000000.1", "token") is Unreachable.REFUSED


def test_slack_returns_the_message_text_when_it_really_answers() -> None:
    """The positive path."""
    payload = {"ok": True, "messages": [{"text": "we decided to cache the weights"}]}
    with mock.patch("urllib.request.urlopen", _replies(payload)):
        got = slack("C123", "1700000000.1", "token")

    assert isinstance(got, Elsewhere)
    assert got.body == "we decided to cache the weights"


def test_an_unparseable_reply_is_unreadable_not_refused() -> None:
    """Ours to fix, not the customer's — and the reader is told which."""
    with mock.patch("urllib.request.urlopen", _replies({"ok": True, "messages": []})):
        assert slack("C123", "1700000000.1", "token") is Unreachable.UNREADABLE
