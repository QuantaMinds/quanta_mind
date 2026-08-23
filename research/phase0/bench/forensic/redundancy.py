"""How many goldens each arm covers, how many comments it spent, and how often it repeated itself.

WHAT: One judging pass over all four arms, storing BOTH counts per pull request -- goldens covered
      and candidates that matched -- so coverage per correct comment is read from a single judge.
WHY:  **THE APPARENT +32 SWING IN CODERABBIT'S TRUE POSITIVES WAS NOT JUDGE NOISE.** Three
      replicates over identical candidates spread 2.1 points. The swing was two code paths
      counting different things: `run.py:judge_arm()` counts goldens matched, at most one per
      golden, and `label_candidates.py` counts candidates that matched anything. Their difference
      IS the redundancy -- candidates restating a golden a sibling already covered.

      **AND THE FIRST VERSION OF THAT TABLE COMPARED OUR JUDGE'S COUNT TO MARTIAN'S PUBLISHED
      ONE FOR QODO**, which is the same defect this file exists to remove: two instruments, one
      column. Qodo could not appear until every arm was scored by one judge in one pass, and that
      is what this is.
IMPORTS: stdlib; local `martian_corpus`, `judge`, and the Vertex `client`.
CONSUMED BY: read by a human; writes `results/redundancy.json`.
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

OUT = HERE.parent / "results" / "redundancy.json"
ARMS = ("OURS", "qodo-extended-v2", "greptile-v4-1", "coderabbit")


def main() -> int:
    mc._assert_intact()
    client = Client("gemini-2.5-pro")
    ours = json.loads((HERE.parent / "results" / "martian_comparison.json").read_text())[
        "ours_candidates"
    ]
    pulls = [p for p in mc.pulls() if p.get("golden")]

    out: dict[str, dict[str, float]] = {}
    for arm in ARMS:
        cands = ours if arm == "OURS" else mc.rival_candidates(arm)
        covered = matched = emitted = 0
        for p in pulls:
            texts = cands.get(str(p["key"]), [])
            if not texts:
                continue
            v = judge.verdicts(client, list(p["golden"]), texts)
            covered += len(v["tp"])
            matched += len(texts) - len(set(v["fp"]))
            emitted += len(texts)
        out[arm] = {
            "goldens_covered": covered,
            "candidates_matching": matched,
            "emitted": emitted,
            "redundant": matched - covered,
            "goldens_per_correct_comment": covered / max(1, matched),
        }
        print(
            f"  {arm:<18} covered {covered:>3}  matching {matched:>3}  emitted {emitted:>3}  "
            f"redundant {matched - covered:>+3}  goldens/correct comment "
            f"{covered / max(1, matched):.2f}",
            flush=True,
        )

    OUT.write_text(json.dumps(out, indent=1))
    print(f"\n  -> {OUT}")
    print(
        "\n  goldens/correct comment above 1.00 means one comment covered more than one defect;\n"
        "  below 1.00 means several comments were spent on one defect."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
