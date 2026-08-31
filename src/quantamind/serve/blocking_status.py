"""Put the rule verdict on the commit, so a failing standard stops a merge, not describes one.

WHAT: `announce(repo, head_sha, checks, enabled=...)` decides the gate from the audit rows, renders
      it, and posts one commit status. Returns the `Standing` so a caller can log what happened,
      including when nothing was posted.
WHY:  **THIS IS THE ONLY PLACE THE THREE LAYERS MEET, AND IT IS THE ONLY PLACE THEY MAY.**
      `verify/blocking.py` decides with no network, `render/status_check.py` phrases it, and
      `ingest/publish/commit_status.py` writes it knowing nothing about either. Each of those sits
      to the left of the next, so only `serve/` can hold all three at once. Putting the join
      anywhere else would be the sideways import the layering rule exists to stop.

      **ONLY A REPRODUCIBLE CHECK MAY BLOCK.** What reaches `state="failure"` is exactly the
      `Outcome.VIOLATED` rows, and `verify/rule_check.check` returns `DEFERRED` for a model-judged
      rule before any path that can construct a violation. Raw model findings measure 66.7 to
      82.1% wrong; a verdict at that error rate may inform a reviewer and must never hold a merge.

      **IT CHECKS `POSTING_ENABLED` ITSELF RATHER THAN INHERITING THE COMMENT'S CHECK.** The caller
      returns early on rehearsal for the comment path, and a writer that relies on somebody else's
      early return is a writer that posts the day somebody reorders the function. During a
      rehearsal the gate is still computed and printed, because what the status WOULD have said is
      the thing an operator is rehearsing to find out.
IMPORTS: types.checked, verify.blocking, render.status_check, ingest.publish.commit_status --
      each strictly to the left of `serve`.
CONSUMED BY: `serve/review_delivery.py`, once the rule checks have been recorded.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from quantamind.ingest.publish import commit_status
from quantamind.render.status_check import render
from quantamind.types.checked import Checked
from quantamind.verify.blocking import Standing, decide


class Wrote(Enum):
    """What became of the status. **Four outcomes, never one boolean.**

    "Nothing was declared", "we rehearsed", and "GitHub refused us" are three different facts and a
    `posted: bool` reports all three as False. A caller that cannot tell a refusal from a rehearsal
    cannot alert on the one that matters.
    """

    POSTED = "posted"
    NOTHING_DECLARED = "nothing_declared"
    REHEARSED = "rehearsed"
    REFUSED = "refused"


@dataclass(frozen=True, slots=True)
class Announced:
    """What was decided and what became of publishing it."""

    standing: Standing
    wrote: Wrote
    refusal: str = ""
    """GitHub's own words when `wrote is REFUSED`, empty otherwise."""

    def __post_init__(self) -> None:
        if (self.wrote is Wrote.REFUSED) != bool(self.refusal):
            raise ValueError("a refusal must carry GitHub's reason, and only a refusal may")


def announce(repo: str, head_sha: str, checks: Sequence[Checked], *, enabled: bool) -> Announced:
    """Post the blocking status. **Never raises: the review must survive this failing.**

    **A STATUS THAT CANNOT BE PUBLISHED MUST NOT TAKE THE REVIEW WITH IT.** This runs before the
    review comment is posted, so an exception here costs the customer the whole review -- and the
    first thing tried against a real repository was a 403, because the App had no `statuses`
    permission. Every unit test missed it: they replace the writer with a spy that returns True.
    `verify/rule_check.enforce` already states this reasoning for the audit trail; the same holds
    here, and more sharply, because the gate is the newer and less important of the two writes.

    **THE REFUSAL IS RETURNED AND PRINTED, NOT SWALLOWED.** A gate that silently stops publishing
    is a gate that reports success by saying nothing -- the failure this codebase exists to refuse.

    **A CHANGE NOTHING GOVERNED GETS NO STATUS.** Posting `success` where no rule applied puts a
    green tick against a standard nobody wrote.
    """
    gate = decide(checks)
    if gate.standing is Standing.NOT_DECLARED:
        return Announced(gate.standing, Wrote.NOTHING_DECLARED)
    shown = render(gate)
    if not enabled:
        print(f"[gate] rehearsed {shown.state}: {shown.description}", flush=True)
        return Announced(gate.standing, Wrote.REHEARSED)
    try:
        commit_status.post(repo, head_sha, shown.state, shown.description)
    except commit_status.StatusFailed as exc:
        print(f"[gate] NOT PUBLISHED — {exc.reason}; the review is posted anyway", flush=True)
        return Announced(gate.standing, Wrote.REFUSED, exc.reason)
    print(f"[gate] {shown.state}: {shown.description}", flush=True)
    return Announced(gate.standing, Wrote.POSTED)
