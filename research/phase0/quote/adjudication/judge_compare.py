"""Grade DESIGN THIRTEEN's pool with design fourteen's judge, and compare to its stored verdicts.

WHAT: Runs `judge14.grade_all()` over `adj13/chunk_*.md`, joins to design thirteen's sealed key,
      and prints W/n and C/n beside the numbers design thirteen actually reported.
WHY:  **DESIGN FOURTEEN SCORED W/n 24.5% AND C/n 62.7% AGAINST DESIGN THIRTEEN'S 52.3% AND 8.1%,
      AND THE PRE-REGISTRATION SAID C/n WOULD NOT CLEAR.** A result that far past its own written
      prior is more likely an instrument change than an effect. The two runs were graded by
      DIFFERENT raters, and design fourteen's judge assigned TRIVIAL to zero of 102 findings where
      design thirteen's rater used it on 18.8% -- which alone could move C/n by nineteen points.

      **So the judge is held fixed and the design is varied, which is the comparison that was never
      made.** If this judge grades design thirteen near 52% wrong, the two raters agree and design
      fourteen's improvement is real. If it grades design thirteen near 25% wrong, the improvement
      is the rater and design fourteen measured nothing.

      There is no third reading, and the answer is not known while this is being written.
IMPORTS: stdlib (json, math, pathlib, sys). Local: `judge14`, the Vertex `client`.
CONSUMED BY: nobody -- it prints.
"""

from __future__ import annotations

import collections
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "vertex"))

from client import Client  # noqa: E402
from judge14 import RUBRIC, grade_all, items_of  # noqa: E402

ADJ13 = HERE.parent / "adj13"
OUT = ADJ13 / "verdicts_judge14.json"
# What design thirteen reported, recomputed from its own artefacts. Printed for comparison only.
D13_W, D13_C, D13_N = 0.523, 0.081, 86


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def main() -> int:
    key = {str(e["item"]): e for e in json.loads((ADJ13 / "KEY_DO_NOT_OPEN.json").read_text())}
    client = Client("gemini-2.5-pro")
    rubric = RUBRIC.read_text()

    verdicts: dict[str, str] = {}
    for path in sorted(ADJ13.glob("chunk_*.md")):
        print(f"  grading {path.name} ...", flush=True)
        head, items = items_of(path.read_text())
        verdicts |= grade_all(client, rubric, head, items)
    OUT.write_text(json.dumps(verdicts, indent=1))
    print(f"  {len(verdicts)}/{len(key)} graded -> {OUT}\n")

    real = [(key[i], verdicts[i]) for i in verdicts if key.get(i, {}).get("kind") == "real"]
    sab = [(key[i], verdicts[i]) for i in verdicts if key.get(i, {}).get("kind") == "SABOTAGE"]
    caught = sum(1 for _, t in sab if t.split()[0].upper() == "WRONG")
    print(f"  sabotage caught by this judge: {caught}/{len(sab)}")

    n = len(real)
    counts = collections.Counter(t.split()[0].upper() for _, t in real)
    W, C = counts["WRONG"], counts["CORRECT"]
    wlo, whi = wilson(W, n)
    clo, chi = wilson(C, n)

    print(f"\n  DESIGN 13's POOL, GRADED BY DESIGN 14's JUDGE   n = {n}")
    for b in ("CORRECT", "WRONG", "UNFALSIFIABLE", "TRIVIAL"):
        print(f"    {b:<14}{counts[b]:>4}{counts[b] / n:>8.1%}")
    print(
        f"\n    W/n = {W / n:.1%}  (Wilson {wlo:.1%} to {whi:.1%})   design 13 reported {D13_W:.1%}"
    )
    print(
        f"    C/n = {C / n:.1%}  (Wilson {clo:.1%} to {chi:.1%})   design 13 reported {D13_C:.1%}"
    )

    print("\n  READING:")
    if wlo <= D13_W <= whi:
        print("    The two raters AGREE on design 13 within the interval. Design 14's judge is")
        print("    comparable, so design 14's improvement is attributable to the DESIGN.")
    else:
        print("    The two raters DISAGREE on the same findings. Design 14's numbers are not")
        print("    comparable to design 13's, and its apparent improvement is RATER DRIFT until")
        print("    design 13 is re-graded by this judge and both are read off the same instrument.")
    return 0


raise SystemExit(main())
