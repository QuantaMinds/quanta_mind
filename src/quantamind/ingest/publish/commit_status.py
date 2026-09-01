"""The commit status that can hold a merge. It writes a verdict; it does not reach one.

WHAT: `post(repo, head_sha, state, description)` writes one commit status and returns True when
      GitHub accepted it. `STATES` is the set it will accept; anything else raises here rather
      than becoming a 422 nobody reads.
WHY:  **A COMMENT CAN BE SCROLLED PAST; A REQUIRED CHECK CANNOT.** The claim this product makes is
      that code meets a declared standard before a human reviewer spends attention on it. A
      comment offers that claim; a status check that fails makes it. This is the only surface here
      that can stop a merge.

      **IT KNOWS NOTHING ABOUT WHAT BLOCKS, AND THAT IS THE LAYERING, NOT A STYLE CHOICE.**
      `verify/blocking.py` decides and `render/blocks/status_check.py` phrases it -- both sit to
      the RIGHT of `ingest` in the layer order, so a writer that imported either would be the
      sideways reach the rule exists to stop. It takes a state and a sentence and posts them. The
      upside is that the thing which can block a customer's merge is decided in a module with no
      network in it.

      **`POSTING_ENABLED` IS NOT CHECKED HERE.** Nothing under `ingest/publish/` consults it; the
      caller does, at its own call site. A second writer inheriting the first one's gate is a gate
      nobody wrote, so `serve/review_delivery.py` checks it again before calling this.
IMPORTS: stdlib json, plus `ingest.github_api` for the authenticated call. Nothing to its right.
CONSUMED BY: `serve/review_delivery.py`, after the review comment is posted.
"""

from __future__ import annotations

import json

from quantamind.ingest import github_api

CONTEXT = "quantamind/declared-rules"
"""The check's name in GitHub's UI and in a branch protection rule. **Changing it silently
un-protects every branch that requires the old name**: a required context that never arrives blocks
forever, and an administrator will drop the requirement rather than wait."""

DESCRIPTION_LIMIT = 140
"""GitHub truncates a longer description without saying so. We truncate deliberately instead."""

STATES = frozenset({"success", "failure", "pending", "error"})
"""What GitHub accepts. A typo becomes a 422 whose body nobody reads, so it is refused here."""


class StatusFailed(RuntimeError):
    """The status could not be written. Carries the repository, the head and the reason."""

    def __init__(self, repo: str, head_sha: str, reason: str) -> None:
        super().__init__(f"could not post a status to {repo}@{head_sha[:7]}: {reason}")
        self.repo, self.head_sha, self.reason = repo, head_sha, reason


def post(repo: str, head_sha: str, state: str, description: str) -> bool:
    """Write one commit status against `head_sha`. True when GitHub accepted it.

    **THE SHA IS THE HEAD OF THE PULL REQUEST, NOT THE BASE AND NOT A MERGE COMMIT.** A status on
    any other commit is invisible to branch protection, which watches the head -- it would post
    successfully, report nothing, and block nothing. The caller passes the same `head_sha` the
    review comment was anchored to, so the two surfaces cannot disagree about which commit was
    reviewed.
    """
    if state not in STATES:
        raise ValueError(
            f"{state!r} is not a status GitHub accepts; expected one of {sorted(STATES)}"
        )
    payload = {
        "state": state,
        "context": CONTEXT,
        "description": description[:DESCRIPTION_LIMIT],
    }
    try:
        github_api.call(
            repo, f"repos/{repo}/statuses/{head_sha}", method="POST", body=json.dumps(payload)
        )
    except github_api.ApiFailed as exc:
        raise StatusFailed(repo, head_sha, exc.reason) from None
    return True
