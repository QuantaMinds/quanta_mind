"""The exposure pass, with a command line  -- `python -m phase0.exposure_run`.

WHAT: Loads persisted `PRRecord`s and drives `run_pipeline.run` over them, writing one
      audit row per PR and resuming from what is already written.
WHY:  `run_pipeline` had no `__main__`, so the runbook's "Days 3-5" command executed the
      module body, ignored every flag, wrote nothing and exited 0. The functions were real
      and tested; nothing invoked them. This module is that entry point, kept separate so
      `run_pipeline` stays a library and the argument surface has one home.

      **A16 is why this cannot be skipped.** The 2x2 is complete-case, and whether a pooled
      relative risk is quotable at all depends on how exposure relates to patch size on the
      corpus that actually survived. The corpus has moved twice  -- the shape rule changed
      which PRs are admitted, and the base-branch fix changed which outcomes exist  -- so
      this must run on the FINAL corpus and not on any earlier one.

      Resume is per PR, not per repository. PyCG runs at a 600-second timeout with roughly
      a 78% success rate, so a single repository can be an hour of work; losing that to a
      reboot at hour twenty-nine is avoidable, and `run_pipeline.run` already skips ids
      present in the output. This module's job is to make that reachable from a shell.

      It prints operational counts only. Computing a 2x2 here would let somebody read an
      effect size before the controls have cleared, which `PHASE0_RUNBOOK.md` "Day 2"
      forbids  -- `analysis/build_table.py` is where that happens, deliberately elsewhere.
IMPORTS: phase0.run_pipeline, phase0.pipeline.records_file, phase0.graph.run_graph.
CONSUMED BY: `python -m phase0.exposure_run`; tests/test_exposure_run.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from phase0.extract_prs import PRRecord
from phase0.github_pulls import require_token
from phase0.graph.run_graph import DEFAULT_TIMEOUT_S
from phase0.pipeline import record, records_file, worktree
from phase0.pipeline.rebuild import records_for
from phase0.pipeline.rejection import Rejection
from phase0.run_pipeline import run

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "data" / "AIDev_BC_Analyser.zip"
CACHE = ROOT / "data" / "gh_cache"


def parse(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exposure pass over persisted PRRecords.")
    parser.add_argument(
        "--records",
        type=Path,
        default=ROOT / "results" / "records.jsonl",
        help="PRRecords written by the pilot; produced by `pilot.run --records`",
    )
    parser.add_argument(
        "--from-journal",
        type=Path,
        default=None,
        help="rebuild records from a pilot journal when none were persisted; the clone "
        "this pass already needs is where they get rebuilt, so it costs no extra sweep",
    )
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "exposure.jsonl")
    parser.add_argument("--workspace", type=Path, default=ROOT / "data" / "exposure_clones")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="first N repositories only, for a smoke run",
    )
    return parser.parse_args(argv)


def _rebuild(args: argparse.Namespace) -> list[PRRecord]:
    """Records the journal says were admitted, rebuilt where the clone is already open.

    Rejections are counted and reported, never dropped: the journal states these were
    admitted, so a silent loss here would shrink the corpus below what it reports and
    nothing would say by how much.
    """
    built: list[PRRecord] = []
    refused: list[Rejection] = []

    def clone_for(repo: str):  # type: ignore[no-untyped-def]
        return worktree.cloned(repo, args.workspace)

    for _, outcome in records_for(args.from_journal, PACKAGE, CACHE, require_token(), clone_for):
        if isinstance(outcome, Rejection):
            refused.append(outcome)
        else:
            built.append(outcome)
            records_file.append(args.records, outcome)

    print(f"rebuilt {len(built)} records from {args.from_journal}", flush=True)
    if refused:
        stages = Counter(r.stage for r in refused)
        print(f"  {len(refused)} admitted rows would not rebuild: {dict(stages)}", flush=True)
    return built


def main(argv: list[str] | None = None) -> int:
    args = parse(argv if argv is not None else sys.argv[1:])

    prs = records_file.read(args.records)
    if not prs and args.from_journal:
        prs = _rebuild(args)
    if not prs:
        # Loud, and non-zero. An exposure pass over nothing would otherwise write an empty
        # file, print a tidy zero, and exit 0 -- the failure this entry point exists to end.
        print(
            f"no usable records in {args.records} and no --from-journal given. Either run "
            f"`python -m phase0.pilot.run --records {args.records}` or pass "
            f"--from-journal <pilot journal>; a pass over zero PRs is not a result.",
            file=sys.stderr,
        )
        return 2

    # A54's population assertion, and it RAISES rather than filtering. The 2026-08-05
    # pass consumed 17 rows that were every one arm=human, every one rejected at
    # clone_failed, none an admitted unit -- and produced a tidy file that nobody
    # questioned until a human read it. Filtering would have written a smaller tidy file.
    #
    # Checked on the artefact this consumer READS, not on the input that produced it:
    # `arm.verify` already checks the population before the first clone and passed while
    # every persisted record said `human`, because the two are one layer apart.
    wrong_arm = sorted({p.arm or "<empty>" for p in prs if p.arm.lower() == "human" or not p.arm})
    no_parent = [p.pr_id for p in prs if not p.parent_sha]
    if wrong_arm or no_parent:
        raise ValueError(
            f"population assertion failed on {args.records}: "
            f"{len(wrong_arm)} distinct human/empty arm value(s) {wrong_arm}, "
            f"{len(no_parent)} record(s) with no parent_sha (first: {no_parent[:3]}). "
            f"A PRRecord carrying the wrong arm produces an audit carrying the wrong arm, "
            f"and nothing downstream re-checks it. Fix the records, do not filter them."
        )
    print(
        f"population asserted: {len(prs)} records, arms {sorted({p.arm for p in prs})}", flush=True
    )

    already = len(record.completed_ids(args.out))
    print(f"{len(prs)} records, {already} already audited in {args.out}", flush=True)

    summary = run(prs, args.out, args.workspace, args.timeout, args.pilot)
    print(json.dumps(summary.__dict__, indent=2, sort_keys=True))
    print(f"\nwritten to {args.out}")
    # Operational counts only, by design: no arm counts, no ratio, no effect size.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
