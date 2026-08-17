"""Write the discordant issues as blind chunks for a rater outside the Gemini family.

WHAT: Samples the issues where our arm and Greptile's disagreed, writes each as a golden comment
      beside one arm's candidate list under an anonymous label, and writes the label key to a
      SEPARATE file the rater must not open.
WHY:  Our reviewer is Gemini and our judge is Gemini; Greptile's candidates were written by another
      system. Self-preference in an LLM judge would inflate our side of every table in
      `docs/product/greptile-gap-analysis.md`, and it is not a symmetric limitation -- it pushes
      one way. No non-Gemini model is reachable on this Vertex project (Anthropic, Meta and
      Mistral publishers all return 404), so the check has to be a hand adjudication.

      THIS IS THE PATTERN THE PROJECT ALREADY USES. `research/phase0/vertex/rater2..rater6` are
      `RUBRIC.md` plus `chunk_N.md` handed to a rater outside the family that produced the text.
      This writes the same shape.

      THE KEY IS A SEPARATE FILE ON PURPOSE. A rater who can see which arm produced a candidate is
      not blind, and a blindness that depends on the rater choosing not to look is not blindness --
      it is a rule in a docstring, which is what this project keeps finding fails.
IMPORTS: stdlib only (json, pathlib, random, sys).
CONSUMED BY: a human or an out-of-family rater reads `blind/chunk_*.md`; `blind_score.py` reads
      the key and the verdicts together.
"""

from __future__ import annotations

import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
DETAIL = HERE / "gap_detail.json"
COMPARISON = HERE / "martian_comparison.json"
BLIND = HERE / "blind"
SEED = 20260817
PER_ARM = 20  # pre-registered: 20 discordant issues per arm, 40 total


def main() -> int:
    detail = json.loads(DETAIL.read_text())
    ours = json.loads(COMPARISON.read_text())["ours_candidates"]
    sys.path.insert(0, str(HERE))
    import corpus

    theirs = corpus.rival_candidates("greptile-v4-1")

    items: list[dict[str, object]] = []
    for d in detail:
        key = str(d["key"])
        got_o, got_t = set(d["ours_caught"]), set(d["theirs_caught"])  # type: ignore[arg-type]
        for g in d["golden"]:  # type: ignore[union-attr]
            if g in got_t and g not in got_o:
                items.append({"golden": g, "arm": "THEIRS", "cands": theirs.get(key, [])})
            elif g in got_o and g not in got_t:
                items.append({"golden": g, "arm": "OURS", "cands": ours.get(key, [])})

    rng = random.Random(SEED)
    sample: list[dict[str, object]] = []
    for arm in ("OURS", "THEIRS"):
        pool = [i for i in items if i["arm"] == arm]
        sample += rng.sample(pool, min(PER_ARM, len(pool)))
    rng.shuffle(sample)

    BLIND.mkdir(exist_ok=True)
    key_rows = []
    lines = [
        "# Blind adjudication — do these describe the same issue?",
        "",
        "For each item: a GOLDEN comment written by a human reviewer, and the CANDIDATE comments",
        "one automated reviewer produced on that same pull request.",
        "",
        "**Question, for each item: does ANY candidate identify the same underlying issue as the",
        "golden comment?** Different wording is fine. Answer `yes` or `no`.",
        "",
        "You are not told which reviewer produced which candidates. That is deliberate.",
        "",
        "---",
        "",
    ]
    for n, it in enumerate(sample, 1):
        key_rows.append({"item": n, "arm": it["arm"], "golden": it["golden"]})
        lines.append(f"## Item {n}")
        lines.append("")
        lines.append(f"**GOLDEN:** {it['golden']}")
        lines.append("")
        lines.append("**CANDIDATES:**")
        cands = list(it["cands"])  # type: ignore[arg-type]
        if not cands:
            lines.append("- *(the reviewer produced no comments on this pull request)*")
        for c in cands:
            lines.append(f"- {c}")
        lines.append("")
    (BLIND / "chunk_0.md").write_text("\n".join(lines))
    (BLIND / "KEY_DO_NOT_OPEN_UNTIL_RATED.json").write_text(json.dumps(key_rows, indent=1))

    print(f"  {len(items)} discordant issues total; sampled {len(sample)}")
    print(f"  wrote {BLIND / 'chunk_0.md'} ({len(lines)} lines)")
    print(f"  key written separately to {BLIND / 'KEY_DO_NOT_OPEN_UNTIL_RATED.json'}")
    print('\n  Rate every item yes/no, save as blind/verdicts.json as {"1": true, ...},')
    print("  then run blind_score.py. It compares the hand verdicts against the Gemini judge's.")
    return 0


sys.exit(main())
