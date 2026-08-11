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

from collections.abc import Callable, Sequence

from phase0.extract_prs import PRRecord
from phase0.handlabel.select import Candidate
from phase0.pilot.attempt import Attempt
from phase0.pipeline.rejection import Rejection


def attempt_for(
    candidate: Candidate,
    outcome: PRRecord | Rejection,
    commit_count: int,
    stars: int,
    breakage: str = "",
    on_default: str = "unknown",
    on_base: str = "unknown",
    lines_changed: int = -1,
    api_files: Sequence[str] | None = None,
    exclusion: str = "",
) -> Attempt:
    """One attempt, with the covariates attrition may track. Never a verdict.

    `arm` comes off the candidate rather than being passed in or defaulted here: the
    population knows which arm it drew, and a row that inferred its own arm would be
    restating an assumption instead of recording a fact.
    """
    corpus_py = sum(1 for f in candidate.changed_files if f.endswith(".py"))
    # None, not 0. These were 0 on every rejected row, which made "derivation never ran"
    # read as "derivation found nothing" -- and a count of rows reading 0 was then
    # arithmetically identical to a count of rejected rows. A `no_symbols` rejection
    # cannot have derived zero files, because `assemble.py` only reaches that branch when
    # `derived` is non-empty, yet it recorded 0 like everything else.
    stage, category = "", ""
    files: int | None = None
    symbols: int | None = None
    if isinstance(outcome, Rejection):
        stage, category = outcome.stage, outcome.category
        if outcome.stage == "no_python":
            # The one stage where zero is a MEASUREMENT: `if not derived` is the rejection.
            files = 0
    else:
        files, symbols = len(outcome.changed_files), len(outcome.changed_symbols)
    # GitHub's own list, recorded rather than consumed and dropped. None when the API gave
    # us nothing -- an empty list and a missing one are different facts. `truncated` is set
    # when the list is exactly one page long, because `github_pulls` fetches one page deep
    # and a list of exactly that length cannot be told from a longer one that was cut.
    gh_files = None if api_files is None else len(api_files)
    gh_py = None if api_files is None else sum(1 for f in api_files if f.endswith(".py"))
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
        github_changed_files=gh_files,
        github_py_files=gh_py,
        # Always False now, and kept rather than dropped so a journal written before
        # pagination still parses. `fetch_all` walks every page and RAISES rather than
        # returning a short list, so a full-page list is complete. Inferring truncation
        # from length after that would flag the largest PRs as suspect for a reason that
        # no longer exists -- the same size selection this field was added to expose.
        github_files_truncated=False,
        stars=stars,
        outcome=breakage,
        base_on_default=on_default,
        merge_on_base=on_base,
        changed_lines=lines_changed,
        arm=candidate.arm,
        exclusion=exclusion,
    )


def recorder(attempts: list[Attempt], stars: dict[str, int]) -> Callable[..., None]:
    """A closure that appends one row per attempt to `attempts`.

    Lives here rather than inside `pilot/run.py` because building a row is this module's
    concern and walking repositories is that one's -- and because run.py had grown past
    its file budget with this closure inside it for the second time.
    """

    def note(
        candidate: Candidate,
        outcome: PRRecord | Rejection,
        commit_count: int,
        breakage: str = "",
        # "unknown", not "yes": a rejected attempt never reached the branch lookup, and
        # defaulting to a measurement is how the two got confused in the first place.
        on_default: str = "unknown",
        on_base: str = "unknown",
        lines_changed: int = -1,
        # None when the API supplied no list; `()` would claim GitHub reported zero files.
        api_files: Sequence[str] | None = None,
        exclusion: str = "",
    ) -> None:
        attempts.append(
            attempt_for(
                candidate,
                outcome,
                commit_count,
                stars.get(candidate.repo, -1),
                breakage,
                on_default,
                on_base,
                lines_changed,
                api_files,
                exclusion,
            )
        )

    return note
