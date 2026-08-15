"""Bill the product's real prompt against Vertex, one line per request, written as it completes.

WHAT: Builds the per-request prompt the architecture specifies -- the repository prefix, the
      funded function's full source, its file's diff, and the schema a finding must satisfy --
      for the top-3 funded units of 24 real merged pull requests, and records what Vertex says
      it billed for each.
WHY:  The cost table was computed from token arithmetic and never billed, and its shallow-read
      token sizes were assumed. Arithmetic also cannot see thinking tokens, which bill at the
      output rate and which the first run showed running to 13,000 against a 150-token answer.

      THE UNIT OF RECORD IS THE REQUEST, not the pull request. Aggregating three calls into one
      line is the defect that priced one call for three and inverted the sign of this table's
      cost argument once already. Rows are appended to JSONL as they land, so a failure at
      request 66 costs 6 requests rather than all 72.
IMPORTS: stdlib only (concurrent.futures, json, sys). Local: `client.Client`, `units.changed_units`.
CONSUMED BY: `report.py` in this package.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor

from client import Client, VertexError
from units import changed_units

MODEL = "gemini-2.5-pro"
BUDGET = 3
WORKERS = 6
OUT = "vertex_cost.jsonl"

# Thinking is billed at the output rate and the first run showed it consuming the whole budget,
# truncating answers to one token. A ceiling is set so the answer always has room; the ceiling
# is a measurement decision and it is recorded with the result.
MAX_OUTPUT_TOKENS = 8192
THINKING_BUDGET = 4096

SCHEMA_INSTRUCTION = """You are reviewing one function from a pull request.

Return ONLY a JSON array. Each element MUST have exactly these fields:
  claim_type : one of "missing_guard", "wrong_order", "unhandled_case", "resource_leak",
               "contract_violation"
  file       : the file path, copied exactly
  line_a     : integer line number where the defect originates
  line_b     : integer line number where the consequence occurs
  relation   : one sentence stating how line_a causes the problem at line_b
  confidence : "high" or "low"

If you find nothing that fits this form, return []. Do not return prose. Do not return a claim
you cannot anchor to two specific line numbers in the code shown."""


def prefix(repo: str) -> str:
    """The per-repository half. Nothing volatile here: a timestamp is a silent cache miss."""
    return (
        f"Repository: {repo}\n"
        "Conventions: Python 3, type hints where present are authoritative, tests live under "
        "tests/. Prefer the narrowest claim the shown code supports.\n"
        f"{SCHEMA_INSTRUCTION}\n"
    )


def build(pr: dict[str, object], f: dict[str, object], u: dict[str, object]) -> dict[str, object]:
    return {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prefix(str(pr["repo"]))},
                    {"text": f"FILE: {f['path']}\n\nDIFF:\n{str(f['patch'])[:6000]}"},
                    {
                        "text": f"FUNCTION {u['name']} (lines {u['lineno']}-{u['end_lineno']}):\n"
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


def funded_units(pr: dict[str, object]) -> list[tuple[dict[str, object], dict[str, object]]]:
    """The BUDGET units this pull request would fund.

    Ranked by touched-line count because the git clones the real ranker needs are gone. Sound
    for a COST figure -- what matters is that three real units are read, not which three -- and
    NOT sound for any accuracy figure. Stated here rather than left for a reader to infer.
    """
    out: list[tuple[dict[str, object], dict[str, object]]] = []
    for f in pr["files"]:  # type: ignore[attr-defined]
        if not f["source"]:
            continue
        for u in changed_units(str(f["source"]), str(f["patch"])):
            out.append((f, u))
    out.sort(key=lambda p: (-int(p[1]["touched"]), -int(p[1]["n_lines"])))
    return out[:BUDGET]


def main() -> int:
    with open("corpora/pr_corpus.json") as fh:
        prs = json.load(fh)

    jobs: list[tuple[dict[str, object], dict[str, object], dict[str, object]]] = []
    for pr in prs:
        for f, u in funded_units(pr):
            jobs.append((pr, f, u))
    print(f"  {len(jobs)} requests over {len(prs)} pull requests, {MODEL}, {WORKERS} concurrent")

    client = Client(MODEL)
    open(OUT, "w").close()

    def run(job: tuple[dict[str, object], dict[str, object], dict[str, object]]):
        pr, f, u = job
        r = client.generate(build(pr, f, u))
        r.update(
            {
                "repo": pr["repo"],
                "pr": pr["number"],
                "file": f["path"],
                "unit": u["name"],
                "unit_lines": u["n_lines"],
            }
        )
        return r

    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for r in pool.map(run, jobs):
            with open(OUT, "a") as fh:  # append as it lands: a late failure costs 6, not 72
                fh.write(json.dumps(r) + "\n")
            done += 1
            print(
                f"  [{done:3d}/{len(jobs)}] {str(r['repo']).split('/')[1][:13]:13s} "
                f"#{r['pr']:<7} {str(r['unit'])[:22]:22s} in={r['prompt']:6d} "
                f"think={r['thoughts']:6d} out={r['out']:5d} {r['finish']}"
            )
    print(f"\n  {done} requests written to {OUT}")
    return 0


try:
    sys.exit(main())
except VertexError as exc:
    print(f"  REFUSING TO REPORT — {exc}")
    print(f"  rows completed before the failure are in {OUT} and are still valid")
    sys.exit(1)
