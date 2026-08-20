"""Write design fourteen's findings as blind chunks, with sabotaged controls mixed in.

WHAT: Flattens every published finding from the single arm, deduplicates, mixes in sabotaged
      controls, shuffles, and writes rater chunks plus a key file the rater never sees.
WHY:  Bars and corpus are fixed in
      docs/plans/preregistrations/reviewer/design14-model-lever-preregistration.md before the run.

      **ONE ARM, SO THERE IS NO ARM LABEL TO HIDE -- AND THE BLINDING STILL MATTERS.** Design
      thirteen hid the arm because the arm was the hypothesis. Here the hypothesis is the
      wrong-rate itself, so what must not leak is which items are the planted controls and what the
      run is expected to score. The rater grades a shuffled pool and nothing else.

      **SABOTAGED CONTROLS ARE A REAL QUOTE WITH A CLAIM FROM A DIFFERENT PULL REQUEST** --
      definitively wrong, identical in format. A pool that grades them CORRECT is rubber-stamping,
      and its verdicts describe the pool rather than the design. Design thirteen's rater caught 10
      of 10, which is why its numbers are usable at all.

      **THE CAP IS ON THE POOL, NOT PER REPOSITORY.** Sampling evenly per repository would build a
      corpus the run did not measure: `sqlalchemy/sqlalchemy` supplies the fewest usable pull
      requests of the six and levelling it up would overweight it. The pool is what the run
      produced.
IMPORTS: stdlib only (json, pathlib, random, sys). Local: `corpus`, `gate`.
CONSUMED BY: a rater reads `adj14/chunk_*.md`; `score14.py` joins verdicts to the key.
"""

from __future__ import annotations

import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
RUN = HERE / "results" / "quote14_run.json"
ADJ = HERE / "adj14"
SEED = 20260819
N_SABOTAGE = 12
CONTEXT = 4
PER_CHUNK = 45


def context_for(repo: str, pr: int, quote: str) -> list[str]:
    """The diff lines around the quote, read from the same diff the model was shown."""
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


HEAD = [
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


def main() -> int:
    blob = json.loads(RUN.read_text())
    rng = random.Random(SEED)

    seen: set[tuple[object, ...]] = set()
    uniq: list[dict[str, object]] = []
    for r in blob["results"]:
        for f in r.get("published") or []:
            k = (f["repo"], f["pr"], f["path"], f["line"], " ".join(str(f["claim"]).split()))
            if k in seen:
                continue
            seen.add(k)
            uniq.append(f)
    print(f"  {len(uniq)} unique published findings from {blob['reviewable']} reviewable PRs")

    items: list[dict[str, object]] = [{"kind": "real", **f} for f in uniq]
    if len(items) < 2:
        print("  too few findings to build a pool; nothing to adjudicate")
        return 1

    pool = list(items)
    for _ in range(N_SABOTAGE):
        a, b = rng.sample(pool, 2)
        tries = 0
        while (a["repo"], a["pr"]) == (b["repo"], b["pr"]) and tries < 50:
            a, b = rng.sample(pool, 2)
            tries += 1
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

    key: list[dict[str, object]] = []
    chunks: list[list[str]] = []
    body: list[str] = []
    for n, it in enumerate(items, 1):
        key.append(
            {
                "item": n,
                "kind": it["kind"],
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
        (ADJ / f"chunk_{i}.md").write_text("\n".join(HEAD + c))
    (ADJ / "KEY_DO_NOT_OPEN.json").write_text(json.dumps(key, indent=1))
    n_sab = sum(1 for k in key if k["kind"] == "SABOTAGE")
    print(f"\n  {len(items)} items: {len(items) - n_sab} real, {n_sab} sabotaged controls")
    print(f"  {len(chunks)} chunk(s) in {ADJ}   key held separately")
    print(
        '\n  Grade every item, save adj14/verdicts.json {"1": "CORRECT ...", ...}, run score14.py.'
    )
    return 0


sys.exit(main())
