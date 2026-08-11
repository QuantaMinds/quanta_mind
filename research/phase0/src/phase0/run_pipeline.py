"""Orchestration: clone once per repo, measure each PR, record it immediately.

WHAT: Drives the exposure pass — grouped by repository, checkpointed, isolated per
      PR — and appends one audit line each time a PR completes.
WHY:  `PHASE0_RUNBOOK.md` “Days 3-5” invokes this by name. It is separate from the measurement
stages
      because the audit log is the study's evidence trail and must be written by
      one place with one schema.

      Five properties, each chosen because getting it wrong costs a re-run:

      1. Grouped by repository, cloned once. ~3,300 PRs live in a few hundred
         repositories; cloning per PR is the largest avoidable cost in the study.
      2. Deterministic order — sorted by (repo, pr_id) — so a partial run is a
         PREFIX of the full run. Pilot and full results are then comparable rather
         than two arbitrary samples.
      3. Append-only checkpoint. A restart skips completed ids, so preemption and
         reboots are survivable rather than fatal at hour 28.
      4. Failure isolation at this level too. run_graph returns statuses instead of
         raising; the orchestrator owes the loop the same, and records WHICH stage
         failed — "PR 4821 failed" is useless at hour 30.
      5. Pilot mode returns operational counts ONLY. Computing the 2x2 is a
         separate command, so nobody can glance at an effect size before the
         controls have cleared.

      Never imports scan_outcome. Outcomes are scanned in a separate pass so
      nothing here can see whether a PR broke — the leakage `PHASE0_RUNBOOK.md` “Exposure classifier
      tests” calls the
      likeliest way to fake a positive by accident. tests/test_run_pipeline.py
      asserts that import is absent.
IMPORTS: phase0.extract_prs, pycg_failure, run_graph, and
      pipeline.{measure,record,worktree}. Never phase0.scan_outcome.
CONSUMED BY: the run itself; tests/test_run_pipeline.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from phase0.extract_prs import PRRecord
from phase0.graph.pycg_failure import GraphStatus
from phase0.graph.run_graph import DEFAULT_TIMEOUT_S, HarnessError
from phase0.pipeline import record, worktree
from phase0.pipeline.measure import measure

PILOT_REPOS = 30


@dataclass(frozen=True, slots=True)
class RunSummary:
    """Operational counts. Deliberately not a result.

    Carries no arm counts and no ratio, so a pilot cannot surface an effect size
    even by accident. `PHASE0_RUNBOOK.md` “Day 2” requires the controls to clear first.
    """

    prs_seen: int = 0
    prs_recorded: int = 0
    prs_skipped: int = 0  # already in the checkpoint
    clone_failures: int = 0
    stage_failures: int = 0


def group_by_repo(prs: Sequence[PRRecord]) -> dict[str, list[PRRecord]]:
    """Deterministic grouping, so a partial run is a prefix of the full one."""
    grouped: dict[str, list[PRRecord]] = {}
    for pr in sorted(prs, key=lambda p: (p.repo, p.pr_id)):
        grouped.setdefault(pr.repo, []).append(pr)
    return dict(sorted(grouped.items()))


def failed(pr: PRRecord, stage: str, reason: str) -> record.PRAudit:
    """A record naming WHICH stage failed. 'PR 4821 failed' is useless at hour 30.

    The parent resolution is copied from the RECORD rather than taken as an argument.
    It was a `MergeShape | None` parameter filled from a resolution this function's
    callers performed themselves; now that nothing here resolves, a parameter would be
    a vestige that only ever received None -- present, plausible and always empty.
    """
    return record.PRAudit(
        pr_id=pr.pr_id,
        repo=pr.repo,
        repo_id=pr.repo_id,
        arm=pr.arm,
        task_type=pr.task_type,
        merged_sha=pr.merged_sha,
        parent_resolution_method=pr.parent_resolution_method,
        parent_resolution_rule=pr.parent_resolution_rule,
        graph_status=GraphStatus.CRASHED.value if stage == "unexpected" else "",
        stage_failed=stage,
        error=reason[:300],
    )


def one_pr(clone: Path, pr: PRRecord, slot: int, timeout_s: int) -> record.PRAudit:
    """One PR, fully isolated. Every failure becomes a record, never an exception.

    CONSUMES the record's parent. It does not re-resolve one.

    The version that re-resolved called `parent_commit.resolve` with the PR's FILE
    COUNT in the commit-count slot -- the substitution `assemble.build_record`'s own
    docstring says A24 forbade -- and omitted `pr_commit_subjects` entirely, so
    `by_subject` returned None every time and the corpus-derived file rules decided
    every PR. It then overwrote a `parent_sha` the record already carried, resolved by
    `assemble` from the API's subjects and true commit count. A caller rebuilding what
    it was handed, which is the `_as_record` defect in the pipeline's own entry point.
    """
    try:
        if not pr.parent_sha:
            # Typed, not recomputed. A record with no parent is malformed -- `assemble`
            # cannot emit one -- and re-deriving it here would turn a corrupt input into
            # a plausible measurement, which is the failure this whole file guards.
            return failed(pr, "parent_commit", "record carries no parent_sha")

        with worktree.at_commit(clone, pr.parent_sha, str(slot)) as tree:
            if tree is None:
                return failed(pr, "worktree", "parent commit unavailable")
            audit = measure(tree, pr, timeout_s)
            if audit is None:
                return failed(pr, "scope", "no analysable Python at the parent")
            return replace(
                audit,
                parent_sha=pr.parent_sha,
                # Empty on a records file written before these fields existed. That is
                # UNRECORDED and must never be read as "ambiguous" or as "checked".
                parent_resolution_method=pr.parent_resolution_method,
                parent_resolution_rule=pr.parent_resolution_rule,
            )
    except HarnessError:
        # Ahead of the catch-all on purpose. Our environment failing is not this PR
        # failing, and recording it as attrition is how a broken machine produces a
        # complete-looking corpus. Stop instead.
        raise
    except Exception as exc:
        return failed(pr, "unexpected", f"{type(exc).__name__}: {exc}")


def run(
    prs: Sequence[PRRecord],
    out: Path,
    workspace: Path,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    pilot: bool = False,
) -> RunSummary:
    """Process every PR, appending one audit record as each completes.

    Never raises for data. Returns operational counts only — see RunSummary.
    """
    done = record.completed_ids(out)
    grouped = group_by_repo(prs)
    if pilot:
        grouped = dict(list(grouped.items())[:PILOT_REPOS])

    seen = recorded = skipped = clone_failures = stage_failures = 0

    # SERIAL over repositories, and that is load-bearing rather than incidental.
    # GitHub's 100-concurrent and 900-points-per-minute ceilings are per ACCOUNT, not
    # per process, so parallel repositories would share one budget and exhaust each
    # other's -- surfacing as 403s that the retry policy would absorb as slowness until
    # it could not. Parallelise the clone-and-analyse work if it is ever needed; the
    # fetches must stay serialised, or revisit the rate-limit handling first.
    for repo_name, repo_prs in grouped.items():
        pending = [p for p in repo_prs if p.pr_id not in done]
        seen += len(repo_prs)
        skipped += len(repo_prs) - len(pending)
        if not pending:
            continue

        try:
            with worktree.cloned(repo_name, workspace) as clone:
                for index, pr in enumerate(pending):
                    audit = one_pr(clone, pr, index, timeout_s)
                    record.append(out, audit)
                    recorded += 1
                    stage_failures += 0 if audit.succeeded else 1
        except worktree.CloneFailed as exc:
            clone_failures += len(pending)
            for pr in pending:
                record.append(out, failed(pr, "clone", str(exc)))
                recorded += 1
                stage_failures += 1

    return RunSummary(seen, recorded, skipped, clone_failures, stage_failures)
