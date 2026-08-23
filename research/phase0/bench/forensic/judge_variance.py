"""Judge the SAME candidates several times and report how far the verdict moves on its own.

WHAT: Re-runs `judge.verdicts()` over one arm's stored candidates N times, and prints the precision
      of each replicate plus the spread. Nothing about the candidates changes between replicates.
WHY:  **A RE-JUDGE OF THE SAME 318 CODERABBIT CANDIDATES MOVED ITS TRUE POSITIVES BY +32, WHICH IS
      A TEN-POINT SWING IN PRECISION FROM CHANGING NOTHING.** Every arm comparison this project has
      published rests on one judging run, and a difference smaller than the instrument's own spread
      is not a difference. This measures the spread so a later comparison can be required to clear
      it -- the bar `judge_arms.py` has no way to set otherwise.

      **THIS IS THE KNOWN-ANSWER TEST FOR THE INSTRUMENT.** The candidates are identical, so the
      correct answer is "no change". Whatever it prints instead is the noise floor, and any prompt
      arm that moves precision by less than that floor has demonstrated nothing.
IMPORTS: stdlib; local `judge` and the Vertex `client`.
CONSUMED BY: read by a human; the floor it prints is the bar quoted in prompt-arm preregistrations.
"""

from __future__ import annotations

import json
import pathlib
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "vertex"))
sys.path.insert(0, str(HERE.parent))

import judge  # noqa: E402
import martian_corpus as mc  # noqa: E402
from client import Client  # noqa: E402

REPLICATES = 3


def main() -> int:
    arm = sys.argv[1] if len(sys.argv) > 1 else "OURS"
    client = Client("gemini-2.5-pro")
    ours = json.loads((HERE.parent / "results" / "martian_comparison.json").read_text())[
        "ours_candidates"
    ]
    cands = ours if arm == "OURS" else mc.rival_candidates(arm)
    golden = {str(p["key"]): list(p["golden"]) for p in mc.pulls()}

    rates: list[float] = []
    for i in range(REPLICATES):
        tp = n = 0
        for key, texts in cands.items():
            g = golden.get(key) or []
            if not g or not texts:
                continue
            v = judge.verdicts(client, g, texts)
            tp += len(texts) - len(set(v["fp"]))
            n += len(texts)
        rates.append(tp / n)
        print(f"  replicate {i + 1}: {tp}/{n} = {tp / n:.1%}", flush=True)

    lo, hi = min(rates), max(rates)
    print(f"\n  {arm}: {lo:.1%} .. {hi:.1%}  spread {hi - lo:.1%} on IDENTICAL candidates")
    if len(rates) > 1:
        print(f"  sd {statistics.stdev(rates):.1%}")
    print(
        f"\n  => a prompt arm must move precision by MORE than {hi - lo:.1%} to have shown "
        f"anything. Anything smaller is this."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
