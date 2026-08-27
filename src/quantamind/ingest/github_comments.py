"""Post one comment per head SHA, and never a second one for the same commit.

WHAT: `marker()` stamps a comment with the commit it describes, `already_posted()` decides from a
      list of existing comments whether we have spoken about this one, and `post()` does the write.
WHY:  **A reviewer that comments twice on the same commit is a reviewer people mute.** Retries,
      redeliveries and a webhook that fires again on an unrelated event all reach this code, and
      none of them are distinguishable from a first delivery without a key.

      **The key is the head SHA, not the pull request number.** A pull request lives for weeks and
      its head moves; keying on the number would comment once and go silent for every later push,
      which is the opposite failure and just as bad.

      **THE DECISION IS A PURE FUNCTION and the I/O is thin.** `already_posted()` takes a list and
      returns a bool, so idempotency is tested against real payload shapes with no network and no
      stub. Everything that could double-post lives in the part that can be tested exhaustively.

      **A truncated read RAISES rather than deciding on partial data.** `existing()` stopped at
      the pagination cap and returned what it had, so a thread longer than the cap would not
      contain our marker as far as we could see, and we would post a duplicate — the module's own
      limit causing the failure it exists to prevent.

      **`post()` writes into someone else's repository under a real identity**, so nothing in this
      project's test suite calls it against a repository we do not own.

      **The write path HAS been exercised**, by hand, against a merged pull request on our own
      private repository, and the comments were deleted afterwards. Three calls: a first post
      returned True and created the comment; a second with the same head SHA returned False and
      created nothing; a third with a different SHA returned True, because the head had moved. Two
      comments existed, both markers matched, and the marker rendered invisibly. Recorded here
      because a test suite that never posts cannot say any of that.
IMPORTS: nothing from this project. Shells out to `gh`, like every other read in this layer.
CONSUMED BY: serve, once a webhook exists.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from quantamind.ingest import github_api

API_TIMEOUT_S = 30
PER_PAGE = 100
MAX_PAGES = 10
# An HTML comment: invisible in rendered markdown, and unambiguous to match on. A human-readable
# footer would be edited by someone eventually and the key would silently stop matching.
MARKER_PREFIX = "<!-- quantamind:head="


class CommentFailed(RuntimeError):
    """A comment read or write that did not complete. Never silently a no-op.

    A failed post that returned quietly would look exactly like a successful one to everything
    upstream, and the next delivery would be the first time anyone noticed.
    """

    def __init__(self, repo: str, number: int, reason: str) -> None:
        self.repo, self.number, self.reason = repo, number, reason
        super().__init__(f"{repo}#{number}: {reason}")


def marker(head_sha: str) -> str:
    """The stamp identifying which commit a comment describes."""
    if not head_sha.strip():
        raise ValueError("head_sha is empty; a comment with no key can never be deduplicated")
    return f"{MARKER_PREFIX}{head_sha.strip()} -->"


def already_posted(comments: Sequence[dict[str, Any]], head_sha: str) -> bool:
    """Whether one of `comments` already describes this commit.

    Pure, and takes the payload GitHub actually returns. A comment whose body is missing counts as
    not ours rather than raising: a malformed entry must not be able to suppress a post.
    """
    key = marker(head_sha)
    return any(key in str(comment.get("body") or "") for comment in comments)


def _gh(repo: str, number: int, path: str, method: str = "GET", body: str | None = None) -> Any:
    """One GitHub API call, authenticated **as the App installation**.

    **THIS USED TO SHELL OUT TO `gh api`, WHICH COMMENTS AS A PERSON.** Whoever ran `gh auth login`
    owned every comment, every rate limit and every audit-log entry. An installation token is
    scoped to the repositories the App was installed on and expires in an hour.
    """
    try:
        raw = github_api.call(repo, path, method=method, body=body)
    except github_api.ApiFailed as exc:
        raise CommentFailed(repo, number, str(exc)) from None
    try:
        return json.loads(raw) if raw.strip() else None
    except json.JSONDecodeError as exc:
        raise CommentFailed(repo, number, f"{method} {path} returned non-JSON: {exc}") from None


def existing(repo: str, number: int) -> list[dict[str, Any]]:
    """Every comment on the pull request. Read-only."""
    out: list[dict[str, Any]] = []
    for page in range(1, MAX_PAGES + 1):
        got = _gh(
            repo, number, f"repos/{repo}/issues/{number}/comments?per_page={PER_PAGE}&page={page}"
        )
        if not isinstance(got, list):
            raise CommentFailed(repo, number, f"comments page {page} was {type(got).__name__}")
        out.extend(got)
        if len(got) < PER_PAGE:
            return out
    raise CommentFailed(
        repo,
        number,
        f"more than {MAX_PAGES * PER_PAGE} comments; refusing to decide idempotency on a "
        "truncated thread. Returning what we had would mean not finding our own marker and "
        "posting a DUPLICATE -- the failure this module exists to prevent, caused by its own limit",
    )


def post(repo: str, number: int, head_sha: str, body: str) -> bool:
    """Post `body` unless this commit has already been commented on. True when it posted.

    Returns False for a duplicate rather than raising: a redelivered webhook is a normal event, not
    an error. Every OTHER failure raises.
    """
    if not body.strip():
        raise ValueError("refusing to post an empty comment; silence is the caller's decision")
    if already_posted(existing(repo, number), head_sha):
        return False

    stamped = f"{body}\n\n{marker(head_sha)}"
    created = _gh(
        repo,
        number,
        f"repos/{repo}/issues/{number}/comments",
        method="POST",
        body=json.dumps({"body": stamped}),
    )
    if not isinstance(created, dict) or not created.get("id"):
        raise CommentFailed(repo, number, f"the post returned no comment id: {created!r}")
    return True
