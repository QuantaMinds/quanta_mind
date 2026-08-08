"""The pilot's command line, and the paths it defaults to.

WHAT: `parse` — the argument surface of `python -m phase0.pilot.run`, plus the project
      paths every default is anchored to.
WHY:  Split from `run.py`, which orchestrates the walk. How the run is INVOKED and what
      the run DOES are separate concerns, and the split keeps the defaults in one place
      where they can be read against each other.

      `ROOT` is why this matters more than tidiness. It was `parents[2]`, which resolved
      to `src/` rather than the project root, so every default below named a directory
      that does not exist and the pilot could not find its own corpus. It broke silently
      when `pilot.py` became the `pilot/` package, and nothing re-ran it until now.
      Counted once, here, rather than recomputed beside each path.
IMPORTS: stdlib argparse, pathlib.
CONSUMED BY: pilot/run.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

# options -> pilot -> phase0 -> src -> project root. `controls/gate.py` counts from the
# same depth; if either moves, both move.
ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "data" / "AIDev_BC_Analyser.zip"
WORKSPACE = ROOT / "data" / "pilot_clones"
CACHE = ROOT / "data" / "gh_cache"


def parse(argv: list[str] | None = None) -> argparse.Namespace:
    """The pilot's arguments. Defaults are anchored to ROOT, never to the cwd."""
    parser = argparse.ArgumentParser(description="Pilot: build records and report shape.")
    parser.add_argument(
        "--arm",
        choices=("agent", "human"),
        required=True,
        help="which population to walk. REQUIRED and deliberately without a default: "
        "the 90-repo pilot ran entirely on the human arm because a caller took the "
        "population function it found, and no default here can be the wrong one if "
        "there is no default. `agent` is the study's primary arm",
    )
    parser.add_argument("--repos", type=int, default=10)
    parser.add_argument(
        "--only-repo",
        action="append",
        default=None,
        metavar="OWNER/NAME",
        help="walk only these repositories, even if the journal marks them done. "
        "Repeatable. Requires --rescan-reason, because a repository appearing twice "
        "without a stated cause is indistinguishable from a duplicated bug",
    )
    parser.add_argument(
        "--rescan-reason",
        default="",
        metavar="TEXT",
        help="stamped on every row this run appends, e.g. 'rescan: blob_none_A29'",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="also scan the outcome window, for the power projection",
    )
    parser.add_argument("--per-repo", type=int, default=4)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=WORKSPACE,
        help="clone directory; a second concurrent run needs its own",
    )
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "pilot.json")
    parser.add_argument(
        "--records",
        type=Path,
        default=ROOT / "results" / "records.jsonl",
        help="persist admitted PRRecords here; the exposure pass reads them rather "
        "than rebuilding what this run already resolved",
    )
    parser.add_argument(
        "--trace-dir",
        type=Path,
        default=ROOT / "runs" / "pilot",
        help="timestamped run record: a timeline, a snapshot per repository, and the "
        "running shape. Separate from --journal, which exists to RESUME a run; this "
        "exists to explain one that died",
    )
    parser.add_argument(
        "--journal",
        type=Path,
        default=ROOT / "results" / "pilot_journal.md",
        help="append-only progress, flushed per repository; a restart resumes from it",
    )
    args = parser.parse_args(argv)
    if args.only_repo and not args.rescan_reason.strip():
        # Refused here rather than defaulted. A default reason would be written into the
        # journal as though someone had stated it, and the journal is the only record of
        # why a repository has two entries.
        parser.error("--only-repo requires --rescan-reason stating why they are re-walked")
    return args
