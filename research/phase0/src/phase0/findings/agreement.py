"""Two raters on the same findings pack: how often they agree, and where they do not.

WHAT: `python -m phase0.findings.agreement --first <md> --second <md> --pack <md>` prints raw
      agreement, Cohen's kappa, each rater's correctness rate, and every disagreement by item.
WHY:  **ONE RATER AT n=24 IS A FIRST MEASUREMENT, NOT A NUMBER TO LEAN ON.**
      `adjudication-preregistration.md` says it plainly — *"A second rater is required before any
      of this is published"* — and the ranking result got one, at 92% agreement and kappa 0.66.
      The 25.0% published-correctness figure has one rater.

      **BLINDNESS IS STRUCTURAL HERE, NOT AN INSTRUCTION.** The first rater's file is moved out of
      the working tree before the second sheet is issued, so a second rater working in this
      repository cannot read it by accident. `PHASE0_PREREGISTRATION.md` A57 voided a whole draw
      because an answer key sat readable next to a blind sheet, and its own conclusion was that
      the protection which failed was an instruction rather than a check.

      **DISAGREEMENTS ARE ITEMISED, NEVER SUMMARISED AWAY.** A kappa says how much two people
      disagreed; it does not say which finding they disagreed about, and that list is the thing
      worth reading — it is where a claim is genuinely ambiguous rather than simply wrong.
IMPORTS: stdlib, phase0.findings.scoring for the shared block parser.
CONSUMED BY: an operator, by hand, after both raters are complete.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from phase0.findings.scoring import VERDICTS, read_blocks, wilson


def kappa(first: dict[str, str], second: dict[str, str]) -> float:
    """Cohen's kappa over the shared items. `nan` when either rater used one category only."""
    items = sorted(set(first) & set(second))
    n = len(items)
    if not n:
        return float("nan")
    observed = sum(first[i] == second[i] for i in items) / n
    a, b = Counter(first[i] for i in items), Counter(second[i] for i in items)
    expected = sum((a[v] / n) * (b[v] / n) for v in VERDICTS)
    if expected >= 1.0:
        return float("nan")
    return (observed - expected) / (1 - expected)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--pack", type=Path, required=True)
    args = parser.parse_args()

    one = {
        k: v["VERDICT"] for k, v in read_blocks(args.first.read_text(), fields=("VERDICT",)).items()
    }
    two = {
        k: v["VERDICT"]
        for k, v in read_blocks(args.second.read_text(), fields=("VERDICT",)).items()
    }
    if set(one) != set(two):
        print(f"the two sheets cover different items ({len(one)} and {len(two)}) — refusing")
        return 1
    blank = sorted(i for i in one if not one[i] or not two[i])
    if blank:
        print(f"unlabelled by one or both, refusing to score: {', '.join(blank)}")
        return 1

    items = sorted(one)
    same = [i for i in items if one[i] == two[i]]
    print(f"RAW AGREEMENT   {len(same)}/{len(items)} = {len(same) / len(items):.1%}")
    print(f"COHEN'S KAPPA   {kappa(one, two):.3f}   (context, not a threshold)")
    print()
    for name, got in (("rater one", one), ("rater two", two)):
        true = sum(v == "TRUE" for v in got.values())
        low, high = wilson(true, len(items))
        counts = Counter(got.values())
        print(
            f"  {name}: TRUE {counts['TRUE']}  FALSE {counts['FALSE']}  UNKNOWN {counts['UNKNOWN']}"
            f"   correct {true}/{len(items)} = {true / len(items):.1%}  95% {low:.1%} to {high:.1%}"
        )

    # **BOTH-AGREE IS THE DEFENSIBLE FLOOR.** A finding two independent readers call correct is a
    # different claim from one a single reader did, and it is the one worth quoting.
    both = sum(one[i] == two[i] == "TRUE" for i in items)
    low, high = wilson(both, len(items))
    agreed = f"{both}/{len(items)} = {both / len(items):.1%}"
    print(f"\n  BOTH CALL CORRECT  {agreed}  95% {low:.1%} to {high:.1%}")

    disagreed = [i for i in items if one[i] != two[i]]
    print(f"\nDISAGREEMENTS   {len(disagreed)}")
    for i in disagreed:
        print(f"  {i}: rater one said {one[i]}, rater two said {two[i]}")
    if disagreed:
        print("\n  These are where the finding is genuinely ambiguous rather than simply wrong.")
        print("  Read them before quoting either rate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
