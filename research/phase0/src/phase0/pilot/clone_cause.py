"""Why a clone failed, as one of four causes that bound the estimand differently.

WHAT: `clone_failure_stage` classifies a `CloneFailed` message; `rows_for_clone_failure`
      turns the PRs that failed clone into one journal row each, carrying that cause.
WHY:  Split out of `pilot/covariates.py`, which had reached its 200-line cap holding two
      concerns: what was measured about an ATTEMPT, and why a REPOSITORY never opened.

      Four causes, and the size medians say they are not one thing. Across the 200
      walked repositories, against a 423-star baseline median:

          clone_timeout      16,245 stars   38.4x   our bound against their size
          git_lfs_absent      2,325           5.5x   OUR machine; not attrition at all
          transport_failure     590           1.4x   network; retryable
          repo_gone             194           0.5x   corpus staleness, no size to measure

      Pooling them puts a repository with no measurable size into the median that
      quantifies the size bias -- and the single-substring test this replaced did worse
      than pool them, filing `git_lfs_absent` under `repo_gone` at eleven times that
      bucket's median. A48.
IMPORTS: phase0.handlabel.select, phase0.pilot.{attempt,covariates},
      phase0.pipeline.{rejection,worktree}.
CONSUMED BY: pilot/run.py; tests/pilot/test_clone_cause.py.
"""

from __future__ import annotations

from collections.abc import Sequence

from phase0.handlabel.select import Candidate
from phase0.pilot.attempt import Attempt
from phase0.pilot.covariates import attempt_for
from phase0.pipeline.rejection import Rejection
from phase0.pipeline.worktree import CloneFailed

# Ordered, and the order is the fix. `git-lfs: command not found` contains "not found",
# so the single substring test this replaced classified a MISSING BINARY ON OUR MACHINE
# as a missing repository -- and put the second-largest failure class into the bucket
# whose docstring says it has no size to measure. The harness cause is tested FIRST so it
# can never be shadowed by a message that merely contains someone else's words.
CLONE_CAUSES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("git_lfs_absent", ("git-lfs",)),
    ("clone_timeout", ("clone exceeded",)),
    ("transport_failure", ("rpc failed", "early eof", "unexpected disconnect")),
    ("repo_gone", ("not found", "could not read", "access denied")),
)


def clone_failure_stage(exc: CloneFailed) -> str:
    """Which kind of clone failure this is. FOUR causes, and they must never be pooled.

    Measured across 200 walked repositories against a 423-star baseline median:

        clone_timeout      16,245 stars   38.4x   our bound against their size
        git_lfs_absent      2,325          5.5x   OUR machine; not attrition at all
        transport_failure     590          1.4x   network; retryable
        repo_gone             194          0.5x   corpus staleness, no size to measure

    So a timeout selects hard on the study's own confounder and a deleted repository
    selects on nothing -- and `git_lfs_absent`, at eleven times the median of the bucket
    it used to land in, is a size-selective failure that was being filed as size-free.

    An unrecognised message returns `clone_failed`, which is a real state meaning "we did
    not classify this", never a default cause. A48.
    """
    text = str(exc).lower()
    for stage, needles in CLONE_CAUSES:
        if any(needle in text for needle in needles):
            return stage
    return "clone_failed"


def rows_for_clone_failure(
    candidates: Sequence[Candidate],
    already_noted: Sequence[Attempt],
    exc: CloneFailed,
    stars: dict[str, int],
) -> list[Attempt]:
    """One row per PR the failed clone never reached. Attrition with a cause, not a gap.

    A denominator that moves with the weather makes every later comparison carry noise
    nobody declared. The commit count comes from the CORPUS list, because the API's count
    is fetched inside the clone that just failed -- passing 0 put every clone failure
    outside every band, so `share_lost` read 0.0 and "cannot tell" rendered as
    "nothing lost".
    """
    seen = {a.pr_id for a in already_noted}
    stage = clone_failure_stage(exc)
    return [
        attempt_for(
            c,
            Rejection(str(c.pr_id), stage, str(exc)),
            len(c.commit_shas),
            # `stars` was a parameter this function ACCEPTED AND NEVER READ, hardcoding
            # -1 -- NOT MEASURED -- on every clone-failure row. The star count is the
            # journal's only size proxy, and these are precisely the rows whose size
            # decides whether `clone_failure_stage`'s split does anything: a timeout
            # removes the LARGEST repositories, a deleted one "has no size to measure".
            # Measured off the parquet at 139 repositories, the medians are 16,245 /
            # 1,618 / 590 / 166 stars for timeout / git-lfs / transport / gone against a
            # 449 baseline -- so the split is real AND the journal could not show it,
            # because every row it applies to said -1. The data was in the call site the
            # whole time: `run.py` loads it before the first clone and passes it here.
            # -1 SURVIVES as the default for a repository absent from the table, which is
            # a real state and still means NOT MEASURED. A48.
            stars.get(c.repo, -1),
        )
        for c in candidates
        if str(c.pr_id) not in seen
    ]
