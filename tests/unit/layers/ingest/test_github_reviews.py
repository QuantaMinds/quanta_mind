"""A finding with no line must not vanish, and a rejected anchor must not lose the review.

WHAT: Exercises `ingest/github_reviews.post_review()` around the two failures that lose
      information: a finding GitHub cannot place, and a call GitHub rejects because one line sits
      outside the diff.
WHY:  **AN UNPLACEABLE FINDING IS THE SILENCE THIS PRODUCT REFUSES.** GitHub returns 422 when a
      review comment names a line that is not in the diff. If that is swallowed, the reviewer never
      learns the finding existed — the review looks complete and is quietly narrower. So the
      unplaceable ones are RETURNED, and an empty return means every one was placed rather than
      that none was tried.

      **AND A REJECTED ANCHOR MUST NOT COST THE WHOLE REVIEW.** GitHub refuses the entire call if
      any single line is out of range, so a retry with the body alone is the difference between a
      summary the developer reads and nothing at all.

      The transport is stubbed because the failure being tested is GitHub's refusal, which cannot
      be produced on demand against a real repository. What is asserted is the record OUR code
      returns from it.
IMPORTS: ingest.github_reviews, types.finding.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json

import pytest

from quantamind.ingest import github_api
from quantamind.ingest.publish import github_reviews
from quantamind.types.finding import Finding

PLACED = Finding(path="a.py", quote="x = 1", claim="This shadows a builtin.", line=12)
UNPLACED = Finding(path="b.py", quote="y = 2", claim="This is never read.", line=0)


def test_a_finding_with_no_line_is_returned_not_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[dict[str, object]] = []

    def _ok(repo: str, path: str, **kw: object) -> bytes:
        sent.append(json.loads(str(kw.get("body"))))
        return b"{}"

    monkeypatch.setattr(github_api, "call", _ok)
    monkeypatch.setattr(github_reviews.github_api, "call", _ok)

    loose = github_reviews.post_review("o/r", 1, "s" * 40, "summary", [PLACED, UNPLACED])

    assert loose == (UNPLACED,), (
        "a finding with no line was not returned. It cannot be anchored, so if it is not handed "
        "back the reviewer never learns it existed"
    )
    assert [c["path"] for c in sent[0]["comments"]] == ["a.py"], "only placeable lines are sent"


def test_a_rejected_anchor_retries_the_body_and_returns_every_finding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**THE ONE THAT WOULD LOSE THE WHOLE REVIEW.** GitHub refuses the entire call if one line is
    outside the diff."""
    attempts: list[dict[str, object]] = []

    def _refuse_then_accept(repo: str, path: str, **kw: object) -> bytes:
        payload = json.loads(str(kw.get("body")))
        attempts.append(payload)
        if payload["comments"]:
            raise github_api.ApiFailed("POST", path, "HTTP 422: line must be part of the diff")
        return b"{}"

    monkeypatch.setattr(github_reviews.github_api, "call", _refuse_then_accept)

    loose = github_reviews.post_review("o/r", 1, "s" * 40, "summary", [PLACED])

    assert len(attempts) == 2, "the review was not retried without its anchors"
    assert attempts[1]["comments"] == [], "the retry still carried the rejected anchors"
    assert loose == (PLACED,), (
        "the rejected finding was not returned, so it would be lost from the summary too"
    )


def test_an_unrelated_failure_raises_rather_than_silently_posting_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _forbidden(repo: str, path: str, **kw: object) -> bytes:
        raise github_api.ApiFailed("POST", path, "HTTP 403: resource not accessible")

    monkeypatch.setattr(github_reviews.github_api, "call", _forbidden)

    with pytest.raises(github_reviews.ReviewFailed, match="403"):
        github_reviews.post_review("o/r", 1, "s" * 40, "summary", [PLACED])
