"""The pilot: build records from the corpus and report the shape metrics, nothing else.

WHAT: `python -m phase0.run_pilot --repos N`. Walks repositories, resolves each PR's
      parent, re-derives its file set, applies the admission gate, and prints where the
      corpus lost rows and why.
WHY:  The pilot exists to answer "is the instrument measuring what we think" before any
      compute is spent on the full run. It deliberately stops at record construction:
      exposure classification and the outcome scan are the next stage, and a pilot that
      produced a relative risk would invite reading it.

      Every metric printed is an attrition count, and none is pooled. The first smoke
      run lost 32% of PRs with `parent_commit` dominating, which is shape detection
      failing when the corpus file list does not match the change -- and that tracks
      patch size. Differential exclusion on the study's own confounder is not something
      a single percentage can show, so attrition is cross-tabulated against commit
      count and corpus file count instead.

      Progress is flushed to a markdown journal after every repository and a restart
      resumes from it. The full run is over thirty hours; holding results in memory
      until the end means a dropped connection costs the whole thing twice.

      Needs a GitHub token. `require_token` fails loudly rather than falling back to
      unauthenticated requests, which at 60/hour would look like a working run while
      silently dropping most of the corpus.
IMPORTS: pandas, phase0.{github_pulls,handlabel.select,pilot_report},
      phase0.pipeline.{assemble,worktree}.
CONSUMED BY: `just pilot`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from phase0.extract_prs import PRRecord
from phase0.github_pulls import merge_info, require_token
from phase0.handlabel.select import Candidate, eligible_prs
from phase0.pilot_report import Attempt, report
from phase0.pipeline import journal
from phase0.pipeline.assemble import Rejection, build_record
from phase0.pipeline.worktree import CloneFailed, cloned

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_TABLE = ROOT / "data" / "aidev" / "repository.parquet"
PACKAGE = ROOT / "data" / "AIDev_BC_Analyser.zip"
WORKSPACE = ROOT / "data" / "pilot_clones"
CACHE = ROOT / "data" / "gh_cache"


def _by_repo(population: list[Candidate]) -> dict[str, list[Candidate]]:
    grouped: dict[str, list[Candidate]] = {}
    for candidate in population:
        grouped.setdefault(candidate.repo, []).append(candidate)
    return grouped


def _stars() -> dict[str, int]:
    """Star count per repository, for the star-band split the human arm needs.

    Returns empty when the table is absent rather than failing: the band is reported as
    `unknown`, which is visibly different from reporting a band we did not measure.
    """
    if not REPOSITORY_TABLE.is_file():
        return {}
    frame = pd.read_parquet(REPOSITORY_TABLE)
    return {str(r.full_name): int(r.stars) for r in frame.itertuples() if r.full_name}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pilot: build records and report shape.")
    parser.add_argument("--repos", type=int, default=10)
    parser.add_argument("--per-repo", type=int, default=4)
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "pilot.json")
    parser.add_argument(
        "--journal",
        type=Path,
        default=ROOT / "results" / "pilot_journal.md",
        help="append-only progress, flushed per repository; a restart resumes from it",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    token = require_token()
    population = eligible_prs(PACKAGE)
    grouped = _by_repo(population)
    chosen = sorted(grouped)[: args.repos]
    print(f"{len(population)} eligible PRs across {len(grouped)} repos; taking {len(chosen)}")

    stars = _stars()
    already = journal.completed_repos(args.journal)
    attempts: list[Attempt] = journal.read_attempts(args.journal)
    clone_failures = 0
    if already:
        print(f"resuming: {len(already)} repos already journalled, {len(attempts)} attempts")

    def note(
        candidate: Candidate,
        outcome: PRRecord | Rejection,
        commit_count: int,
    ) -> None:
        """One attempt, with the covariates attrition may track. Never a verdict."""
        corpus_py = sum(1 for f in candidate.changed_files if f.endswith(".py"))
        stage, category, files, symbols = "", "", 0, 0
        if isinstance(outcome, Rejection):
            stage, category = outcome.stage, outcome.category
        else:
            files, symbols = len(outcome.changed_files), len(outcome.changed_symbols)
        attempts.append(
            Attempt(
                pr_id=str(candidate.pr_id),
                repo=candidate.repo,
                admitted=not isinstance(outcome, Rejection),
                stage=stage,
                category=category,
                commit_count=commit_count,
                corpus_py_files=corpus_py,
                derived_files=files,
                changed_symbols=symbols,
                stars=stars.get(candidate.repo, -1),
            )
        )

    for position, repo in enumerate(chosen, start=1):
        if repo in already:
            continue
        candidates = grouped[repo][: args.per_repo]
        before = len(attempts)
        print(f"[{position}/{len(chosen)}] {repo} ({len(candidates)} PRs)", flush=True)
        try:
            with cloned(repo, WORKSPACE) as clone:
                for candidate in candidates:
                    merge = merge_info(repo, candidate.number, str(candidate.pr_id), CACHE, token)
                    if merge is None:
                        note(
                            candidate,
                            Rejection(str(candidate.pr_id), "merge_metadata", "PR or repo gone"),
                            0,
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
                    note(candidate, outcome, merge.commit_count)
                    if isinstance(outcome, Rejection):
                        print(
                            f"     #{candidate.number}: rejected [{outcome.stage}"
                            f"/{outcome.category}]",
                            flush=True,
                        )
                    else:
                        print(
                            f"     #{candidate.number}: {len(outcome.changed_files)} files, "
                            f"{len(outcome.changed_symbols)} symbols",
                            flush=True,
                        )
        except CloneFailed as exc:
            clone_failures += 1
            print(f"     clone failed: {exc}", flush=True)
        # Flushed here, not at the end. A repository that yielded nothing is still
        # marked done, or a restart would retry it forever.
        journal.append_repo(args.journal, repo, attempts[before:])

    summary = report(attempts, clone_failures, len(chosen))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("\n" + json.dumps(summary, indent=2))
    print(f"\nwritten to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
