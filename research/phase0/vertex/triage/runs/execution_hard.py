"""Ask the model for a claim AND the program that would demonstrate it, then run the program.

WHAT: Same reviewer, on the HARD corpus -- 82.1% wrong and 0 correct before. Adds `check_snippet`:
      self-contained Python that prints CONFIRMED if the claimed behaviour occurs and REFUTED if
      it does not. The snippet is executed and the finding is promoted only on CONFIRMED.
WHY:  Three of the measured wrong findings asserted things about Python that Python contradicts in
      one line. The model is not asked whether it is right -- it is asked to write the program that
      would show it, and the interpreter answers.

      THIS VARIANT RUNS ON THE HARD CORPUS and deliberately skips the corpus-age guard. That guard
      exists for questions about what happened NEXT; this is a question about PRECISION, and the
      only corpus that can answer it is the one where the previous designs were measured -- the 20
      recent pull requests where this model scored 82.1% wrong and zero correct of 39.
IMPORTS: stdlib only (json, os, sys, concurrent.futures). Local: `execute`, `units`, `client`.
CONSUMED BY: nobody -- it prints and writes execution_findings.jsonl.
"""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client import Client, VertexError
from execute import run as run_snippet
from units import changed_units

MODEL, BUDGET, WORKERS = "gemini-2.5-pro", 3, 6
OUT = "execution_hard.jsonl"

SCHEMA = """Return ONLY a JSON array. Each element MUST have exactly these fields:
  claim_type    : one of "missing_guard", "wrong_order", "unhandled_case", "resource_leak",
                  "contract_violation"
  file          : the file path, copied exactly
  symbol_a      : the identifier where the defect originates
  symbol_b      : the identifier where the consequence occurs
  relation      : one sentence stating how symbol_a causes the problem at symbol_b
  check_snippet : SELF-CONTAINED Python that demonstrates the claim and prints exactly
                  "CONFIRMED" if the claimed behaviour occurs, or "REFUTED" if it does not

The snippet is executed. Rules for it:
  - standard library only, no file or network access, under ten seconds
  - it must reproduce the MECHANISM you are claiming, not restate the claim in a comment
  - if you cannot write a snippet that would demonstrate the claim, do not report the finding

If you find nothing you can demonstrate this way, return []."""


def main() -> int:
    with open("../corpora/pr_corpus_fresh.json") as fh:
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
    print(f"  {len(jobs)} requests over {len(prs)} pull requests, THE HARD CORPUS")

    client = Client(MODEL)
    open(OUT, "w").close()

    def do(job):
        pr, f, u = job
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": f"Repository: {pr['repo']}\n"
                            f"You are reviewing ONE function that a change touched.\n"
                            f"{SCHEMA}\n"
                        },
                        {"text": f"FILE: {f['path']}\n\nDIFF:\n{str(f['patch'])[:6000]}"},
                        {
                            "text": f"FUNCTION {u['name']} "
                            f"(lines {u['lineno']}-{u['end_lineno']}):\n"
                            f"{str(u['source'])[:24000]}"
                        },
                    ],
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 8192,
                "thinkingConfig": {"thinkingBudget": 4096},
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
        for item in found:
            if isinstance(item, dict):
                item["execution"] = run_snippet(str(item.get("check_snippet", "")))
        return {
            "repo": pr["repo"],
            "pr": pr["number"],
            "file": f["path"],
            "unit": u["name"],
            "findings": [x for x in found if isinstance(x, dict)],
            "finish": r["finish"],
        }

    done = 0
    outcomes: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for r in pool.map(do, jobs):
            with open(OUT, "a") as fh:
                fh.write(json.dumps(r) + "\n")
            done += 1
            for x in r["findings"]:
                o = str(x["execution"]["outcome"])
                outcomes[o] = outcomes.get(o, 0) + 1
            print(
                f"  [{done:3d}/{len(jobs)}] {str(r['repo']).split('/')[1][:16]:16s} "
                f"#{r['pr']:<6} {str(r['unit'])[:20]:20s} "
                f"{len(r['findings'])} findings "
                f"{[x['execution']['outcome'] for x in r['findings']]}"
            )

    total = sum(outcomes.values())
    print(f"\n  {done} requests, {total} findings, each with an executed snippet\n")
    for k in ("CONFIRMED", "REFUTED", "CRASHED", "SILENT", "TIMEOUT", "REFUSED"):
        if outcomes.get(k):
            print(f"    {k:10s} {outcomes[k]:3d}  {outcomes[k] / total:5.1%}")
    print(
        f"\n  the gate publishes only CONFIRMED: "
        f"{outcomes.get('CONFIRMED', 0)}/{total} survive, "
        f"{outcomes.get('CONFIRMED', 0) / len(prs):.2f} per pull request"
    )
    return 0


try:
    sys.exit(main())
except VertexError as exc:
    print(f"  REFUSING TO REPORT — {exc}")
    sys.exit(1)
