"""A review whose comments sit on the lines they are about.

WHAT: `post_review(repo, number, head_sha, body, findings)` posts one pull-request review: the
      summary as its body, and each finding anchored to its file and line. Returns the findings it
      could NOT place, which is never an empty answer by default.
WHY:  **A LINE NUMBER IN A SUMMARY IS A REFERENCE; A REVIEW COMMENT IS ON THE CODE.** The developer
      reading the Files-changed tab sees the claim beside the line it concerns, without scrolling
      to a comment and back. That is what every competitor means by inline review, and it is the
      difference between a report about a change and a review of it.

      **GITHUB REFUSES A COMMENT ON A LINE THAT IS NOT IN THE DIFF, AND THAT REFUSAL MUST NOT
      DISAPPEAR.** A finding anchored to an unchanged line — a caller three files away, a quote the
      locator placed loosely — comes back 422. Dropping it silently would mean the reviewer never
      learns a finding existed, so unplaceable findings are RETURNED to the caller, which folds
      them into the summary body instead. **Empty means everything was placed**, not that nothing
      was tried.

      **ONE REVIEW, NOT N COMMENTS.** Posting each finding separately floods the timeline and
      notifies the author once per line. A single `COMMENT` review carries all of them and reads as
      one act, which is what a human reviewer does.

      **`event: COMMENT`, NEVER `REQUEST_CHANGES`.** Blocking a merge on a model's reading is a
      claim this product's evidence does not support — raw findings measured 66.7-82.1% wrong.
      Blocking belongs to the deterministic rule checks, and it is a separate decision (D1f).
IMPORTS: stdlib json, plus `ingest.github_api` for the authenticated call and `types.finding`.
CONSUMED BY: `serve/review_delivery.py`, which calls `publish()` and lets this decide the shape.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

from quantamind.ingest import github_api
from quantamind.ingest.github_comments import marker, post
from quantamind.types.finding import Finding

RIGHT = "RIGHT"


class ReviewFailed(RuntimeError):
    """Posting the review failed for a reason that is not an unplaceable comment."""

    def __init__(self, repo: str, number: int, reason: str) -> None:
        super().__init__(f"{repo}#{number}: {reason}")
        self.repo, self.number, self.reason = repo, number, reason


def already_reviewed(repo: str, number: int, head_sha: str) -> bool:
    """Whether this commit already has a review from us.

    **A REDELIVERY IS A NORMAL EVENT, NOT AN ERROR.** GitHub retries, and a second review on the
    same commit would notify the author twice for one change. The marker is the same one
    `ingest/github_comments` stamps, so both surfaces answer "have we spoken about this commit"
    the same way.
    """
    raw = github_api.call(repo, f"repos/{repo}/pulls/{number}/reviews?per_page=100")
    reviews = json.loads(raw)
    if not isinstance(reviews, list):
        return False
    return any(marker(head_sha) in str(r.get("body", "")) for r in reviews)


def _anchor(finding: Finding) -> dict[str, object]:
    """One review comment, on the right-hand side of the diff at the finding's line."""
    return {"path": finding.path, "line": finding.line, "side": RIGHT, "body": finding.claim}


def post_review(
    repo: str, number: int, head_sha: str, body: str, findings: Sequence[Finding]
) -> tuple[Finding, ...]:
    """Post one review. Returns the findings GitHub would not place on a line.

    **A FINDING WITH NO LINE IS UNPLACEABLE BY DEFINITION** and is returned without being tried:
    `Finding.line` is 0 until the gate locates the quote in the diff, and asking GitHub to anchor
    at line 0 is a 422 we can predict.
    """
    placeable = [f for f in findings if f.line > 0]
    unplaceable = tuple(f for f in findings if f.line <= 0)
    payload: dict[str, object] = {
        "commit_id": head_sha,
        "body": f"{body}\n\n{marker(head_sha)}",
        "event": "COMMENT",
        "comments": [_anchor(f) for f in placeable],
    }
    try:
        github_api.call(
            repo, f"repos/{repo}/pulls/{number}/reviews", method="POST", body=json.dumps(payload)
        )
    except github_api.ApiFailed as exc:
        # **A REJECTED ANCHOR IS NOT A FAILED REVIEW.** GitHub refuses the whole call when any one
        # line is outside the diff, so the review is retried with the body alone and every finding
        # comes back to the caller to be folded into it. Losing them here would be the silence.
        if "line" not in exc.reason.lower() and "diff" not in exc.reason.lower():
            raise ReviewFailed(repo, number, exc.reason) from None
        payload["comments"] = []
        github_api.call(
            repo, f"repos/{repo}/pulls/{number}/reviews", method="POST", body=json.dumps(payload)
        )
        return tuple(findings)
    return unplaceable


def publish(repo: str, number: int, head_sha: str, body: str, findings: Sequence[Finding]) -> bool:
    """Post the review the right way for what we have. True when something was written.

    **A REVIEW WHEN THERE IS SOMETHING TO ANCHOR, A COMMENT WHEN THERE IS NOT.** A finding on the
    line it concerns is what a developer reads without leaving the diff. A summary with no findings
    has nothing to anchor, and an empty review is a notification about nothing.

    The duplicate check covers both surfaces on the same marker, so a redelivered webhook writes
    once whichever path it took.
    """
    if not findings:
        return post(repo, number, head_sha, body)
    if already_reviewed(repo, number, head_sha):
        return False
    loose = post_review(repo, number, head_sha, body, findings)
    if loose:
        print(f"[review] {len(loose)} finding(s) had no line in the diff", flush=True)
    return True
