"""Correct the clone-failure stage on journal rows, from the run log's actual git error.

WHAT: Reads a pilot run log, classifies every `clone failed:` into one of four causes, and
      emits a SIDECAR correction map (`repo -> corrected stage`) plus the rows it applies
      to. Does not rewrite the journal.
WHY:  `pilot/covariates.py` `clone_failure_stage` decides with one substring test --
      `"repo_gone" if "not found" in str(exc).lower() else "clone_timeout"` -- and
      `git-lfs: command not found` contains "not found". A missing binary on THIS MACHINE
      is therefore recorded as a missing repository, and it lands in the bucket whose own
      docstring says it "selects on nothing and has no size to measure". git-lfs tracks
      large binary assets, so a size-selective failure sits in the category defined as
      size-free. A48.

      Four causes, not two, and they bound the estimand differently:
        `git_lfs_absent`     ours to fix; not attrition at all
        `clone_timeout`      our bound against their size -- A17's confounder
        `transport_failure`  network; retryable, and currently pooled into clone_timeout
        `repo_gone`          corpus staleness against a 1 Aug 2025 snapshot

      A SIDECAR rather than an in-place rewrite, deliberately. The journal is the resume
      checkpoint and `pipeline/resume.py` parses it by column INDEX, so editing it while a
      walk can still append is how two schemas end up in one file. Regenerate this after
      the walk lands and apply it then.
IMPORTS: stdlib argparse/collections/json/pathlib/re. Nothing from phase0 -- it reads
      text, so it cannot be broken by the classifier it exists to correct.
CONSUMED BY: run by hand; `results/clone_failure_corrections.json`.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

FAILED = re.compile(r"clone failed: ([^:]+/[^:]+): (.*)")
PROGRESS = re.compile(r"^\[(\d+)/(\d+)\]")

# Order matters: `git-lfs: command not found` also matches the "not found" test, which is
# the defect. The harness cause is tested FIRST so it can never be shadowed again.
CAUSES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("git_lfs_absent", ("git-lfs",)),
    ("clone_timeout", ("clone exceeded",)),
    ("transport_failure", ("rpc failed", "early eof", "unexpected disconnect")),
    ("repo_gone", ("not found", "could not read", "access denied")),
)


def classify(message: str) -> str:
    low = message.lower()
    for cause, needles in CAUSES:
        if any(needle in low for needle in needles):
            return cause
    return "unclassified"


def failures(log: Path) -> list[dict[str, str]]:
    """Every clone failure with its cause and the git text that decided it."""
    lines = log.read_text(errors="replace").splitlines()
    found: list[dict[str, str]] = []
    for index, line in enumerate(lines):
        match = FAILED.search(line)
        if not match:
            continue
        repo, head = match.group(1), match.group(2)
        # git writes the useful part across several lines; take the block, stopping at the
        # next progress marker so one failure cannot absorb the next repository's output.
        tail: list[str] = []
        for following in lines[index + 1 : index + 6]:
            if PROGRESS.match(following) or "clone failed:" in following:
                break
            tail.append(following)
        message = " ".join([head, *tail]).strip()
        cause = classify(message)
        found.append(
            {
                "repo": repo,
                "cause": cause,
                # What the CURRENT code writes, so the correction is auditable rather than
                # asserted: a row whose recorded stage already equals the cause needs no
                # change, and saying which is which is the whole point of the sidecar.
                "recorded_as": "repo_gone" if "not found" in message.lower() else "clone_timeout",
                "git_said": message[:300],
            }
        )
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--journal",
        type=Path,
        default=None,
        help="optional: count the journal rows each correction applies to",
    )
    args = parser.parse_args()

    rows = failures(args.log)
    wrong = [r for r in rows if r["cause"] != r["recorded_as"]]
    by_cause = collections.Counter(r["cause"] for r in rows)

    affected: dict[str, int] = {}
    if args.journal and args.journal.exists():
        text = args.journal.read_text(errors="replace")
        for row in rows:
            affected[row["repo"]] = sum(
                1 for line in text.splitlines() if line.startswith(f"| {row['repo']} ")
            )

    args.out.write_text(
        json.dumps(
            {
                "clone_failures": len(rows),
                "misclassified": len(wrong),
                "by_cause": dict(by_cause),
                "journal_rows_affected": affected,
                "corrections": rows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"{len(rows)} clone failure(s); {len(wrong)} carry the WRONG stage")
    for cause, n in by_cause.most_common():
        print(f"  {cause:20s} {n}")
    for row in wrong:
        rows_hit = affected.get(row["repo"], -1)
        seen = f"{rows_hit} journal row(s)" if rows_hit >= 0 else "journal not read"
        print(f"  WRONG  {row['repo']:44s} {row['recorded_as']} -> {row['cause']}  ({seen})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
