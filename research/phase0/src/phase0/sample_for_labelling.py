"""Draw the stratified labelling sample. Run this first; it seals the answers away.

WHAT: `python -m phase0.sample_for_labelling --n-broke 10 --n-clean 10 --seed <int>`.
      Writes a two-column blind sheet, a blank label template, and a sealed key.
WHY:  The seed is required and has no default, so a draw is reproducible and cannot be
      quietly redrawn because somebody disliked the first one. Re-running with the same
      seed and package reproduces the same twenty.

      Progress prints the repository and the running bucket totals -- how many, never
      which. Printing a per-PR verdict here would contaminate the labeller through the
      terminal, which is the one channel the file-level split does not cover.

      `--arm` is REQUIRED, for the reason the pilot's is. The gate validates the outcome
      classifier for the population it will be APPLIED to, and the study runs on agent
      PRs. Agent fix-commits may differ from human ones in message style and timing, and
      A26's rules were tuned on human commits -- so a gate passed on the human arm would
      certify the classifier against the wrong corpus. This module drew from the human
      package because that was the only population that existed; the agent arm exists
      now, so the choice becomes explicit rather than inherited.
IMPORTS: phase0.arm, phase0.handlabel.{draw,files}, phase0.pilot.options, phase0.population.
CONSUMED BY: `just label-draw`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from phase0 import arm
from phase0.handlabel.draw import draw
from phase0.handlabel.files import write_blind, write_key, write_label_template
from phase0.handlabel.select import Candidate
from phase0.pipeline import records_file
from phase0.population import for_arm

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "data" / "AIDev_BC_Analyser.zip"
AIDEV = ROOT / "data" / "aidev"
WORKSPACE = ROOT / "data" / "labelling_clones"


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draw a blind, stratified labelling sample.")
    parser.add_argument(
        "--arm",
        choices=("agent", "human"),
        required=True,
        help="which population to draw from. REQUIRED and without a default: the gate "
        "certifies the classifier for the arm it draws from, and the study runs on "
        "`agent`. A human-arm gate would validate against the wrong corpus",
    )
    parser.add_argument("--n-broke", type=int, default=10)
    parser.add_argument("--n-clean", type=int, default=10)
    parser.add_argument(
        "--seed", type=int, required=True, help="fixed, so the draw is reproducible"
    )
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "labelling" / "sample.csv")
    parser.add_argument(
        "--records",
        type=Path,
        required=True,
        help="the pilot's own PRRecords for this arm. REQUIRED and without a default: the "
        "gate certifies the classifier on the records the study analyses, and rebuilding "
        "that input here is what made it certify a different classifier",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv if argv is not None else sys.argv[1:])
    if not PACKAGE.is_file():
        print(f"{PACKAGE} not found -- see ENVIRONMENT.lock for the figshare URL.")
        return 1

    population, claimed = for_arm(args.arm, AIDEV, PACKAGE)
    # Same check the pilot makes, for the same reason: the arm a draw claims must be the
    # arm AIDev's own `agent` column puts its ids in.
    tally = arm.verify([c.pr_id for c in population], claimed, AIDEV)
    print(f"arm verified: {tally}", flush=True)
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

    # The pipeline's own records, not a reconstruction of them. `_as_record` used to
    # rebuild the scan's input here and got `base_ref`, `arm` and `merged_sha` wrong, so
    # the gate certified a classifier the study does not run. A candidate absent from this
    # map was never admitted, and the gate must not certify the classifier on a PR the
    # study never analyses.
    records = {r.pr_id: r for r in records_file.read(args.records)}
    if not records:
        print(f"{args.records} holds no records -- run the pilot for this arm first.")
        return 1
    print(f"{len(records)} admitted records to draw from", flush=True)

    drawn = draw(
        population,
        WORKSPACE,
        records,
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
    # Printed, not merely collected. The draw skips PRs whose outcome it could not scan,
    # and a count that is computed and then discarded is the same silence as never
    # counting -- which is the defect that put UNSCANNABLE in the enum to begin with.
    if drawn.unscannable:
        breakdown = ", ".join(
            f"{reason.value}={count}"
            for reason, count in sorted(drawn.unscannable.items(), key=lambda kv: kv[0].value)
        )
        print(f"skipped      {drawn.skipped_total()} unscannable ({breakdown})")
    print(f"blind sheet  {args.out}")
    print(f"label here   {labels_path}")
    print(f"sealed key   {key_path}   <- DO NOT OPEN until the labels are committed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
