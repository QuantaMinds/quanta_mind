"""Arm A: the mechanical gate alone, no model, reported on the trade rather than on precision.

WHAT: Applies `decidable.keyword_flag()` to every candidate in the nits arm, then re-scores the
      survivors against the same golden comments. Prints false positives removed (D), true findings
      lost (L), and D/L against the pool's chance value.
WHY:  Bars are fixed in
      docs/plans/preregistrations/reviewer/filter-gate-preregistration.md before this ran.

      **A IS RUN AND REPORTED ALONE, BEFORE ANY MODEL JUDGE.** If the rule does the work, a model
      judge on top is inference cost defended by a number the rule earned. This project has twice
      credited a mechanism whose work belonged to another -- hunk expansion, and the location
      signal that turned out to be the ranker's.

      **THE BAR IS D/L, NOT PRECISION.** Precision rises whatever you delete, including at random,
      so it is arithmetic rather than evidence. **The chance value of D/L is the pool's odds:
      364/100 = 3.64.** A gate scoring 3.64 has done nothing however good its precision looks.
      B1 asks for 15 -- four times chance.

      **AND A FILTER HERE CAN BE INVERTED, NOT MERELY NULL.** Four have failed in this project:
      anchor snapping (p = 0.53), the rejection filter (+9.9 against a +15 bar), the >40-line gate
      (p = 0.281, discarding 2 of 12 correct findings), and the execution gate, which came back
      **significantly backwards at p = 0.003**. D/L below 3.64 is that outcome and is reported as
      such.
IMPORTS: stdlib (json, pathlib, sys). Local: `corpus`, `judge`, `decidable`, the Vertex `client`.
CONSUMED BY: nobody -- it prints and writes results/gate_arm.json.
"""

from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
# **ORDER MATTERS AND IT BIT ONCE ALREADY.** `bench/` and `quote/` BOTH contain a `corpus.py`.
# Each `insert(0, ...)` goes to the front, so the LAST insert wins the name -- listing bench first
# silently resolved `corpus` to `quote/corpus.py`, whose API is different and which has no
# `_assert_intact`. bench is inserted last so it wins, and the bench corpus is what this arm scores
# against.
sys.path.insert(0, str(HERE.parent / "vertex"))
sys.path.insert(0, str(HERE.parent / "quote"))
sys.path.insert(0, str(HERE))

import decidable  # noqa: E402  — from quote/
import judge  # noqa: E402
import martian_corpus as corpus  # noqa: E402  — bench/corpus.py, NOT quote/corpus.py
from client import Client  # noqa: E402

assert hasattr(corpus, "_assert_intact"), "wrong corpus module resolved; check sys.path order"

SCORING_MODEL = "gemini-2.5-pro"
NITS = HERE / "results" / "nits_arm.json"
OUT = HERE / "results" / "gate_arm.json"
# Fixed in the pre-registration before this ran. Never edited to fit a number.
B1_TRADE, B2_VOLUME, B3_RECALL = 15.0, 180, 15
BASE_TP, BASE_FP = 100, 364


def main() -> int:
    corpus._assert_intact()
    blob = json.loads(NITS.read_text())
    cands: dict[str, list[str]] = blob["candidates"]
    golden = {pr["key"]: pr["golden"] for pr in blob["detail"]}
    before = sum(len(v) for v in cands.values())

    kept = {k: [c for c in v if not decidable.keyword_flag(c)] for k, v in cands.items()}
    after = sum(len(v) for v in kept.values())
    print("  ARM A — the mechanical gate alone. No model in the filter.")
    print(f"({1 - after / before:.0%} dropped), 0 model calls in the gate\n")

    print(f"  re-scoring survivors against the same golden comments ({SCORING_MODEL}) ...")
    client = Client(SCORING_MODEL)
    tp = fp = 0
    for key, issues in kept.items():
        g = golden.get(key) or []
        if not g:
            fp += len(issues)
            continue
        v = judge.verdicts(client, g, issues)
        tp += len(v["tp"])
        fp += len(v["fp"])

    lost = BASE_TP - tp
    removed = BASE_FP - fp
    trade = removed / lost if lost else float("inf")
    chance = BASE_FP / BASE_TP

    OUT.write_text(
        json.dumps(
            {
                "arm": "A — mechanical gate only",
                "gate": "decidable.keyword_flag",
                "before": before,
                "after": after,
                "tp": tp,
                "fp": fp,
                "removed_fp": removed,
                "lost_tp": lost,
                "trade": trade,
                "chance": chance,
            },
            indent=1,
        )
    )

    print(f"\n  TP {tp}/{BASE_TP}   FP {fp}/{BASE_FP}")
    print(f"\n  {'bar':<34}{'value':>12}{'required':>12}{'verdict':>12}")
    rows = [
        ("B1  trade  D/L", f"{trade:.1f}", f">= {B1_TRADE:.0f}", trade >= B1_TRADE),
        ("B2  volume D (false removed)", f"{removed}", f">= {B2_VOLUME}", removed >= B2_VOLUME),
        ("B3  recall L (true lost)", f"{lost}", f"<= {B3_RECALL}", lost <= B3_RECALL),
    ]
    for name, got, need, ok in rows:
        print(f"  {name:<34}{got:>12}{need:>12}{'PASS' if ok else 'FAIL':>12}")
    print(f"\n  chance value of D/L on this pool: {chance:.2f} (the pool's odds, 364/100)")
    if trade < chance:
        print("  *** D/L IS BELOW CHANCE. The gate is discarding true findings faster than false")
        print("      ones -- the INVERTED outcome, not the null one. ***")
    elif trade < B1_TRADE:
        print(f"  D/L beats chance by {trade / chance:.2f}x but misses B1. Not a pass.")
    print(f"\n  precision {tp / max(tp + fp, 1):.1%} — printed LAST and never alone, because it")
    print("  rises whatever you delete.")
    return 0 if all(ok for *_, ok in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
