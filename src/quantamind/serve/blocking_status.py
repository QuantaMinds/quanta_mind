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

from quantamind.ingest.publish import commit_status
from quantamind.render.status_check import render
from quantamind.types.checked import Checked
from quantamind.verify.blocking import Standing, decide


def announce(repo: str, head_sha: str, checks: Sequence[Checked], *, enabled: bool) -> Standing:
    """Post the blocking status. Returns what was decided, whether or not anything was written.

    **A CHANGE NOTHING GOVERNED GETS NO STATUS.** Posting `success` where no rule applied puts a
    green tick against a standard nobody wrote, which is the same lie as a green test that asserts
    nothing. The absence is the honest answer, and a required check that never arrives is treated
    by GitHub as pending rather than passed.
    """
    gate = decide(checks)
    if gate.standing is Standing.NOT_DECLARED:
        return gate.standing
    shown = render(gate)
    if not enabled:
        print(f"[gate] rehearsed {shown.state}: {shown.description}", flush=True)
        return gate.standing
    commit_status.post(repo, head_sha, shown.state, shown.description)
    print(f"[gate] {shown.state}: {shown.description}", flush=True)
    return gate.standing
