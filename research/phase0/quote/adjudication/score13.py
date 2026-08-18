"""Score design thirteen against the bars fixed before the run, and say pass or fail.

WHAT: Joins the rater's verdicts to the held-back key, prints the sabotage catch-rate first, then
      per-arm wrong-rates with Wilson intervals, then each pre-registered hypothesis with its bar.
WHY:  The bars are in docs/plans/preregistrations/expansion-conventions-preregistration.md and are
      read from there by a human, not restated loosely here. A near-miss is a fail.

      THE SABOTAGE RATE IS PRINTED BEFORE ANY RESULT AND GATES IT. If the pool graded planted-wrong
      findings CORRECT, its verdicts describe the pool, not the arms, and nothing below them means
      anything. Printing it first is deliberate -- a number read after a result is a number the
      reader has already discounted.

      THE INTERVAL RULE: a point estimate under a bar passes only if the Wilson upper bound clears
      it too. This project has passed a bar on a point estimate whose interval spanned the bar
      twice, and both had to be withdrawn.
IMPORTS: stdlib only (collections, json, math, pathlib, sys).
CONSUMED BY: nobody -- it prints.
"""

from __future__ import annotations

import collections
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

HERE = pathlib.Path(__file__).resolve().parent.parent
ADJ = HERE / "adj13"
WRONGISH = {"WRONG"}
COUNTED = {"CORRECT", "WRONG", "UNFALSIFIABLE", "TRIVIAL"}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """(point, low, high). Returns (0,0,1) at n=0 rather than dividing by zero."""
    if n == 0:
        return 0.0, 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


CAUSES = {"EXTERNAL", "ABSENT", "TRACE", "OTHER"}


def verdict_of(line: str) -> tuple[str, str]:
    """(bucket, cause) from one verdict string of the form 'BUCKET sentence ... CAUSE'.

    An unrecognised bucket returns ('', '') and is counted as unparseable, never as a pass. The
    cause defaults to OTHER so a rater who omits it cannot inflate the class H1 is measuring.
    """
    parts = str(line).strip().split()
    if not parts:
        return "", ""
    bucket = parts[0].upper().strip(".,:")
    cause = parts[-1].upper().strip(".,:")
    return (bucket if bucket in COUNTED else ""), (cause if cause in CAUSES else "OTHER")


def main() -> int:
    key = {int(k["item"]): k for k in json.loads((ADJ / "KEY_DO_NOT_OPEN.json").read_text())}
    raw = json.loads((ADJ / "verdicts.json").read_text())
    verdicts = {int(k): v for k, v in raw.items()}

    # --- the gate on the whole adjudication, printed first ---
    sab = [(i, verdicts.get(i)) for i, k in key.items() if k["kind"] == "SABOTAGE"]
    graded = [(i, v) for i, v in sab if v]
    caught = [(i, v) for i, v in graded if verdict_of(v)[0] == "WRONG"]
    print(f"  SABOTAGE CONTROLS: {len(caught)}/{len(graded)} caught as WRONG")
    if len(graded) and len(caught) / len(graded) < 0.8:
        print("  RATINGS DISCARDED — the pool rubber-stamped planted-wrong findings.")
        return 1
    print("  the pool caught the plants; its verdicts are readable\n")

    arms: dict[str, collections.Counter[str]] = {a: collections.Counter() for a in "ABC"}
    causes: dict[str, collections.Counter[str]] = {a: collections.Counter() for a in "ABC"}
    unparsed = 0
    for i, k in key.items():
        if k["kind"] != "real":
            continue
        line = verdicts.get(i)
        if not line:
            arms[str(k["arm"])]["UNRATED"] += 1
            continue
        bucket, cause = verdict_of(line)
        if not bucket:
            unparsed += 1
            continue
        arms[str(k["arm"])][bucket] += 1
        if bucket in WRONGISH:
            causes[str(k["arm"])][cause] += 1

    print(f"  {'arm':>4} {'n':>4} {'wrong':>6} {'rate':>7} {'95% Wilson':>16}   buckets")
    rates: dict[str, tuple[float, float, float]] = {}
    for a in "ABC":
        c = arms[a]
        n = sum(c[b] for b in COUNTED)
        w = c["WRONG"]
        p, lo, hi = wilson(w, n)
        rates[a] = (p, lo, hi)
        print(f"  {a:>4} {n:>4} {w:>6} {p:>6.1%}   [{lo:>5.1%}, {hi:>5.1%}]   {dict(c)}")

    print("\n  wrong-cause mix (H1 targets TRACE + ABSENT — what expansion can supply):")
    for a in "ABC":
        tot = sum(causes[a].values()) or 1
        ta = (causes[a]["TRACE"] + causes[a]["ABSENT"]) / tot
        print(f"    {a}: TRACE+ABSENT {ta:>6.1%} of {tot} wrong   {dict(causes[a])}")

    ta = {
        a: (causes[a]["TRACE"] + causes[a]["ABSENT"]) / (sum(causes[a].values()) or 1)
        for a in "ABC"
    }
    print("\n  === pre-registered bars ===")
    d1 = ta["A"] - ta["B"]
    print(
        f"  H1 TRACE+ABSENT share falls A->B by >= 15 pts : {d1:+.1%}   "
        f"[{'PASS' if d1 >= 0.15 else 'FAIL'}]"
    )
    pb, _lb, hb = rates["B"]
    print(
        f"  H2 arm B wrong-rate <= 30% (interval rule)    : {pb:.1%} upper {hb:.1%}   "
        f"[{'PASS' if pb <= 0.30 and hb <= 0.30 else 'FAIL'}]"
    )
    dc = rates["C"][0] - rates["B"][0]
    print(
        f"  H3 arm C wrong-rate not >10 pts above B       : {dc:+.1%}   "
        f"[{'PASS' if dc <= 0.10 else 'FAIL — conventions not shipped'}]"
    )
    if unparsed:
        print(f"\n  {unparsed} rater line(s) unparseable — counted nowhere, never as a pass")
    print("\n  H4 yield is printed by run13.py. Power was fixed in advance: this corpus")
    print("  detects a large effect and nothing smaller, so a null on H2 is not a negative.")
    return 0


sys.exit(main())
