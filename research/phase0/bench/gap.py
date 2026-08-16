"""Which specific issues does Greptile find that we miss, and what do they have in common?

WHAT: Re-judges our arm and Greptile's against the same golden comments, keeping the per-issue
      detail the headline run discarded, and writes the four cells: caught by both, caught only by
      Greptile, caught only by us, missed by both.
WHY:  The headline says Greptile beats us by 12.9 points, p = 0.0228. That is a score, not a
      diagnosis. The hypothesis under test is that they index the whole repository and we read one
      diff, so the gap should concentrate in issues whose evidence is NOT in the diff.

      A CAUSE THAT DOES NOT SEPARATE OUTCOMES IS A STORY. So the gap set is cross-tabulated
      against a mechanical marker -- whether the golden comment names a symbol absent from the
      diff we were shown -- rather than read for a narrative.
IMPORTS: stdlib only (json, pathlib, sys). Local: `corpus`, `judge`, and the Vertex `client`.
CONSUMED BY: nobody -- it prints and writes gap_detail.json.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "vertex"))

import judge
from client import Client

import corpus

MODEL = "gemini-2.5-pro"
OUT = pathlib.Path(__file__).resolve().parent / "gap_detail.json"
OURS = pathlib.Path(__file__).resolve().parent / "martian_comparison.json"
RIVAL = "greptile-v4-1"


def main() -> int:
    prs = corpus.pulls()
    ours = json.loads(OURS.read_text())["ours_candidates"]
    theirs = corpus.rival_candidates(RIVAL)
    client = Client(MODEL)

    detail: list[dict[str, object]] = []
    for i, pr in enumerate(prs, 1):
        key = str(pr["key"])
        golden = list(pr["golden"])
        vo = judge.verdicts(client, golden, ours.get(key, []))
        vt = judge.verdicts(client, golden, theirs.get(key, []))
        got_o, got_t = set(vo["tp"]), set(vt["tp"])  # type: ignore[arg-type]
        detail.append(
            {
                "key": key,
                "repo": pr["repo_file"],
                "original": pr["original"],
                "golden": golden,
                "ours_caught": sorted(got_o),
                "theirs_caught": sorted(got_t),
                "ours_n_candidates": len(ours.get(key, [])),
                "theirs_n_candidates": len(theirs.get(key, [])),
                "errors": int(vo["errors"]) + int(vt["errors"]),
            }
        )
        both = len(got_o & got_t)
        only_t = len(got_t - got_o)
        only_o = len(got_o - got_t)
        print(
            f"  {i:2d}/50 {pr['repo_file'][:10]:10s} golden={len(golden):2d} "
            f"both={both:2d} onlyTHEM={only_t:2d} onlyUS={only_o:2d} "
            f"neither={len(golden) - len(got_o | got_t):2d}"
        )

    OUT.write_text(json.dumps(detail, indent=1))

    tot = sum(len(d["golden"]) for d in detail)  # type: ignore[arg-type]
    both = sum(len(set(d["ours_caught"]) & set(d["theirs_caught"])) for d in detail)  # type: ignore[arg-type]
    only_t = sum(len(set(d["theirs_caught"]) - set(d["ours_caught"])) for d in detail)  # type: ignore[arg-type]
    only_o = sum(len(set(d["ours_caught"]) - set(d["theirs_caught"])) for d in detail)  # type: ignore[arg-type]
    neither = tot - both - only_t - only_o
    print(f"\n  {tot} golden comments across {len(detail)} pull requests\n")
    print(f"  {'caught by both':22s} {both:4d} {both / tot:7.1%}")
    print(f"  {'only GREPTILE':22s} {only_t:4d} {only_t / tot:7.1%}   <- the gap")
    print(f"  {'only US':22s} {only_o:4d} {only_o / tot:7.1%}")
    print(f"  {'neither':22s} {neither:4d} {neither / tot:7.1%}")
    print(f"\n  net gap: {only_t - only_o:+d} issues")
    return 0


sys.exit(main())
