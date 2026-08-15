"""Bill the real prompt against Vertex, and compare it to the priced estimate.

WHAT: Builds the product's actual per-request prompt -- a cached repository prefix, the ranked
      function's full source, its file's diff, and the schema the finding must satisfy -- for
      the top-3 funded units of 24 real merged pull requests, sends each to Gemini on Vertex,
      and records the tokens Vertex says it billed.
WHY:  The cost table in `docs/product/QUANTAMIND.md` was computed from token arithmetic and
      never billed. Two things arithmetic cannot see: thinking tokens, which are charged as
      output and which a probe showed running to 204 for a one-word answer, and the real size
      of a funded unit, which is a property of how people actually write Python.
IMPORTS: stdlib only (json, pathlib, statistics, sys, urllib). Local: `units.changed_units`.
CONSUMED BY: nobody -- it prints and writes vertex_cost.json.
"""

from __future__ import annotations

import json
import pathlib
import statistics
import sys
import urllib.error
import urllib.request

from units import changed_units

SP = pathlib.Path(
    "/private/tmp/claude-501/-Users-dhanu-Documents-SaaS-quanta-mind/"
    "6063c1dc-2654-4975-b12a-47677aad0026/scratchpad"
)
PROJECT, LOCATION = "quantamind-oss", "us-central1"
MODEL = "gemini-2.5-pro"
BUDGET = 3

# Vertex list price, USD per 1M tokens, gemini-2.5-pro at <=200k context. Thinking tokens are
# billed at the OUTPUT rate, which is the whole reason this measurement exists.
IN_RATE, OUT_RATE = 1.25, 10.00

SCHEMA_INSTRUCTION = """You are reviewing one function from a pull request.

Return ONLY a JSON array. Each element MUST have exactly these fields:
  claim_type : one of "missing_guard", "wrong_order", "unhandled_case", "resource_leak",
               "contract_violation", "none"
  file       : the file path, copied exactly
  line_a     : integer line number where the defect originates
  line_b     : integer line number where the consequence occurs
  relation   : one sentence stating how line_a causes the problem at line_b
  confidence : "high" or "low"

If you find nothing that fits this form, return []. Do not return prose. Do not return a claim
you cannot anchor to two specific line numbers in the code shown."""


def prefix(repo: str) -> str:
    """The cached-per-repository half. Nothing volatile: a timestamp here is a silent miss."""
    return (
        f"Repository: {repo}\n"
        "Conventions: Python 3, type hints where present are authoritative, tests live under "
        "tests/. Prefer the narrowest claim that the shown code supports.\n"
        "You are given one function that a change touched, and the diff for its file.\n"
        f"{SCHEMA_INSTRUCTION}\n"
    )


def call(token: str, body: dict[str, object]) -> tuple[int, dict[str, object] | str]:
    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT}"
        f"/locations/{LOCATION}/publishers/google/models/{MODEL}:generateContent"
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300].decode("utf-8", "replace")


def main() -> int:
    token = (SP / ".tok").read_text().strip()
    with open("pr_corpus.json") as fh:
        prs = json.load(fh)

    rows: list[dict[str, object]] = []
    unparsed = 0
    for pr in prs:
        funded: list[tuple[dict[str, object], dict[str, object]]] = []
        for f in pr["files"]:
            if not f["source"]:
                continue
            us = changed_units(f["source"], f["patch"])
            if not us and f["source"].strip():
                unparsed += 1
            for u in us:
                funded.append((f, u))
        # rank proxy: most touched lines first, then largest. The ranker needs git history the
        # clones no longer carry; for a COST measurement what matters is that three real units
        # are read, not which three -- stated, because it is an assumption and not a finding.
        funded.sort(key=lambda p: (-int(p[1]["touched"]), -int(p[1]["n_lines"])))
        for f, u in funded[:BUDGET]:
            body = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prefix(pr["repo"])},
                            {"text": f"FILE: {f['path']}\n\nDIFF:\n{f['patch'][:6000]}"},
                            {
                                "text": f"FUNCTION {u['name']} "
                                f"(lines {u['lineno']}-{u['end_lineno']}):\n"
                                f"{str(u['source'])[:24000]}"
                            },
                        ],
                    }
                ],
            }
            status, resp = call(token, body)
            if status != 200:
                print(f"  REFUSING TO REPORT — {pr['repo']}#{pr['number']} {status}: {resp}")
                return 1
            um = resp.get("usageMetadata", {}) if isinstance(resp, dict) else {}
            text = ""
            for c in (resp.get("candidates") or []) if isinstance(resp, dict) else []:
                for part in (c.get("content", {}) or {}).get("parts", []) or []:
                    text += part.get("text", "")
            rows.append(
                {
                    "repo": pr["repo"],
                    "pr": pr["number"],
                    "file": f["path"],
                    "unit": u["name"],
                    "unit_lines": u["n_lines"],
                    "prompt": um.get("promptTokenCount", 0),
                    "out": um.get("candidatesTokenCount", 0),
                    "thoughts": um.get("thoughtsTokenCount", 0),
                    "total": um.get("totalTokenCount", 0),
                    "text": text[:4000],
                }
            )
            print(
                f"  {pr['repo'].split('/')[1][:14]:14s} #{pr['number']:<6} "
                f"{str(u['name'])[:26]:26s} in={um.get('promptTokenCount', 0):6d} "
                f"think={um.get('thoughtsTokenCount', 0):6d} "
                f"out={um.get('candidatesTokenCount', 0):5d}"
            )

    with open("vertex_cost.json", "w") as fh:
        json.dump(rows, fh, indent=1)
    if not rows:
        print("  REFUSING TO REPORT — no requests completed")
        return 1

    n_pr = len({(r["repo"], r["pr"]) for r in rows})
    print(
        f"\n  {len(rows)} requests over {n_pr} pull requests   files that did not parse: {unparsed}"
    )
    for label, key in (("prompt", "prompt"), ("thinking", "thoughts"), ("answer", "out")):
        v = [int(r[key]) for r in rows]
        print(
            f"    {label:9s} mean {statistics.mean(v):8.0f}  median {statistics.median(v):7.0f}"
            f"  max {max(v):7d}"
        )
    per_req = [
        int(r["prompt"]) * IN_RATE / 1e6 + (int(r["thoughts"]) + int(r["out"])) * OUT_RATE / 1e6
        for r in rows
    ]
    by_pr: dict[tuple[str, int], float] = {}
    for r, c in zip(rows, per_req, strict=True):
        by_pr[(str(r["repo"]), int(r["pr"]))] = by_pr.get((str(r["repo"]), int(r["pr"])), 0.0) + c
    costs = sorted(by_pr.values())
    print(f"\n  COST PER PULL REQUEST, {MODEL} list price, {BUDGET} funded units")
    print(f"    mean   ${statistics.mean(costs):.4f}")
    print(f"    median ${statistics.median(costs):.4f}")
    print(f"    p90    ${costs[int(0.9 * (len(costs) - 1))]:.4f}")
    print(f"    max    ${max(costs):.4f}")
    thinking_share = sum(int(r["thoughts"]) for r in rows) / max(
        1, sum(int(r["thoughts"]) + int(r["out"]) for r in rows)
    )
    print(f"    thinking is {thinking_share:.1%} of all billed output tokens")
    return 0


sys.exit(main())
