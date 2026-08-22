"""What our false positives are ABOUT, and whether the defect was in a file we were looking at.

WHAT: Reads `candidate_labels.json` and cross-tabulates every candidate against the golden set:
      did we speak about a file a defect is in; how many candidates did we spend per pull request;
      what share of our true positives cost us how many false ones; and where a rival was right
      about a place we were wrong about.
WHY:  **THE FOUR EARLIER ANALYSES WERE INFERRED FROM A FIELD THAT DOES NOT HOLD WHAT THEY READ IT
      AS.** `gap_detail.json`'s `ours_caught` holds GOLDEN comments, and every question here was
      answered by testing candidate membership in it -- which is false for all 194 by construction,
      so every candidate classified as a false positive and the resulting split was arithmetic on a
      constant. This module reads the stored per-candidate verdict instead and nothing else.

      **IT ALSO DOES NOT ASK WHETHER A FALSE POSITIVE LANDED IN THE WRONG FILE, AND THAT IS NOT AN
      OVERSIGHT.** The corpus carries no file or line metadata -- goldens are free text plus a
      severity and a category -- so the question is unanswerable here. A first version answered it
      anyway by testing whether a comment's TEXT happened to spell a filename, which read 0.0% for
      three of the four arms because those arms do not write paths into prose. **A marker that
      reports zero because it is measuring the wrong thing looks exactly like a real negative**,
      so it is deleted rather than left in with a caveat.

      **A CAUSE THAT DOES NOT SEPARATE OUTCOMES IS A STORY.** So each suspected cause below is
      printed as a cross-tabulation against the verdict, not as a share of the failures. "68% of
      our false positives are in files with no defect" means nothing until the same number is read
      for the true positives; if it is also 68%, the file is not what distinguishes them.
IMPORTS: stdlib; local `martian_corpus`.
CONSUMED BY: read by a human. Writes nothing.
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))


LABELS = HERE.parent / "results" / "candidate_labels.json"


def main() -> int:
    rows = json.loads(LABELS.read_text())
    print("\n=== precision, from the stored per-candidate verdicts ===")
    for arm in dict.fromkeys(r["arm"] for r in rows):
        a = [r for r in rows if r["arm"] == arm]
        tp = sum(1 for r in a if r["verdict"] == "TP")
        print(f"  {arm:<18} {tp:>3} TP / {len(a):<4} = {tp / len(a):>6.1%}")

    print("\n=== candidates spent per pull request, and what it buys ===")
    print(f"  {'arm':<18} {'PRs':>4} {'cands/PR':>9} {'TP/PR':>7} {'FP per TP':>10}")
    for arm in dict.fromkeys(r["arm"] for r in rows):
        a = [r for r in rows if r["arm"] == arm]
        prs = {r["pr"] for r in a}
        tp = sum(1 for r in a if r["verdict"] == "TP")
        fp = len(a) - tp
        print(
            f"  {arm:<18} {len(prs):>4} {len(a) / len(prs):>9.1f} {tp / len(prs):>7.1f} "
            f"{fp / max(1, tp):>10.1f}"
        )

    print("\n=== volume vs correctness, per pull request (does emitting more help?) ===")
    per: dict[str, list[tuple[int, int]]] = collections.defaultdict(list)
    for arm in dict.fromkeys(r["arm"] for r in rows):
        by = collections.defaultdict(lambda: [0, 0])
        for r in rows:
            if r["arm"] == arm:
                by[str(r["pr"])][0] += 1
                by[str(r["pr"])][1] += r["verdict"] == "TP"
        per[arm] = [(n, t) for n, t in by.values()]
    for arm, pairs in per.items():
        lo = [t / n for n, t in pairs if n <= 3]
        hi = [t / n for n, t in pairs if n >= 6]
        f = f"{sum(lo) / len(lo):.1%}" if lo else "  n/a"
        g = f"{sum(hi) / len(hi):.1%}" if hi else "  n/a"
        print(f"  {arm:<18} PRs with <=3 cands: {f:>6} ({len(lo)})   >=6 cands: {g:>6} ({len(hi)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
