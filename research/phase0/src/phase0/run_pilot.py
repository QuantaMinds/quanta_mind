"""The pilot: build records from the corpus and report the shape metrics, nothing else.

WHAT: `python -m phase0.run_pilot --repos N`. Walks repositories, resolves each PR's
      parent, re-derives its file set, applies the admission gate, and prints where the
      corpus lost rows and why.
WHY:  The pilot exists to answer "is the instrument measuring what we think" before any
      compute is spent on the full run. It deliberately stops at record construction:
      exposure classification and the outcome scan are the next stage, and a pilot that
      produced a relative risk would invite reading it.

      Every metric printed is an attrition count. The one that matters most is the
      file-set disagreement rate, because A24 measured the corpus attributing 92 `.py`
      files to a pull request that changed two -- if that rate is high, the corpus is
      not usable as shipped and no downstream number means anything.

      Needs a GitHub token. `require_token` fails loudly rather than falling back to
      unauthenticated requests, which at 60/hour would look like a working run while
      silently dropping most of the corpus.
IMPORTS: phase0.{github_pulls,handlabel.select}, phase0.pipeline.{assemble,worktree}.
CONSUMED BY: `just pilot`.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from phase0.extract_prs import PRRecord
from phase0.github_pulls import merge_info, require_token
from phase0.handlabel.select import Candidate, eligible_prs
from phase0.pipeline.assemble import Rejection, build_record
from phase0.pipeline.worktree import CloneFailed, cloned

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "data" / "AIDev_BC_Analyser.zip"
WORKSPACE = ROOT / "data" / "pilot_clones"
CACHE = ROOT / "data" / "gh_cache"


def _by_repo(population: list[Candidate]) -> dict[str, list[Candidate]]:
    grouped: dict[str, list[Candidate]] = {}
    for candidate in population:
        grouped.setdefault(candidate.repo, []).append(candidate)
    return grouped


def _report(
    records: list[PRRecord], rejects: list[Rejection], clone_failures: int, repos: int
) -> dict[str, object]:
    stages = Counter(r.stage for r in rejects)
    attempted = len(records) + len(rejects)
    disagreements = [r for r in rejects if r.stage == "file_set"]
    symbols = [len(r.changed_symbols) for r in records]
    files = [len(r.changed_files) for r in records]
    return {
        "repositories_visited": repos,
        "clone_failures": clone_failures,
        "prs_attempted": attempted,
        "records_built": len(records),
        "admission_rate": round(len(records) / attempted, 4) if attempted else 0.0,
        "rejected_by_stage": dict(stages),
        "file_set_disagreement_rate": round(len(disagreements) / attempted, 4)
        if attempted
        else 0.0,
        "records_with_no_symbols": sum(1 for s in symbols if s == 0),
        "median_changed_files": sorted(files)[len(files) // 2] if files else 0,
        "median_changed_symbols": sorted(symbols)[len(symbols) // 2] if symbols else 0,
        "distinct_repos_in_records": len({r.repo for r in records}),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pilot: build records and report shape.")
    parser.add_argument("--repos", type=int, default=10)
    parser.add_argument("--per-repo", type=int, default=4)
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "pilot.json")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    token = require_token()
    population = eligible_prs(PACKAGE)
    grouped = _by_repo(population)
    chosen = sorted(grouped)[: args.repos]
    print(f"{len(population)} eligible PRs across {len(grouped)} repos; taking {len(chosen)}")

    records: list[PRRecord] = []
    rejects: list[Rejection] = []
    clone_failures = 0

    for position, repo in enumerate(chosen, start=1):
        candidates = grouped[repo][: args.per_repo]
        print(f"[{position}/{len(chosen)}] {repo} ({len(candidates)} PRs)", flush=True)
        try:
            with cloned(repo, WORKSPACE) as clone:
                for candidate in candidates:
                    merge = merge_info(repo, candidate.number, str(candidate.pr_id), CACHE, token)
                    if merge is None:
                        rejects.append(
                            Rejection(str(candidate.pr_id), "merge_metadata", "PR or repo gone")
                        )
                        continue
                    outcome = build_record(
                        clone,
                        merge,
                        pr_id=str(candidate.pr_id),
                        repo=repo,
                        merged_at=candidate.merged_at,
                        corpus_files=candidate.changed_files,
                    )
                    if isinstance(outcome, Rejection):
                        rejects.append(outcome)
                        print(f"     #{candidate.number}: rejected [{outcome.stage}]", flush=True)
                    else:
                        records.append(outcome)
                        print(
                            f"     #{candidate.number}: {len(outcome.changed_files)} files, "
                            f"{len(outcome.changed_symbols)} symbols",
                            flush=True,
                        )
        except CloneFailed as exc:
            clone_failures += 1
            print(f"     clone failed: {exc}", flush=True)

    summary = _report(records, rejects, clone_failures, len(chosen))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("\n" + json.dumps(summary, indent=2))
    print(f"\nwritten to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
