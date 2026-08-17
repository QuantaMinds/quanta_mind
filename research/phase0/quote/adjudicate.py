"""Write the published findings as blind chunks, with sabotaged controls mixed in.

WHAT: Renders each published finding as its quoted line in diff context, the claim, and the fix,
      shuffles in SABOTAGED findings whose claim comes from a different pull request, and writes
      the key to a separate file.
WHY:  G2 -- published findings under 50% wrong -- is the bar the review half failed seven times and
      it is the only one that decides anything. It needs a rater outside the Gemini family that
      produced the findings.

      THE RATER KNOWS THE HYPOTHESIS AND WANTS IT TO PASS. Every earlier adjudication in this
      project blinded the rater to which DESIGN produced a finding; here all findings come from one
      design, so that form of blinding is unavailable and something else has to carry the weight.

      SO THE CONTROLS ARE SABOTAGED FINDINGS: a real quote from one pull request paired with a real
      claim from another. They are definitively WRONG -- the claim does not describe the quoted
      code -- and they are indistinguishable in format from the real ones. **A rater who grades
      them CORRECT is rubber-stamping, and the rate at which that happens is the measurement of
      whether this adjudication can be believed at all.**
IMPORTS: stdlib only (json, pathlib, random, sys).
CONSUMED BY: a rater reads `adj/chunk_*.md`; `adjudicate_score.py` joins verdicts to the key.
"""

from __future__ import annotations

import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
# Which run to adjudicate. Design eight by default; pass "9" for the path-filtered run.
WHICH = sys.argv[1] if len(sys.argv) > 1 else "8"
RUN = HERE / ("quote9_run.json" if WHICH == "9" else "quote_run.json")
ADJ = HERE / ("adj9" if WHICH == "9" else "adj")
SEED = 20260818 if WHICH == "8" else 20260819
N_SABOTAGE = 8
CONTEXT = 4
# Hand adjudication has a practical ceiling. Fixed BEFORE design nine's count was known, and
# chosen for rater capacity rather than for the result: a larger published set is sampled down
# with a fixed seed, and the sampling is reported beside the wrong-rate.
MAX_RATED = 70


def context_for(repo: str, pr: int, quote: str) -> list[str]:
    """The diff lines around the quote, so the rater can judge the claim against real code."""
    sys.path.insert(0, str(HERE))
    import gate

    import corpus

    diff = corpus.diff(repo, pr)
    lines = diff.split("\n")
    needle = gate._norm(quote)
    first = next((gate._norm(x) for x in quote.split("\n") if gate._norm(x)), needle)
    for i, ln in enumerate(lines):
        if not ln.startswith("+") or ln.startswith("+++"):
            continue
        hay = gate._norm(ln[1:])
        if (needle and needle in hay) or (first and first in hay):
            return lines[max(0, i - CONTEXT) : i + CONTEXT + 1]
    return []


def main() -> int:
    pub = json.loads(RUN.read_text())["published"]
    rng = random.Random(SEED)

    sampled = pub if len(pub) <= MAX_RATED else rng.sample(pub, MAX_RATED)
    items: list[dict[str, object]] = []
    for p in sampled:
        items.append({"kind": "real", **p})

    # Sabotage: a real quote, a real claim, deliberately from DIFFERENT pull requests.
    pool = [p for p in sampled if len({(q["repo"], q["pr"]) for q in sampled}) > 1]
    for _ in range(N_SABOTAGE):
        a, b = rng.sample(pool, 2)
        while (a["repo"], a["pr"]) == (b["repo"], b["pr"]):
            a, b = rng.sample(pool, 2)
        items.append(
            {
                "kind": "SABOTAGE",
                "repo": a["repo"],
                "pr": a["pr"],
                "quote": a["quote"],
                "path": a["path"],
                "line": a["line"],
                "claim": b["claim"],  # describes different code entirely
                "fix": a["fix"],
            }
        )

    rng.shuffle(items)
    ADJ.mkdir(exist_ok=True)

    out = [
        "# Adjudication — grade every finding against the rubric",
        "",
        "Each finding is a claim an AI reviewer made about a MERGED pull request from a real",
        "open-source project. You are given the quoted line, the diff around it, the claim, and",
        "the fix the reviewer proposed.",
        "",
        "**Buckets: CORRECT / WRONG / UNFALSIFIABLE / TRIVIAL.** Definitions in",
        "`research/phase0/vertex/rater2/RUBRIC.md` — use them unchanged.",
        "",
        "A claim that does not describe the quoted code is WRONG. These pull requests are MERGED,",
        "so a claim that a passing test's assertion is wrong is false.",
        "",
        "Output one line per finding: `<index> <BUCKET> <one sentence giving the deciding fact>`",
        "",
        "---",
        "",
    ]
    key = []
    for n, it in enumerate(items, 1):
        key.append({"item": n, "kind": it["kind"], "repo": it["repo"], "pr": it["pr"]})
        ctx = context_for(str(it["repo"]), int(str(it["pr"])), str(it["quote"]))
        out.append(f"## {n}")
        out.append("")
        out.append(f"`{it['repo']}#{it['pr']}` — `{it['path']}:{it['line']}`")
        out.append("")
        out.append("```diff")
        out += ctx if ctx else [f"+{it['quote']}"]
        out.append("```")
        out.append("")
        out.append(f"**CLAIM:** {it['claim']}")
        out.append("")
        out.append(f"**PROPOSED FIX:** `{str(it['fix'])[:200]}`")
        out.append("")

    (ADJ / "chunk_0.md").write_text("\n".join(out))
    (ADJ / "KEY_DO_NOT_OPEN.json").write_text(json.dumps(key, indent=1))
    n_sab = sum(1 for k in key if k["kind"] == "SABOTAGE")
    print(
        f"  {len(pub)} published; {len(sampled)} sampled for rating (cap {MAX_RATED}, seed fixed)"
    )
    print(f"  {len(items)} items written: {len(items) - n_sab} real, {n_sab} sabotaged controls")
    print(f"  {ADJ / 'chunk_0.md'}  ({len(out)} lines)")
    print(f"  key held separately in {ADJ / 'KEY_DO_NOT_OPEN.json'}")
    print('\n  Grade every item, save as adj/verdicts.json {"1": "CORRECT", ...},')
    print("  then run adjudicate_score.py. Sabotaged items graded CORRECT measure rubber-stamping.")
    return 0


sys.exit(main())
