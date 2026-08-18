"""When G-evidence fires, is the evidence ABSENT or merely UNMATCHED?

WHAT: For every finding the evidence gate rejected, classifies the cited evidence four ways --
      found in an added line under a looser match, found elsewhere in the diff but not in an added
      line, found nowhere, or empty.
WHY:  A 62% gate rejection rate has two opposite readings and the joint gate distribution cannot
      separate them. If the cited text is nearly present -- whitespace, a paraphrase, a span across
      a hunk boundary -- then the number measures THE GATE'S STRICTNESS. If it appears nowhere,
      the number measures THE MODEL'S GROUNDING.

      This is the same shape as the G-quote known-answer test: ask what the check outputs when the
      thing it checks is fine, not only when it is broken.
IMPORTS: stdlib only (collections, json, pathlib, re, sys). Local: `corpus`, `gate`, `paths`.
CONSUMED BY: nobody -- it prints.
"""

from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

import gate
import paths

import corpus

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

RUN = pathlib.Path(__file__).resolve().parent.parent / "results" / "quote11_run.json"


def squash(s: str) -> str:
    """Whitespace and punctuation removed -- the loosest match worth calling 'nearly present'."""
    return re.sub(r"[^A-Za-z0-9_]", "", s).lower()


def ellipsis_match(ev: str, added: list) -> bool:
    """Would this match if `...` were allowed, as Qodo's own instruction permits?

    Their `existing_code` field says "Include only complete code lines. Use ellipsis (...) for
    brevity if needed", so their anchor is NOT a strict verbatim match and ours is. A field that
    would match under their rule and fails under ours is neither absent evidence nor a matching
    bug -- it is our gate being stricter than the design it was copied from.
    """
    if "..." not in ev and "\u2026" not in ev:
        return False
    parts = [squash(x) for x in re.split(r"\.\.\.|\u2026", ev) if squash(x)]
    if not parts:
        return False
    return any(all(pt in squash(t) for pt in parts) for _p, _l, t, _h in added)


def classify(ev: str, diff: str, added: list) -> str:
    if not ev.strip():
        return "empty"
    if ev.strip().upper() == "SAME":
        return "SAME"
    if gate.locate(ev, added) is not None:
        return "matched (gate should not have fired)"
    if ellipsis_match(ev, added):
        return "would match if ELLIPSIS allowed (Qodo permits it, we do not)"
    sq = squash(ev)
    if len(sq) < 6:
        return "too short to match"
    if any(sq in squash(t) or squash(t) in sq for _p, _l, t, _h in added):
        return "NEAR MISS in an added line"
    if sq in squash(diff):
        return "present in the diff but NOT an added line"
    return "absent from the diff entirely"


def main() -> int:
    blob = json.loads(RUN.read_text())
    arm = blob["arm_e"]
    rejected = [f for f in arm["raw"] if "G-evidence" in f["failed"]]
    print(
        f"  {len(arm['raw'])} raw findings in the evidence arm; "
        f"{len(rejected)} rejected by G-evidence\n"
    )
    if not rejected:
        print("  nothing to classify")
        return 0

    counts: collections.Counter[str] = collections.Counter()
    cache: dict[tuple[str, int], tuple[str, list]] = {}
    for f in rejected:
        k = (str(f["repo"]), int(str(f["pr"])))
        if k not in cache:
            d, _r, _kept = paths.filter_diff(corpus.diff(*k))
            added, _s = gate.added_lines(d)
            cache[k] = (d, added)
        d, added = cache[k]
        counts[classify(str(f.get("raw_evidence") or ""), d, added)] += 1

    n = sum(counts.values())
    print(f"  {'classification':44s} {'n':>4} {'share':>7}")
    for k, c in counts.most_common():
        print(f"  {k:44s} {c:4d} {c / n:6.0%}")

    near = (
        counts["NEAR MISS in an added line"] + counts["present in the diff but NOT an added line"]
    )
    print(f"\n  NEARLY PRESENT: {near}/{n} = {near / n:.0%}")
    if near / n > 0.5:
        print("  -> the 62% is measuring THE GATE'S STRICTNESS, not the model's grounding.")
    else:
        print("  -> the cited evidence mostly appears nowhere. The gate is working as designed.")
    return 0


sys.exit(main())
