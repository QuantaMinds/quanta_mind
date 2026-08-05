"""The pilot: build records from the corpus and report the shape metrics, nothing else.

WHAT: `python -m phase0.pilot.run --repos N`. Walks repositories, resolves each PR's
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

import json
import sys

from phase0 import arm
from phase0.extract_prs import PRRecord
from phase0.github_pulls import merge_info, require_token
from phase0.handlabel.select import Candidate
from phase0.outcome.scan import scan
from phase0.outcome.window import merge_on_base
from phase0.pilot.attempt import Attempt
from phase0.pilot.covariates import attempt_for
from phase0.pilot.options import CACHE, PACKAGE, ROOT, parse
from phase0.pilot.report import by_repo, default_branch, report, star_counts
from phase0.pilot.targets import choose
from phase0.pipeline import journal, records_file, resume
from phase0.pipeline.assemble import build_record
from phase0.pipeline.rejection import Rejection
from phase0.pipeline.worktree import CloneFailed, cloned, sweep
from phase0.population import for_arm


def main(argv: list[str] | None = None) -> int:
    args = parse(argv if argv is not None else sys.argv[1:])

    token = require_token()
    aidev = ROOT / "data" / "aidev"
    population, claimed = for_arm(args.arm, aidev, PACKAGE)
    # Before the first clone, not after thirty hours. This run's entire 90-repo
    # predecessor was human-arm and every metric it produced was read as the agent arm;
    # nothing objected because no artefact named an arm. `verify` raises unless every
    # id is in the arm the population claims, checked against AIDev's own `agent`
    # column rather than against the filename the population was built from.
    tally = arm.verify([c.pr_id for c in population], claimed, aidev)
    grouped = by_repo(population)
    targets = choose(grouped, args.journal, args.repos, args.only_repo, args.rescan_reason)
    print(f"arm verified: {tally}")
    print(f"{len(population)} eligible across {len(grouped)} repos; {targets.announcement}")

    swept = sweep(args.workspace)
    if swept:
        print(f"swept {swept} clone(s) left by a previous run")
    stars = star_counts(ROOT / "data" / "aidev" / "repository.parquet")
    attempts: list[Attempt] = resume.read_attempts(args.journal)
    clone_failures = 0
    if targets.already:
        print(f"resuming: {len(targets.already)} repos journalled, {len(attempts)} attempts")

    def note(
        candidate: Candidate,
        outcome: PRRecord | Rejection,
        commit_count: int,
        breakage: str = "",
        on_default: bool = True,
        on_base: str = "unknown",
        lines_changed: int = -1,
    ) -> None:
        """One attempt appended. The row itself is built by `covariates.attempt_for`."""
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
            )
        )

    for position, repo in enumerate(targets.chosen, start=1):
        if repo in targets.already:
            continue
        candidates = grouped[repo][: args.per_repo]
        before = len(attempts)
        print(f"[{position}/{len(targets.chosen)}] {repo} ({len(candidates)} PRs)", flush=True)
        try:
            with cloned(repo, args.workspace) as clone:
                for candidate in candidates:
                    merge = merge_info(repo, candidate.number, str(candidate.pr_id), CACHE, token)
                    if merge is None:
                        note(
                            candidate,
                            Rejection(str(candidate.pr_id), "merge_metadata", "PR or repo gone"),
                            0,
                        )
                        continue
                    # BEFORE the gate, on every attempt: the scan only sees survivors,
                    # and all four agentops PRs that exposed the unreachable-merge case
                    # were rejected at `no_python` first. A prevalence taken after the
                    # gate describes the residue and gets quoted as the population.
                    on_base = merge_on_base(clone, merge.merge_commit_sha, merge.base_ref)
                    outcome = build_record(
                        clone,
                        merge,
                        pr_id=str(candidate.pr_id),
                        repo=repo,
                        merged_at=candidate.merged_at,
                        corpus_files=candidate.changed_files,
                    )
                    if not isinstance(outcome, Rejection):
                        # Persisted as built. Every later stage needs a PRRecord and
                        # this run already paid for the clone, the metadata, the parent
                        # and the file set -- discarding them is what made the outcome
                        # scan need a second pass over the corpus.
                        records_file.append(args.records, outcome)
                    breakage = ""
                    if args.scan and not isinstance(outcome, Rejection):
                        # The clone is already open and at the right repository, so the
                        # scan costs a history walk and no network. Doing it in a second
                        # pass would mean cloning every repository twice.
                        breakage = scan(clone, outcome).outcome.value
                    note(
                        candidate,
                        outcome,
                        merge.commit_count,
                        breakage,
                        merge.base_ref == default_branch(repo),
                        on_base,
                        merge.changed_lines,
                    )
                    if isinstance(outcome, Rejection):
                        print(
                            f"     #{candidate.number}: rejected [{outcome.stage}"
                            f"/{outcome.category}]",
                            flush=True,
                        )
                    else:
                        print(
                            f"     #{candidate.number}: {len(outcome.changed_files)} files, "
                            f"{len(outcome.changed_symbols)} symbols"
                            + (f", {breakage}" if breakage else ""),
                            flush=True,
                        )
        except CloneFailed as exc:
            clone_failures += 1
            print(f"     clone failed: {exc}", flush=True)
            # One row per PR, not a gap. A clone failure is attrition with a cause, and
            # a denominator that moves with the weather makes every later comparison
            # carry noise nobody declared.
            #
            # Two causes, kept apart. A timeout removes the LARGEST repositories, so it
            # selects on the study's own confounder; a repository that no longer exists
            # selects on nothing and has no size to measure. Pooling them puts a repo
            # with no measurable size into the median that quantifies the size bias.
            stage = "repo_gone" if "not found" in str(exc).lower() else "clone_timeout"
            for candidate in candidates:
                if not any(a.pr_id == str(candidate.pr_id) for a in attempts[before:]):
                    # The corpus's commit list: the API's count is fetched inside the
                    # clone that just failed, and passing 0 put every clone failure
                    # outside every band, so `share_lost` read 0.0 -- "cannot tell"
                    # rendered as "nothing lost".
                    fail = Rejection(str(candidate.pr_id), stage, str(exc))
                    note(candidate, fail, len(candidate.commit_shas))
        # Flushed here, not at the end. A repository that yielded nothing is still
        # marked done, or a restart would retry it forever.
        journal.append_repo(args.journal, repo, attempts[before:], targets.rescan)

    summary = report(attempts, clone_failures, len(targets.chosen))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("\n" + json.dumps(summary, indent=2))
    print(f"\nwritten to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
