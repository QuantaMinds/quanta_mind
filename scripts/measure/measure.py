"""Findings published per change, over every denominator a reader might mean.

WHAT: `python research/phase0/bench/rate/measure.py --clone C --repo R --limit N --skip M`
      runs the full pipeline over N commits and prints the rate three ways.
WHY:  A rate is a fraction and the argument is always about its bottom half. A change can
      fail to reach the model three ways -- no timestamp, no funded files, or a funded set
      whose diff is empty -- and each is a different statement about the pipeline. Reporting
      only "0.686 per change" leaves a reader to guess which of the three were counted.

      **EVERY EXCLUSION IS A COUNTED CATEGORY, NEVER A `continue`.** The instrument reports on
      itself: a run where most changes never reached the model looks identical, in a single
      rate, to one where the model was asked every time and said little.
IMPORTS: stdlib, quantamind.{serve,infer}.
CONSUMED BY: an operator, by hand; results are quoted in docs/findings/.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from quantamind.infer.vertex import InferenceFailed, Unavailable
from quantamind.serve.commands.run_commit import _timestamp
from quantamind.serve.commands.run_review import review
from quantamind.serve.review.deep_review import deep

sys.path.insert(0, str(Path(__file__).parent))
from record import ChangeRecord, report

GIT_TIMEOUT_S = 120


def commits(clone: Path, limit: int, skip: int) -> list[str]:
    out = subprocess.run(
        [
            "git",
            "-C",
            str(clone),
            "log",
            "--no-merges",
            f"--skip={skip}",
            "-n",
            str(limit),
            "--format=%H",
            "--",
            "*.py",
        ],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_S,
        check=True,
    )
    return out.stdout.split()


def one(clone: Path, repo: str, sha: str, *, project: str, gcloud: str) -> ChangeRecord:
    """Run one change all the way through, naming where it stopped if it stopped."""
    stamp = _timestamp(clone, sha)
    if stamp is None:
        return ChangeRecord(sha, "no-timestamp")
    changed, as_of = stamp
    with TemporaryDirectory() as scratch:
        out = review(clone, repo, changed, Path(scratch) / "r.db", as_of=as_of)
    ranked = [u.unit.site.path for u in out.ranking.funded()]
    if not ranked:
        return ChangeRecord(sha, "no-funded-files")
    try:
        got = deep(clone, sha, ranked, project=project, changed=list(out.considered), gcloud=gcloud)
    except (InferenceFailed, Unavailable):
        return ChangeRecord(sha, "model-failed")
    if not got.consulted:
        # The funded paths carried no diff, so the model was never asked. This is NOT a change
        # on which the model found nothing, and collapsing the two would understate the rate.
        return ChangeRecord(sha, "empty-diff")
    return ChangeRecord(
        sha,
        "measured",
        got.raw,
        len(got.anchored),
        got.unanchored,
        got.refuted,
        got.unresolvable,
        got.withdrawn,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clone", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--skip", type=int, default=0)
    parser.add_argument("--project", default="quantamind-oss")
    parser.add_argument("--gcloud", default="gcloud")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    records: list[ChangeRecord] = []
    for sha in commits(args.clone, args.limit, args.skip):
        records.append(one(args.clone, args.repo, sha, project=args.project, gcloud=args.gcloud))
        args.out.write_text(json.dumps([asdict(r) for r in records], indent=1))
        print(f"  {records[-1].outcome:<16} {sha[:10]}  kept={records[-1].kept}", flush=True)
    print()
    print(report(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
