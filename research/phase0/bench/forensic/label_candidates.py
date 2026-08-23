"""Label EVERY candidate of every arm TP or FP, and keep the label. Nothing on disk had them.

WHAT: Re-judges our arm and each rival's, candidate by candidate, against the same golden comments,
      and writes one flat row per candidate: arm, pull request, text, and the verdict.
WHY:  **THE PER-CANDIDATE LABELS WERE NEVER STORED, AND FOUR ANALYSES WERE BUILT ON GUESSES ABOUT
      THEM.** `martian_comparison.json` keeps aggregate tp/fp/fn and the raw candidate list;
      `gap_detail.json` keeps which GOLDENS were caught. Neither says which CANDIDATE was right.

      Every forensic question — do our false positives land where the defects are, do we duplicate a
      true finding into three wrong ones, what do we say when we are wrong — needs the label on the
      candidate. Inferring it from `ours_caught`, which holds goldens rather than candidates, gave
      an answer that looked plausible and was arithmetically impossible: it marked all 194 of our
      candidates false.

      **So this run exists to make the labels a stored artefact rather than a re-derivation.**
IMPORTS: stdlib; local `martian_corpus`, `judge`, and the Vertex `client`.
CONSUMED BY: `forensics.py` in this package.
"""

from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "vertex"))
sys.path.insert(0, str(HERE.parent))

import judge  # noqa: E402
import martian_corpus as mc  # noqa: E402
from client import Client  # noqa: E402

OUT = HERE.parent / "results" / "candidate_labels.json"
RIVALS = ("qodo-extended-v2", "greptile-v4-1", "coderabbit")


def main() -> int:
    mc._assert_intact()
    client = Client("gemini-2.5-pro")
    ours = json.loads((HERE.parent / "results" / "martian_comparison.json").read_text())[
        "ours_candidates"
    ]
    golden = {str(pr["key"]): list(pr["golden"]) for pr in mc.pulls()}

    arms: dict[str, dict[str, list[str]]] = {"OURS": ours}
    for r in RIVALS:
        arms[r] = mc.rival_candidates(r)

    rows: list[dict[str, object]] = []
    for arm, cands in arms.items():
        n = 0
        for key, texts in cands.items():
            g = golden.get(key) or []
            if not g or not texts:
                continue
            v = judge.verdicts(client, g, texts)
            fp = set(v["fp"])
            for t in texts:
                rows.append(
                    {"arm": arm, "pr": key, "text": t, "verdict": "FP" if t in fp else "TP"}
                )
            n += len(texts)
            print(f"    {arm:<18} {key.split('/')[-1]:>8}  {len(texts):>2} cands", flush=True)
        print(f"  {arm}: {n} candidates labelled", flush=True)

    OUT.write_text(json.dumps(rows, indent=1))
    print(f"\n  {len(rows)} rows -> {OUT}")
    for arm in arms:
        a = [r for r in rows if r["arm"] == arm]
        tp = sum(1 for r in a if r["verdict"] == "TP")
        if a:
            print(f"    {arm:<18} {tp:>3}/{len(a):<4} TP = {tp / len(a):.1%} precision")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
