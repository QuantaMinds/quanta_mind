"""Compare the committed human labels against the sealed key. Run this last.

WHAT: `python -m phase0.score_labelling --human <csv> --key <csv> --out <json>`.
      Prints agreement, kappa, the 2x2 and every disagreement; writes the same as JSON.
WHY:  Kept separate from drawing so the two are commands a person runs in order. The
      label file must be complete before this will run, which means committing to twenty
      answers rather than peeking after ten.

      The JSON records the label file's git SHA when one is available. That is what makes
      the ordering checkable by somebody who was not there -- including the author in
      three months, when the result is inconvenient.
IMPORTS: phase0.handlabel.{files,labels,score}.
CONSUMED BY: `just label-score`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from phase0.handlabel.files import read_key
from phase0.handlabel.labels import read_labels
from phase0.handlabel.score import score

ROOT = Path(__file__).resolve().parents[2]
GIT_TIMEOUT_S = 30


def _committed_sha(path: Path) -> str:
    """The commit that last touched the label file, or a marker saying there isn't one."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    sha = result.stdout.strip()
    # Uncommitted labels are a real weakness in the audit trail, not a formatting detail.
    return sha or "UNCOMMITTED -- the ordering claim is unverifiable"


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score human labels against the sealed key.")
    base = ROOT / "data" / "labelling"
    parser.add_argument("--human", type=Path, default=base / "human_labels.csv")
    parser.add_argument("--key", type=Path, default=base / "_key.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "labelling.json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv if argv is not None else sys.argv[1:])
    key = read_key(args.key)
    human = read_labels(args.human, expected=len(key))
    result = score(key, human)

    print(result.describe())

    payload = {
        "agreement": result.agreed,
        "total": result.total,
        "rate": result.rate,
        "passed": result.passed,
        "kappa": result.kappa,
        "unsure": result.unsure,
        "minutes_median": result.minutes_median,
        "confusion": {
            "both_broke": result.both_broke,
            "both_clean": result.both_clean,
            "machine_broke_human_clean": result.machine_broke_human_clean,
            "machine_clean_human_broke": result.machine_clean_human_broke,
        },
        "disagreements": [asdict(d) | {"direction": d.direction} for d in result.disagreements],
        "human_labels_commit": _committed_sha(args.human),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nwritten to {args.out}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
