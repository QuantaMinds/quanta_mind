"""The model judges one analyzer alarm at a time, on the 20 unseen pull requests.

WHAT: For each of the same 20 pull requests, ranks the changed units, runs `ruff` over their files,
      keeps the alarms falling inside the top-3 funded units, and asks the model to PROMOTE or KILL
      each one with the enclosing function in front of it.
WHY:  As a finder this model is 7.2% correct across 195 blind-adjudicated findings; as a judge it
      reached kappa 0.82 on the same code. The literature's working systems all use it in the
      second role. This tests whether that inversion survives contact with our corpus.

      THE MODEL NEVER PROPOSES ANYTHING HERE. It cannot invent a location, a symbol or a defect --
      the analyzer supplies all three and the model only decides whether the alarm is worth a
      reviewer's attention. That is the whole point of the redesign.
IMPORTS: stdlib only (json, sys, concurrent.futures). Local: `alarms`, `client`, `units`.
CONSUMED BY: nobody -- it prints and writes triage_results.jsonl.
"""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alarms import AnalyzerFailed, in_units, raise_alarms
from client import Client, VertexError
from units import changed_units

MODEL, BUDGET, WORKERS = "gemini-2.5-pro", 3, 6
OUT = "triage_results.jsonl"

PROMPT = """A static analyzer raised this alarm on a pull request under review. Decide whether it
is worth reporting to the developer.

Return ONLY a JSON object with exactly these fields:
  verdict   : "PROMOTE" if this is a real defect a reviewer should act on, "KILL" otherwise
  reason    : one sentence. If PROMOTE, state the concrete consequence. If KILL, state why it is
              not a defect here -- intentional, unreachable, guarded elsewhere, or merely stylistic.

KILL is the default. Promote only when you can name what breaks."""


def main() -> int:
    with open("../corpora/pr_corpus_fresh.json") as fh:
        prs = json.load(fh)

    jobs, no_alarm_units, scanned = [], 0, 0
    for pr in prs:
        for f in pr["files"]:
            if not f["source"]:
                continue
            us = changed_units(str(f["source"]), str(f["patch"]))
            us.sort(key=lambda u: (-int(u["touched"]), -int(u["n_lines"])))
            funded = us[:BUDGET]
            if not funded:
                continue
            scanned += len(funded)
            try:
                found = raise_alarms(str(f["path"]), str(f["source"]))
            except AnalyzerFailed as exc:
                print(f"  REFUSING TO REPORT — {exc}")
                return 1
            hits = in_units(found, funded)
            if not hits:
                no_alarm_units += len(funded)
            for a in hits:
                jobs.append((pr, f, a))

    print(f"  {scanned} funded units scanned across {len(prs)} pull requests")
    print(f"  {len(jobs)} alarms raised inside them; {no_alarm_units} funded units had none")
    if not jobs:
        print("  REFUSING TO REPORT — the analyzer found nothing in any funded unit.")
        print("  That is a finding about the RANKER, not a failed run: the units a later fix")
        print("  returns to are not the units that fail lint. Report it as such.")
        return 1

    client = Client(MODEL)
    open(OUT, "w").close()

    def run(job):
        pr, f, a = job
        lines = str(f["source"]).split("\n")
        lo, hi = int(a["unit_lineno"]), int(a["unit_end"])
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": PROMPT},
                        {
                            "text": f"Repository: {pr['repo']}\nFile: {f['path']}\n"
                            f"ALARM {a['code']} at line {a['line']}: {a['message']}"
                        },
                        {
                            "text": "THE FUNCTION IT WAS RAISED IN:\n"
                            + "\n".join(
                                f"{i:6d} | {lines[i - 1]}"
                                for i in range(lo, min(hi, len(lines)) + 1)
                            )[:20000]
                        },
                    ],
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 2048,
                "thinkingConfig": {"thinkingBudget": 2048},
            },
        }
        r = client.generate(body)
        t = r["text"].strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        try:
            d = json.loads(t.strip())
        except json.JSONDecodeError:
            d = {}
        return {
            "repo": pr["repo"],
            "pr": pr["number"],
            "file": f["path"],
            "alarm": a,
            "verdict": str(d.get("verdict", "")).upper(),
            "reason": d.get("reason", ""),
            "prompt": r["prompt"],
            "thoughts": r["thoughts"],
            "out": r["out"],
        }

    done = promoted = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for r in pool.map(run, jobs):
            with open(OUT, "a") as fh:
                fh.write(json.dumps(r) + "\n")
            done += 1
            promoted += int(r["verdict"] == "PROMOTE")
            print(
                f"  [{done:3d}/{len(jobs)}] {str(r['repo']).split('/')[1][:13]:13s} "
                f"#{r['pr']:<6} {r['alarm']['code']!s:6s} {r['verdict']:8s} "
                f"{str(r['reason'])[:60]}"
            )

    killed = done - promoted
    print(f"\n  {done} alarms triaged")
    print(f"    PROMOTED {promoted}  ({promoted / done:.1%})")
    print(f"    KILLED   {killed}  ({killed / done:.1%})")
    print("    the literature reports kill rates of 79-98%")
    print(f"    promoted per pull request: {promoted / len(prs):.2f}")
    print("\n  A HIGH KILL RATE IS NOT SUCCESS. What decides is the wrong-rate among the")
    print("  promoted alarms, which needs blind adjudication.")
    return 0


try:
    sys.exit(main())
except VertexError as exc:
    print(f"  REFUSING TO REPORT — {exc}")
    sys.exit(1)
