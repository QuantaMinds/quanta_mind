"""Score a labelled findings pack. The deciding line is what makes a verdict admissible.

WHAT: `python -m phase0.findings.scoring --labels <md> --pack <md>` prints the share of
      PUBLISHED findings a human judged correct, with a Wilson interval.
WHY:  **A VERDICT WITHOUT A DECIDING LINE IS NOT SCORED.** For TRUE and FALSE the rater must
      quote a line that is actually in that item's diff. This replaces the planted control arm,
      which a rater could pass by checking filenames without ever assessing a finding -- an
      isolated judge scored 12 of 12 on it while doing exactly that. A quoted line cannot be
      produced without reading the code, and whether it is really there is checkable.

      **UNKNOWN IS A FIRST-CLASS VERDICT AND NEEDS NO LINE.** It is the honest answer when
      deciding would require code or library behaviour outside the diff, and the judge run
      showed why it must exist: with only TRUE/FALSE available, confident FALSEs were returned
      on recalled facts, one of which was verifiably backwards.

      **TWO RATES ARE PRINTED AND NEITHER IS "THE" NUMBER.** Correct over all items counts
      UNKNOWN against the finding; correct over decided items does not. They answer different
      questions and quoting one without the other is how a rate loses its denominator.
IMPORTS: stdlib only.
CONSUMED BY: an operator, by hand, after the labels are committed.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from phase0.findings.deciding_line import locate

# A sheet this one-sided cannot be told apart from a constant responder.
CONSTANT_AT = 0.9
VERDICTS = {"TRUE", "FALSE", "UNKNOWN"}
# **DIRECTION HAS A MECHANICAL RIGHT ANSWER**, which is the whole point of asking for it. A
# rater who describes what the commit does rather than judging the claim never has to locate the
# claim's own code; this makes them locate it. On the item that exposed this, the claim asserts a
# sentinel IS yielded and the diff deletes it -- answering REMOVED makes that visible.
DIRECTIONS = {"ADDED", "REMOVED"}
NEEDS_LINE = {"TRUE", "FALSE"}
Z = 1.96


def wilson(hits: int, n: int) -> tuple[float, float]:
    """Wilson score interval. The normal approximation is wrong at this n and near the ends."""
    if n == 0:
        return (0.0, 1.0)
    p = hits / n
    mid = (p + Z * Z / (2 * n)) / (1 + Z * Z / n)
    half = Z * ((p * (1 - p) / n + Z * Z / (4 * n * n)) ** 0.5) / (1 + Z * Z / n)
    return (max(0.0, mid - half), min(1.0, mid + half))


def read_blocks(text: str, *, fields: tuple[str, ...]) -> dict[str, dict[str, str]]:
    """Parse `## item NN` sections into `{item: {FIELD: value}}`. Missing fields come back empty."""
    out: dict[str, dict[str, str]] = {}
    parts = re.split(r"^## (item \d\d)\s*$", text, flags=re.M)[1:]
    for name, body in zip(parts[::2], parts[1::2], strict=True):
        got = dict.fromkeys(fields, "")
        for field in fields:
            found = re.search(rf"^{field}:[ \t]*(.*)$", body, flags=re.M)
            if found:
                got[field] = found.group(1).strip()
        out[name] = got
    return out


def diffs_of(pack_text: str) -> dict[str, str]:
    """The code shown for each item, so a cited line can be checked against it."""
    out: dict[str, str] = {}
    parts = re.split(r"^## (item \d\d)\s*$", pack_text, flags=re.M)[1:]
    for name, body in zip(parts[::2], parts[1::2], strict=True):
        block = re.search(r"```diff\n(.*?)```", body, flags=re.S)
        out[name] = block.group(1) if block else ""
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--pack", type=Path, required=True)
    args = parser.parse_args()

    shown = diffs_of(args.pack.read_text())
    labels = read_blocks(args.labels.read_text(), fields=("VERDICT", "LINE", "DIRECTION"))

    if set(labels) != set(shown):
        print(f"labels cover {len(labels)} items, the pack has {len(shown)} -- refusing to score")
        return 1
    blank = sorted(i for i, v in labels.items() if not v["VERDICT"])
    if blank:
        print(f"unlabelled, refusing to score: {', '.join(blank)}")
        return 1
    bad = {v["VERDICT"] for v in labels.values()} - VERDICTS
    if bad:
        print(f"not a verdict: {sorted(bad)}")
        return 1

    # **THE ATTENTION CHECK.** A cited line that is not in the code shown means the verdict was
    # not read off that code. Inadmissible, and named per item rather than summarised away.
    unquoted: list[str] = []
    for name, got in sorted(labels.items()):
        if got["VERDICT"] not in NEEDS_LINE:
            continue
        line = got["LINE"].strip().strip("`")
        placed = locate(line, shown[name])
        if not placed.placed:
            unquoted.append(f"{name} ({got['VERDICT']}): {placed.reason}")
    if unquoted:
        print(f"VERDICTS WITHOUT AN ADMISSIBLE DECIDING LINE   {len(unquoted)} of {len(labels)}")
        print()
        for u in unquoted:
            print(f"  {u}")
        print()
        print("  A verdict whose deciding line is not in the code shown was not read off that")
        print("  code. The rate is NOT computed -- fix these, or record why the line is absent.")
        return 2

    # **WHAT A ROBOT WOULD SCORE, PRINTED BESIDE WHAT THE RATER SCORED.** A second rater
    # returned 23 TRUE of 24 and scored 95.8%; a responder answering TRUE unconditionally scores
    # the same. Nothing in the output said so, so the number read as a measurement. It now cannot
    # be quoted without its own null beside it.
    # The cited line's direction is checked against the diff, when the sheet asks for it.
    wrong_way: list[str] = []
    for name, got in sorted(labels.items()):
        if got["VERDICT"] not in NEEDS_LINE:
            continue
        said = got.get("DIRECTION", "").strip().upper()
        if said not in DIRECTIONS:
            # **MISSING IS NOT SKIPPED.** An absent field made this check pass over the item in
            # silence, which is the same shape as every defect this instrument was built after.
            wrong_way.append(f"{name}: no DIRECTION given ({said or 'blank'})")
            continue
        placed = locate(got["LINE"].strip().strip("`"), shown[name])
        if not placed.placed:
            # **UNPLACEABLE IS REPORTED, NOT SKIPPED.** `if truth and ...` passed over these,
            # so a sheet citing diff headers went through this gate untouched.
            wrong_way.append(f"{name}: cannot be placed -- {placed.reason}")
        elif said != placed.direction:
            wrong_way.append(f"{name}: said {said}, the diff shows {placed.direction}")
    if wrong_way:
        print(f"DECIDING LINES POINTING THE WRONG WAY   {len(wrong_way)} of {len(labels)}")
        print()
        for w in wrong_way:
            print(f"  {w}")
        print()
        print("  A verdict whose own deciding line was not located in the diff was not read off")
        print("  it. The rate is NOT computed.")
        return 4

    counts = {v: sum(g["VERDICT"] == v for g in labels.values()) for v in sorted(VERDICTS)}
    decided = counts["TRUE"] + counts["FALSE"]
    print(f"TRUE {counts['TRUE']}   FALSE {counts['FALSE']}   UNKNOWN {counts['UNKNOWN']}")
    top = max(counts.values())
    if top >= len(labels) * CONSTANT_AT:
        share = top / len(labels)
        print()
        print(f"  ONE VERDICT ON {share:.0%} OF ITEMS. A responder answering that verdict to")
        print("  every item is indistinguishable from this sheet on every check here.")
        print("  THE RATE IS WITHHELD -- not computed, not printed under a caveat.")
        print()
        print("  This is not an accusation of carelessness. It says the instrument cannot")
        print("  separate this rating from a constant one, which makes the number unusable")
        print("  either way. A second reading is the only thing that resolves it.")
        return 3
    print(f"every verdict cites a line present in its own diff  ({len(labels)} of {len(labels)})")
    print()
    n = len(labels)
    low, high = wilson(counts["TRUE"], n)
    rate = counts["TRUE"] / n
    print(
        f"CORRECT, over all items      {counts['TRUE']}/{n} = {rate:.1%}"
        f"   95% {low:.1%} to {high:.1%}   (UNKNOWN counts against)"
    )
    if decided:
        lo_d, hi_d = wilson(counts["TRUE"], decided)
        rate_d = counts["TRUE"] / decided
        print(
            f"CORRECT, over decided items  {counts['TRUE']}/{decided} = {rate_d:.1%}"
            f"   95% {lo_d:.1%} to {hi_d:.1%}   (UNKNOWN excluded)"
        )
    print()
    print("Correctness of a PUBLISHED finding -- after the anchor gate and the refutation pass,")
    print("not the raw model error rate. One repository, one language, consecutive commits,")
    print("unstratified. The intervals are sampling error alone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
