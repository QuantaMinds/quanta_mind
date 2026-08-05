"""One attempt's covariate row, assembled from a candidate and what happened to it.

WHAT: `attempt_for` -- turns a `Candidate` plus its outcome into the `Attempt` the
      journal writes, filling every covariate a later cross-tabulation reads.
WHY:  Split from `pilot/run.py`, which owns the walk: choosing repositories, cloning,
      checkpointing, resuming. Building a row is not walking, and the walk had grown
      past its file budget with this closure inside it.

      Worth separating on its own merits. Every field here is one that cannot be
      recovered without re-running the corpus, and the rule they share is that a value
      meaning NOT MEASURED must never be one that could pass as a measurement --
      `stars=-1` for a repository AIDev does not list, `arm` carried from the candidate
      rather than defaulted, `outcome=""` for a PR that was never scanned. A row is
      built for EVERY attempt, admitted or rejected, because the outcome scan only ever
      sees survivors and a covariate counted after the gate describes the residue.
IMPORTS: phase0.extract_prs, phase0.handlabel.select, phase0.pilot.attempt,
      phase0.pipeline.rejection, phase0.pipeline.worktree.
CONSUMED BY: pilot/run.py; tests/pilot/test_covariates.py.
"""

from __future__ import annotations

from collections.abc import Sequence

from phase0.extract_prs import PRRecord
from phase0.handlabel.select import Candidate
from phase0.pilot.attempt import Attempt
from phase0.pipeline.rejection import Rejection
from phase0.pipeline.worktree import CloneFailed


def attempt_for(
    candidate: Candidate,
    outcome: PRRecord | Rejection,
    commit_count: int,
    stars: int,
    breakage: str = "",
    on_default: str = "unknown",
    on_base: str = "unknown",
    lines_changed: int = -1,
) -> Attempt:
    """One attempt, with the covariates attrition may track. Never a verdict.

    `arm` comes off the candidate rather than being passed in or defaulted here: the
    population knows which arm it drew, and a row that inferred its own arm would be
    restating an assumption instead of recording a fact.
    """
    corpus_py = sum(1 for f in candidate.changed_files if f.endswith(".py"))
    stage, category, files, symbols = "", "", 0, 0
    if isinstance(outcome, Rejection):
        stage, category = outcome.stage, outcome.category
    else:
        files, symbols = len(outcome.changed_files), len(outcome.changed_symbols)
    return Attempt(
        pr_id=str(candidate.pr_id),
        repo=candidate.repo,
        admitted=not isinstance(outcome, Rejection),
        stage=stage,
        category=category,
        commit_count=commit_count,
        corpus_py_files=corpus_py,
        derived_files=files,
        changed_symbols=symbols,
        stars=stars,
        outcome=breakage,
        base_on_default=on_default,
        merge_on_base=on_base,
        changed_lines=lines_changed,
        arm=candidate.arm,
    )


def clone_failure_stage(exc: CloneFailed) -> str:
    """Which kind of clone failure this is. The two must never be pooled.

    A timeout removes the LARGEST repositories, so it selects on the study's own
    confounder. A repository that no longer exists selects on nothing and has no size to
    measure. Pooling them puts a repo with no measurable size into the median that
    quantifies the size bias.
    """
    return "repo_gone" if "not found" in str(exc).lower() else "clone_timeout"


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
        attempt_for(c, Rejection(str(c.pr_id), stage, str(exc)), len(c.commit_shas), stars=-1)
        for c in candidates
        if str(c.pr_id) not in seen
    ]
