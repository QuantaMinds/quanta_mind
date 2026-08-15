"""Re-run the same 23 pull requests with structured context and parser-snapped anchors.

WHAT: Same repositories, same funded units, same schema, same model. Two changes only: the prompt
      carries the enclosing class's attributes, the file's other signatures, its imports and the
      call sites of the target function; and every line the model returns is snapped to its
      enclosing statement before anyone grades it.
WHY:  The first run measured 66.7-74.2% of findings wrong across two blind raters. Its two
      largest failure buckets have mechanical causes -- 36.4% cited a blank line or a bracket,
      and 7.6% asserted things only visible elsewhere in the file. This tests whether fixing both
      moves the number, on the same pull requests so the comparison is paired.

      THE BAR IS PRE-REGISTERED AND IT IS NOT "IMPROVEMENT". Perfect anchor repair alone reaches
      45.5% correct by arithmetic. To reverse the stop, this must clear 50% WRONG. Anything less
      confirms it, expensively.
IMPORTS: stdlib only (json, sys, concurrent.futures). Local: `client`, `units`, `context`,
      `anchors`.
CONSUMED BY: nobody -- it prints and writes enriched_findings.jsonl.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor

from anchoring.anchors import snap_pair
from anchoring.context import build as build_context
from client import Client, VertexError
from units import changed_units

MODEL, BUDGET, WORKERS = "gemini-2.5-pro", 3, 6
MAX_OUTPUT_TOKENS, THINKING_BUDGET = 8192, 4096
OUT = "corpora/enriched_findings.jsonl"

SCHEMA = """Return ONLY a JSON array. Each element MUST have exactly these fields:
  claim_type : one of "missing_guard", "wrong_order", "unhandled_case", "resource_leak",
               "contract_violation"
  file       : the file path, copied exactly
  line_a     : integer line number where the defect originates
  line_b     : integer line number where the consequence occurs
  relation   : one sentence stating how line_a causes the problem at line_b
  confidence : "high" or "low"

If you find nothing that fits this form, return []. Do not return prose."""

# Written against the first run's actual failures rather than as generic advice.
RULES = """Rules, each of which a previous run violated:
  - Cite the line of the STATEMENT you mean, never a blank line, a comment, a closing bracket, or
    an argument line below the call it belongs to.
  - Do not assert what a caller passes unless a call site is shown to you below.
  - Do not assert that an attribute may be absent or None if the class attributes below show it
    is always assigned.
  - Do not report a finding whose consequence you cannot name concretely. "May be", "could" and
    "likely" mean you do not have the evidence -- return [] instead.
  - Do not report style, naming, type-annotation tidiness, or a test asserting one thing when it
    could also assert another. Only defects."""


def prompt(repo: str) -> str:
    return (
        f"Repository: {repo}\nYou are reviewing ONE function that a change touched.\n"
        f"{SCHEMA}\n\n{RULES}\n"
    )


def main() -> int:
    with open("corpora/pr_corpus.json") as fh:
        prs = json.load(fh)

    jobs = []
    for pr in prs:
        funded = []
        for f in pr["files"]:
            if not f["source"]:
                continue
            for u in changed_units(str(f["source"]), str(f["patch"])):
                funded.append((f, u))
        funded.sort(key=lambda p: (-int(p[1]["touched"]), -int(p[1]["n_lines"])))
        for f, u in funded[:BUDGET]:
            jobs.append((pr, f, u))
    print(f"  {len(jobs)} requests over {len(prs)} pull requests, {MODEL}, structured context")

    client = Client(MODEL)
    open(OUT, "w").close()

    def run(job):
        pr, f, u = job
        ctx = build_context(str(f["source"]), str(u["name"]))
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt(str(pr["repo"]))},
                        {"text": f"FILE: {f['path']}\n\nDIFF:\n{str(f['patch'])[:6000]}"},
                        {"text": "STRUCTURED CONTEXT FROM THIS FILE:\n" + ctx[:14000]},
                        {
                            "text": f"FUNCTION {u['name']} "
                            f"(lines {u['lineno']}-{u['end_lineno']}):\n"
                            f"{str(u['source'])[:24000]}"
                        },
                    ],
                }
            ],
            "generationConfig": {
                "maxOutputTokens": MAX_OUTPUT_TOKENS,
                "thinkingConfig": {"thinkingBudget": THINKING_BUDGET},
            },
        }
        r = client.generate(body)
        t = r["text"].strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        try:
            found = json.loads(t.strip())
        except json.JSONDecodeError:
            found = []
        if not isinstance(found, list):
            found = []
        snapped = 0
        for item in found:
            if not isinstance(item, dict):
                continue
            a, b = item.get("line_a"), item.get("line_b")
            sa, sb, moved = snap_pair(
                str(f["source"]), a if isinstance(a, int) else 0, b if isinstance(b, int) else 0
            )
            item["line_a_raw"], item["line_b_raw"] = a, b
            item["line_a"], item["line_b"] = sa, sb
            snapped += int(moved)
        return {
            "repo": pr["repo"],
            "pr": pr["number"],
            "file": f["path"],
            "unit": u["name"],
            "findings": found,
            "snapped": snapped,
            "ctx_chars": len(ctx),
            "prompt": r["prompt"],
            "thoughts": r["thoughts"],
            "out": r["out"],
            "finish": r["finish"],
        }

    done = nf = nsnap = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for r in pool.map(run, jobs):
            with open(OUT, "a") as fh:
                fh.write(json.dumps(r) + "\n")
            done += 1
            nf += len(r["findings"])
            nsnap += r["snapped"]
            print(
                f"  [{done:3d}/{len(jobs)}] {str(r['repo']).split('/')[1][:13]:13s} "
                f"#{r['pr']:<6} {str(r['unit'])[:20]:20s} findings={len(r['findings'])} "
                f"snapped={r['snapped']} in={r['prompt']:6d} {r['finish']}"
            )

    print(f"\n  {done} requests, {nf} findings, {nsnap} anchors moved by the parser")
    print("  first run for comparison: 68 requests, 66 findings, no snapping")
    return 0


try:
    sys.exit(main())
except VertexError as exc:
    print(f"  REFUSING TO REPORT — {exc}")
    sys.exit(1)
