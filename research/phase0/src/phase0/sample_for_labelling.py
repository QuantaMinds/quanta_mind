"""Draw the stratified labelling sample. Run this first; it seals the answers away.

WHAT: `python -m phase0.sample_for_labelling --n-broke 10 --n-clean 10 --seed <int>`.
      Writes a two-column blind sheet, a blank label template, and a sealed key.
WHY:  The seed is required and has no default, so a draw is reproducible and cannot be
      quietly redrawn because somebody disliked the first one. Re-running with the same
      seed and package reproduces the same twenty.

      Progress prints the repository and the running bucket totals -- how many, never
      which. Printing a per-PR verdict here would contaminate the labeller through the
      terminal, which is the one channel the file-level split does not cover.
IMPORTS: phase0.handlabel.{select,draw,files}.
CONSUMED BY: `just label-draw`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from phase0.handlabel.draw import draw
from phase0.handlabel.files import write_blind, write_key, write_label_template
from phase0.handlabel.select import Candidate, eligible_prs

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "data" / "AIDev_BC_Analyser.zip"
WORKSPACE = ROOT / "data" / "labelling_clones"


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draw a blind, stratified labelling sample.")
    parser.add_argument("--n-broke", type=int, default=10)
    parser.add_argument("--n-clean", type=int, default=10)
    parser.add_argument(
        "--seed", type=int, required=True, help="fixed, so the draw is reproducible"
    )
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "labelling" / "sample.csv")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv if argv is not None else sys.argv[1:])
    if not PACKAGE.is_file():
        print(f"{PACKAGE} not found -- see ENVIRONMENT.lock for the figshare URL.")
        return 1

    population = eligible_prs(PACKAGE)
    print(f"{len(population)} eligible PRs; drawing {args.n_broke} + {args.n_clean}", flush=True)

    seen: set[str] = set()

    def progress(repo: str, _candidate: Candidate, n_broke: int, n_clean: int) -> None:
        if repo not in seen:
            seen.add(repo)
            print(f"  [{len(seen):>2}] {repo}", flush=True)
        print(
            f"       buckets: broke {n_broke}/{args.n_broke}  clean {n_clean}/{args.n_clean}",
            flush=True,
        )

    drawn = draw(
        population,
        WORKSPACE,
        n_broke=args.n_broke,
        n_clean=args.n_clean,
        seed=args.seed,
        on_progress=progress,
    )

    key_path = args.out.parent / "_key.csv"
    labels_path = args.out.parent / "human_labels.csv"
    write_blind(args.out, drawn.blind)
    write_key(key_path, drawn.key)
    write_label_template(labels_path, [label_id for label_id, _ in drawn.blind])

    print(
        f"\nseed {drawn.seed}   examined {drawn.considered} PRs across "
        f"{drawn.repos_visited} repositories   buckets {drawn.bucket_sizes()}"
    )
    print(f"blind sheet  {args.out}")
    print(f"label here   {labels_path}")
    print(f"sealed key   {key_path}   <- DO NOT OPEN until the labels are committed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
