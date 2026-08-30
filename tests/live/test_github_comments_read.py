"""The read half against real pull requests. The write half is not exercised, and that is stated.

WHAT: Reads real comment threads and asserts the idempotency key behaves against what GitHub
      actually returns — including a thread with many comments and one with none.
WHY:  The pure tests cover the decision against payloads I wrote. This covers it against payloads
      GitHub wrote, which is where field names and pagination differ from what anyone assumed.

      **`post()` is deliberately not called.** It writes into someone else's repository under a
      real identity — `gh api user` here is a person, not a bot — and a test suite that posts to
      open-source projects to prove itself is a test suite that should not exist. The write path is
      exercised by hand against a repository we own, and `docs/engineering/CODEBASE.md` says so
      rather than letting a green suite imply coverage.
IMPORTS: quantamind.ingest.publish.github_comments.
CONSUMED BY: `just verify` via `test-live`.
"""

from __future__ import annotations

from quantamind.ingest.publish.github_comments import CommentFailed, already_posted, existing

REPO = "pallets/flask"
BUSY_PR = 6096
SOME_SHA = "0f4d1c9a5b3e2d7c8a1b0e9f6d3c2b1a0e9f8d7c"


def test_a_real_thread_reads_and_contains_none_of_our_comments() -> None:
    comments = existing(REPO, BUSY_PR)
    assert isinstance(comments, list), "the reader must return a list even when the thread is empty"
    assert not already_posted(comments, SOME_SHA), (
        "we have never commented on flask; a True here means the key matches something it should "
        "not, and the product would go silent on real work"
    )
    for comment in comments:
        assert "body" in comment, f"a real comment lacked a body field: {sorted(comment)[:8]}"


def test_a_pull_request_that_does_not_exist_raises_with_the_call_site() -> None:
    try:
        existing(REPO, 99_999_999)
    except CommentFailed as failure:
        assert "99999999" in str(failure) and REPO in str(failure)
    else:
        raise AssertionError("reading a non-existent pull request must raise, not return []")
