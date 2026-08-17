"""Join the hand verdicts to the key and report G2 and the discriminator.

WHAT: Separates real findings from sabotaged controls, reports the published wrong-rate against the
      50% bar, the UNFALSIFIABLE share against the 25% discriminator, and the rate at which the
      rater passed a sabotaged control.
WHY:  The rater knew the hypothesis and wanted it to pass, so the sabotage rate is what decides
      whether any of the rest can be believed. **A sabotaged control graded anything but WRONG is
      rubber-stamping** -- its claim was lifted from a different pull request and cannot describe
      the quoted code.
IMPORTS: stdlib only (collections, json, pathlib, sys).
CONSUMED BY: nobody -- it prints.
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys

ADJ = pathlib.Path(__file__).resolve().parent / "adj"
WRONG_BAR = 0.50
UNFALS_BAR = 0.25


def main() -> int:
    key = {r["item"]: r for r in json.loads((ADJ / "KEY_DO_NOT_OPEN.json").read_text())}
    verdicts = json.loads((ADJ / "verdicts.json").read_text())
    if len(verdicts) != len(key):
        print(f"  REFUSING TO REPORT — {len(verdicts)} verdicts against {len(key)} items")
        return 1

    real: collections.Counter[str] = collections.Counter()
    sab: collections.Counter[str] = collections.Counter()
    missed: list[int] = []
    for n_str, verdict in verdicts.items():
        n = int(n_str)
        if str(key[n]["kind"]) == "SABOTAGE":
            sab[verdict] += 1
            if verdict != "WRONG":
                missed.append(n)
        else:
            real[verdict] += 1

    ns = sum(sab.values())
    caught = sab["WRONG"]
    print("  CONTROL FIRST — sabotaged findings whose claim came from a different pull request\n")
    print(f"    {ns} controls, graded WRONG {caught}, missed {ns - caught}")
    print(f"    catch rate {caught / ns:.0%}" if ns else "    no controls")
    if missed:
        print(f"    NOT caught: items {sorted(missed)} -> {[verdicts[str(m)] for m in missed]}")
    if ns and caught / ns < 0.75:
        print("\n  VOID — the rater passed too many controls to be believed on the real findings.")
        return 1
    print("    the rater discriminates; the real verdicts below can be read\n")

    n = sum(real.values())
    print(f"  {n} PUBLISHED FINDINGS, hand-adjudicated out of the Gemini family\n")
    for k in ("CORRECT", "TRIVIAL", "UNFALSIFIABLE", "WRONG"):
        print(f"    {k:14s} {real[k]:3d}  {real[k] / n:6.1%}")

    wrong = real["WRONG"] / n
    unfals = real["UNFALSIFIABLE"] / n
    print(f"\n  G2  published wrong-rate {wrong:.1%}   bar < {WRONG_BAR:.0%}")
    print(f"      [{'PASS' if wrong < WRONG_BAR else 'FAIL'}]")
    print(f"\n  discriminator  UNFALSIFIABLE {unfals:.1%}   bar < {UNFALS_BAR:.0%}")
    print(f"      [{'PASS' if unfals < UNFALS_BAR else 'FAIL'}]")
    print("\n  for comparison, the seven designs that failed this bar:")
    print("      design 1  66.7% / 74.2% wrong      design 2  61.1%")
    print("      design 3  82.1%   design 4  66.7%  design 5  77.8%   design 6b  52.4%")
    verdict = "PASS" if wrong < WRONG_BAR and unfals < UNFALS_BAR else "FAIL"
    print(f"\n  DESIGN EIGHT: {verdict}")
    return 0


sys.exit(main())
