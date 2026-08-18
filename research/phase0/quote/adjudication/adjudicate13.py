"""Write design thirteen's three arms as blind chunks, arm label held back in the key.

WHAT: Flattens every published finding from arms A, B and C, deduplicates within each arm, mixes in
      sabotaged controls, shuffles the lot, and writes rater chunks plus a key file.
WHY:  Arms B and C change the prompt, so they produce DIFFERENT findings than A -- this is not
      design ten, where B and C were index subsets of A and one rating pass scored all three. Every
      finding must be rated, and the arm that produced it is the one thing the rater must not see.

      THE ARM LABEL IS THE HYPOTHESIS. A rater who can tell which findings came from the expanded
      prompt is a rater who can deliver the result. Arm lives only in KEY_DO_NOT_OPEN.json, and the
      items are shuffled across arms so position carries nothing either.

      SABOTAGED CONTROLS ARE A REAL QUOTE WITH A CLAIM FROM A DIFFERENT PULL REQUEST -- definitively
      wrong, identical in format. A pool that grades them CORRECT is rubber-stamping and its
      ratings are discarded before they are read.
IMPORTS: stdlib only (json, pathlib, random, sys). Local: `corpus`, `gate`.
CONSUMED BY: a rater reads `adj13/chunk_*.md`; `score13.py` joins verdicts to the key.
"""

from __future__ import annotations

import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
RUN = HERE / "results" / "quote13_run.json"
ADJ = HERE / "adj13"
SEED = 20260821
N_SABOTAGE = 10
CONTEXT = 4
PER_CHUNK = 45
# Per ARM, not overall. A single overall cap would sample the arms unevenly and make the
# comparison the run exists to make weaker than the run itself. Fixed before the counts were seen.
MAX_PER_ARM = 60


def context_for(repo: str, pr: int, quote: str) -> list[str]:
    """The diff lines around the quote. Read from the PLAIN diff so every arm looks identical."""
    sys.path.insert(0, str(HERE))
    import gate

    import corpus

    lines = corpus.diff(repo, pr).split("\n")
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
    blob = json.loads(RUN.read_text())
    rng = random.Random(SEED)

    per_arm: dict[str, list[dict]] = {}
    for arm in "ABC":
        seen: set[tuple] = set()
        uniq: list[dict] = []
        for r in blob["results"]:
            for f in r["published"].get(arm, []):
                k = (f["repo"], f["pr"], f["path"], f["line"], " ".join(str(f["claim"]).split()))
                if k in seen:
                    continue
                seen.add(k)
                uniq.append(f)
        per_arm[arm] = uniq if len(uniq) <= MAX_PER_ARM else rng.sample(uniq, MAX_PER_ARM)
        print(f"  arm {arm}: {len(uniq)} unique, {len(per_arm[arm])} rated (cap {MAX_PER_ARM})")

    items: list[dict[str, object]] = []
    for arm, fs in per_arm.items():
        for n, f in enumerate(fs):
            items.append({"kind": "real", "arm": arm, "arm_idx": n, **f})

    pool = list(items)
    for _ in range(N_SABOTAGE):
        a, b = rng.sample(pool, 2)
        while (a["repo"], a["pr"]) == (b["repo"], b["pr"]):
            a, b = rng.sample(pool, 2)
        items.append(
            {
                "kind": "SABOTAGE",
                "arm": "-",
                "arm_idx": -1,
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

    head = [
        "# Adjudication — grade every finding against the rubric",
        "",
        "Each finding is a claim an AI reviewer made about a MERGED pull request from a real",
        "open-source project. You are given the quoted line, the diff around it, the claim, and",
        "the fix the reviewer proposed.",
        "",
        "**Buckets: CORRECT / WRONG / UNFALSIFIABLE / TRIVIAL.** Definitions in",
        "`research/phase0/vertex/rater2/RUBRIC.md` — use them unchanged.",
        "",
        "When a finding is WRONG, add one of these causes as the last word of your sentence:",
        "`EXTERNAL` (deciding it needs a fact the diff cannot supply), `ABSENT` (the code it",
        "describes is not there), `TRACE` (the supporting code IS shown and the reviewer did not",
        "follow it), `OTHER`.",
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
    chunks: list[list[str]] = []
    body: list[str] = []
    for n, it in enumerate(items, 1):
        key.append(
            {
                "item": n,
                "kind": it["kind"],
                "arm": it["arm"],
                "repo": it["repo"],
                "pr": it["pr"],
                "path": it["path"],
                "line": it["line"],
            }
        )
        ctx = context_for(str(it["repo"]), int(str(it["pr"])), str(it["quote"]))
        body += [
            f"## {n}",
            "",
            f"`{it['repo']}#{it['pr']}` — `{it['path']}:{it['line']}`",
            "",
            "```diff",
            *(ctx if ctx else [f"+{it['quote']}"]),
            "```",
            "",
            f"**CLAIM:** {it['claim']}",
            "",
            f"**PROPOSED FIX:** `{str(it['fix'])[:200]}`",
            "",
        ]
        if n % PER_CHUNK == 0:
            chunks.append(body)
            body = []
    if body:
        chunks.append(body)

    for i, c in enumerate(chunks):
        (ADJ / f"chunk_{i}.md").write_text("\n".join(head + c))
    (ADJ / "KEY_DO_NOT_OPEN.json").write_text(json.dumps(key, indent=1))
    n_sab = sum(1 for k in key if k["kind"] == "SABOTAGE")
    print(f"\n  {len(items)} items: {len(items) - n_sab} real, {n_sab} sabotaged controls")
    print(f"  {len(chunks)} chunk(s) in {ADJ}   key held separately")
    print('\n  Grade every item, save adj13/verdicts.json {"1": "CORRECT", ...}, run score13.py.')
    return 0


sys.exit(main())
