"""Idempotency, tested exhaustively because the part that can double-post is a pure function.

WHAT: Asserts the head-SHA key behaves against the payload shapes GitHub actually returns.
WHY:  **A reviewer that comments twice on the same commit is a reviewer people mute**, and every
      path into this code — a retry, a redelivered webhook, an unrelated event on the same pull
      request — is indistinguishable from a first delivery without a key.

      These are pure-function tests with no network and no stub, which is the point of putting the
      decision in a pure function: the dangerous half is the half that can be tested exhaustively.

      **`post()` is not exercised here.** It writes into a repository under a real identity, and
      nothing in this suite posts to a repository we do not own.
IMPORTS: quantamind.ingest.github_comments.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from quantamind.ingest import github_comments
from quantamind.ingest.github_comments import MARKER_PREFIX, already_posted, marker

SHA = "0f4d1c9a5b3e2d7c8a1b0e9f6d3c2b1a0e9f8d7c"
OTHER = "ffffffffffffffffffffffffffffffffffffffff"


def test_a_comment_carrying_the_key_counts_as_posted() -> None:
    comments = [{"body": f"### QuantaMind\n\nranked\n\n{marker(SHA)}"}]
    assert already_posted(comments, SHA) is True


def test_a_comment_for_a_different_commit_does_not_suppress_this_one() -> None:
    """A pull request lives for weeks and its head moves; each new head gets its own comment."""
    comments = [{"body": f"older review\n\n{marker(OTHER)}"}]
    assert already_posted(comments, SHA) is False


def test_someone_elses_comment_never_counts_as_ours() -> None:
    comments = [
        {"body": "LGTM"},
        {"body": "Please rebase"},
        {"body": "quantamind mentioned in prose, not the marker"},
    ]
    assert already_posted(comments, SHA) is False


def test_a_malformed_comment_cannot_suppress_a_post() -> None:
    """A missing body must not be able to silence us; the failure would look like idempotency."""
    assert already_posted([{}, {"body": None}, {"user": "x"}], SHA) is False


def test_no_comments_at_all_means_not_posted() -> None:
    assert already_posted([], SHA) is False


def test_the_key_is_invisible_in_rendered_markdown() -> None:
    """A human-readable footer would be edited eventually and the key would stop matching."""
    assert marker(SHA).startswith("<!--") and marker(SHA).endswith("-->")
    assert SHA in marker(SHA)
    assert marker(SHA).startswith(MARKER_PREFIX)


def test_an_empty_key_is_refused_rather_than_matching_everything() -> None:
    with pytest.raises(ValueError):
        marker("   ")


def test_the_key_survives_a_body_that_contains_other_html_comments() -> None:
    comments = [{"body": f"<!-- other tool -->\ntext\n{marker(SHA)}\n<!-- trailing -->"}]
    assert already_posted(comments, SHA) is True


# --- pagination -------------------------------------------------------------------------------
#
# **`existing()` REFUSES A TRUNCATED THREAD AND NOTHING EXERCISED THE REFUSAL.** Reading only
# part of the comments means not finding our own marker and posting a DUPLICATE review on a
# customer's pull request — the failure this module exists to prevent, caused by its own limit.
# The code is right; mutating `MAX_PAGES` to 0 or 21 left every tier of the suite green.
#
# The budget is written out as 10 x 100 rather than imported: a test phrased as `MAX_PAGES + 1`
# reads the value under test and passes at any value.

PAGES, SIZE = 10, 100


def _serve(pages: dict[int, list[dict[str, Any]]], monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Answer each page request from `pages`, recording which pages were asked for."""
    asked: list[int] = []

    def call(repo: str, path: str, method: str = "GET", body: bytes | None = None) -> bytes:
        page = int(path.split("&page=")[1])
        asked.append(page)
        return json.dumps(pages.get(page, [])).encode()

    monkeypatch.setattr(github_comments.github_api, "call", call)
    return asked


def test_the_comment_budget_is_ten_pages_of_a_hundred() -> None:
    """The numbers the refusal depends on. Both were freely mutable."""
    assert github_comments.MAX_PAGES == PAGES
    assert github_comments.PER_PAGE == SIZE


def test_a_thread_longer_than_the_budget_refuses_rather_than_returning_part_of_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The duplicate-comment failure. A short list here would read as 'we never posted'."""
    full = [{"body": f"comment {n}"} for n in range(SIZE)]
    asked = _serve(dict.fromkeys(range(1, PAGES + 3), full), monkeypatch)

    with pytest.raises(github_comments.CommentFailed, match="refusing to decide idempotency"):
        github_comments.existing("o/r", 1)

    assert asked == list(range(1, PAGES + 1)), "the page budget was not walked exactly once"


def test_a_short_page_returns_the_thread_and_asks_for_no_more(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ordinary case, so the refusal above is not the function refusing everything."""
    asked = _serve({1: [{"body": "only one"}]}, monkeypatch)

    assert github_comments.existing("o/r", 1) == [{"body": "only one"}]
    assert asked == [1]


def test_a_full_page_is_followed_by_another_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exactly one full page is indistinguishable from more, so the walk must continue."""
    asked = _serve({1: [{"body": f"c{n}"} for n in range(SIZE)], 2: []}, monkeypatch)

    assert len(github_comments.existing("o/r", 1)) == SIZE
    assert asked == [1, 2]


def test_a_non_list_page_is_a_failure_not_an_empty_thread(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An error object must never read as 'no comments', which would authorise a post."""
    monkeypatch.setattr(
        github_comments.github_api, "call", lambda *a, **k: b'{"message": "Not Found"}'
    )

    with pytest.raises(github_comments.CommentFailed, match="comments page 1 was dict"):
        github_comments.existing("o/r", 1)
