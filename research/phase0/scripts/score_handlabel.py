"""Score the hand labels against the classifier — the step that must run last.

WHAT: Reads the completed answers, runs `scan_outcome.scan` over the same twenty PRs,
      and prints agreement against `PHASE0_PREREGISTRATION.md` “Timeline” >=16/20 gate with kappa
      and the label
      distribution beside it.
WHY:  Separate from sheet generation so that producing the evidence and producing the
      verdict are two commands a person runs in order, not one command that could emit
      both. `read_labels` refuses an incomplete file, so this cannot be run early to
      "just have a look" without first committing to twenty answers.

      The parent SHA is not needed here. The classifier's window starts at the merge and
      the PR's own commits are excluded by SHA, both of which the replication package
      supplies — so this gate runs with no GitHub token, which is the point of doing it
      before the pilot.
IMPORTS: phase0.extract_prs, phase0.handlabel, phase0.pipeline.worktree, phase0.scan_outcome.
CONSUMED BY: `just handlabel-score`.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

from phase0.extract_prs import PRRecord
from phase0.handlabel.score import read_labels, score
from phase0.handlabel.select import Candidate, Selection, select_prs
from phase0.pipeline.worktree import CloneFailed, cloned
from phase0.scan_outcome import Outcome, scan

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data" / "AIDev_BC_Analyser.zip"
RESULTS = ROOT / "results"
WORKSPACE = ROOT / "data" / "handlabel_clones"


def _as_record(candidate: Candidate) -> PRRecord:
    """The classifier's input. `parent_sha` is unused by the outcome scan."""
    return PRRecord(
        pr_id=str(candidate.pr_id),
        repo=candidate.repo,
        language="python",
        parent_sha="",
        merged_sha=candidate.commit_shas[-1] if candidate.commit_shas else "",
        merged_at=candidate.merged_at,
        changed_files=candidate.changed_files,
        changed_symbols=(),
        arm="human",
    )


def _classify(selection: Selection) -> dict[int, Outcome]:
    by_repo: dict[str, list[tuple[int, Candidate]]] = defaultdict(list)
    for index, candidate in enumerate(selection.candidates, start=1):
        by_repo[candidate.repo].append((index, candidate))

    verdicts: dict[int, Outcome] = {}
    for repo, entries in sorted(by_repo.items()):
        print(f"scanning {repo} …", flush=True)
        try:
            with cloned(repo, WORKSPACE) as path:
                for index, candidate in entries:
                    record = scan(path, _as_record(candidate))
                    verdicts[index] = record.outcome
                    print(
                        f"    #{candidate.number}: {record.outcome.value}"
                        f"  ({record.criterion.value})",
                        flush=True,
                    )
        except CloneFailed as exc:
            # A repository we cannot read is not evidence of cleanliness. Fail the run
            # rather than score an unreadable PR as CLEAN and quietly inflate agreement.
            print(f"    CLONE FAILED: {exc}", flush=True)
            raise SystemExit(
                f"cannot score: {repo} is unreadable, and scoring it as clean would "
                f"manufacture agreement. Re-run when the clone succeeds."
            ) from exc
    return verdicts


def main() -> int:
    selection = select_prs(PACKAGE)
    answers = RESULTS / "handlabel_answers.txt"

    human = read_labels(answers, expected=len(selection.candidates))
    print(f"read {len(human)} human labels from {answers}\n", flush=True)

    result = score(selection, human, _classify(selection))
    print("\n" + result.describe())

    report = RESULTS / "handlabel_agreement.txt"
    report.write_text(result.describe() + "\n", encoding="utf-8")
    print(f"\nwritten to {report}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
