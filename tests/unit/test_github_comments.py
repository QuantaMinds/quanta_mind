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

import pytest

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
