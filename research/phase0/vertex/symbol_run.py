"""Run the reviewer with symbol names instead of line numbers, on the unseen corpus.

WHAT: Same model, budget, context and repositories as the previous run. One change: the schema
      asks for `symbol_a` and `symbol_b` rather than `line_a` and `line_b`, and the parser derives
      the lines. A finding naming a symbol absent from the shown function is rejected mechanically.
WHY:  Three fixes failed against a reviewer whose dominant defect is that its prose and its line
      numbers are generated independently -- 87.3% of claims quote code not at the line they cite.
      This removes the ability to emit a number rather than trying to correct one.

      DECISIVE IN BOTH DIRECTIONS, which is the reason to run it. Anchor correctness becomes true
      by construction, so the only interesting number is the WRONG-RATE. If it falls under 50% the
      decoupling was causal. If it stays high while anchors are correct by construction, the
      decoupling was a symptom and the reasoning was always the problem.
IMPORTS: stdlib only (json, sys, concurrent.futures). Local: `client`, `units`, `context`,
      `symbols`.
CONSUMED BY: nobody -- it prints and writes symbol_findings.jsonl.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor

from anchoring.context import build as build_context
from anchoring.symbols import resolve
from client import Client, VertexError
from units import changed_units

MODEL, BUDGET, WORKERS = "gemini-2.5-pro", 3, 6
MAX_OUTPUT_TOKENS, THINKING_BUDGET = 8192, 4096
OUT = "corpora/symbol_findings.jsonl"

SCHEMA = """Return ONLY a JSON array. Each element MUST have exactly these fields:
  claim_type : one of "missing_guard", "wrong_order", "unhandled_case", "resource_leak",
               "contract_violation"
  file       : the file path, copied exactly
  symbol_a   : the NAME of the variable, attribute, function or argument where the defect
               originates. A bare identifier, e.g. "worker_support". NOT a line number, NOT an
               expression, NOT prose.
  symbol_b   : the NAME of the variable, attribute, function or argument where the consequence
               occurs. Same rules.
  relation   : one sentence stating how symbol_a causes the problem at symbol_b
  confidence : "high" or "low"

If you find nothing that fits this form, return []. Do not return prose."""

RULES = """Rules:
  - symbol_a and symbol_b MUST be identifiers that literally appear in the FUNCTION shown below.
    They are looked up by a parser. If the name is not there, your finding is discarded.
  - Do not invent a name, do not name something from another file, do not use a dotted path.
  - Do not assert what a caller passes unless a call site is shown to you.
  - Do not report a finding whose consequence you cannot name concretely. "May be", "could" and
    "likely" mean you do not have the evidence -- return [] instead.
  - Do not report style, naming, or type-annotation tidiness. Only defects."""


def main() -> int:
    with open("corpora/pr_corpus_fresh.json") as fh:
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
    print(f"  {len(jobs)} requests over {len(prs)} pull requests, {MODEL}, SYMBOL anchors")

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
                        {
                            "text": f"Repository: {pr['repo']}\n"
                            f"You are reviewing ONE function that a change touched.\n"
                            f"{SCHEMA}\n\n{RULES}\n"
                        },
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

        kept, rejected = [], []
        for item in found:
            if not isinstance(item, dict):
                continue
            res = resolve(
                str(u["source"]), str(item.get("symbol_a", "")), str(item.get("symbol_b", ""))
            )
            # the derived line is relative to the unit's source; shift to file coordinates
            for k in ("line_a", "line_b"):
                if res[k] is not None:
                    res[k] = int(res[k]) + int(u["lineno"]) - 1
            item.update(res)
            (kept if res["resolved"] else rejected).append(item)

        return {
            "repo": pr["repo"],
            "pr": pr["number"],
            "file": f["path"],
            "unit": u["name"],
            "kept": kept,
            "rejected": rejected,
            "finish": r["finish"],
            "prompt": r["prompt"],
            "thoughts": r["thoughts"],
            "out": r["out"],
        }

    done = nk = nr = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for r in pool.map(run, jobs):
            with open(OUT, "a") as fh:
                fh.write(json.dumps(r) + "\n")
            done += 1
            nk += len(r["kept"])
            nr += len(r["rejected"])
            print(
                f"  [{done:3d}/{len(jobs)}] {str(r['repo']).split('/')[1][:13]:13s} "
                f"#{r['pr']:<6} {str(r['unit'])[:20]:20s} kept={len(r['kept'])} "
                f"rejected={len(r['rejected'])} {r['finish']}"
            )

    total = nk + nr
    print(f"\n  {done} requests, {total} findings emitted")
    print(f"    resolved to a real symbol : {nk}")
    print(
        f"    named a symbol NOT in the shown function : {nr}"
        + (f" = {nr / total:.1%}" if total else "")
    )
    print("  the second number measures the decoupling directly.")
    return 0


try:
    sys.exit(main())
except VertexError as exc:
    print(f"  REFUSING TO REPORT — {exc}")
    sys.exit(1)
