"""Run design eight on the fresh corpus and report every pre-registered bar.

WHAT: Reviews sixty merged pull requests from six untouched repositories, runs each finding through
      the model-free gate, and prints the raw quote-failure rate, the joint gate distribution, the
      yield, and the hunk-size stratification.
WHY:  Bars are fixed in the quote-anchor pre-registration under `docs/plans/preregistrations/`
      and are not restated here as
      thresholds to be nudged. G2 -- the wrong-rate of published findings -- needs blind
      adjudication and is NOT computed here; this run produces the findings that get adjudicated.

      THE JOINT DISTRIBUTION IS THE POINT OF G4. Five marginals would hide that one gate rejects
      everything the others would have caught, which would make four of them decorative.
IMPORTS: stdlib only (collections, json, pathlib, statistics, sys). Local: `corpus`, `gate`,
      `reviewer`, and the Vertex `client`.
CONSUMED BY: nobody -- it prints and writes quote_run.json.
"""

from __future__ import annotations

import collections
import json
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "vertex"))

import gate
import reviewer
from client import Client

import corpus

MODEL = "gemini-2.5-pro"
OUT = pathlib.Path(__file__).resolve().parent / "quote_run.json"
BASELINE_ANCHOR_FAILURE = 0.873  # the measured line-citing defect rate this must beat (bar G1)


def main() -> int:
    prs = corpus.pulls()
    print(f"  {len(prs)} merged pull requests from {len(corpus.REPOS)} untouched repositories\n")
    client = Client(MODEL)

    raw: list[dict[str, object]] = []
    published: list[dict[str, object]] = []
    finishes: collections.Counter[str] = collections.Counter()
    per_repo_hunks: dict[str, list[int]] = collections.defaultdict(list)

    for i, pr in enumerate(prs, 1):
        repo, num = str(pr["repo"]), int(pr["number"])  # type: ignore[arg-type]
        try:
            d = corpus.diff(repo, num)
            findings, finish = reviewer.review(client, str(pr["title"]), d)
        except (corpus.FetchFailed, reviewer.ReviewFailed) as exc:
            print(f"    {i:2d}/{len(prs)} {repo}#{num} FAILED: {str(exc)[:70]}")
            finishes["FAILED"] += 1
            continue
        finishes[finish] += 1
        added, sizes = gate.added_lines(d)
        per_repo_hunks[repo] += list(sizes.values())
        kept = 0
        for f in findings:
            v = gate.check(f, d, added, sizes)
            v["repo"], v["pr"] = repo, num
            raw.append(v)
            if v["ok"]:
                published.append(v)
                kept += 1
        print(
            f"    {i:2d}/{len(prs)} {repo.split('/')[-1][:18]:18s} #{num:<6d} "
            f"raw {len(findings):2d} -> published {kept:2d}  {finish}"
        )

    if not raw:
        print("  REFUSING TO REPORT — no findings produced at all")
        return 1
    OUT.write_text(json.dumps({"raw": raw, "published": published}, indent=1))

    n = len(raw)
    print(f"\n  finish reasons: {dict(finishes)}")
    print(f"  {n} raw findings, {len(published)} published, {len(prs)} pull requests\n")

    # ---- G1: the raw quote-failure rate, against the baseline it replaces ----
    qf = sum(1 for r in raw if "G-quote" in r["failed"]) / n  # type: ignore[operator]
    b = BASELINE_ANCHOR_FAILURE
    print(f"  G1  raw quote-failure {qf:.1%}  (line-citing baseline {b:.1%})")
    print(f"      [{'PASS' if qf < BASELINE_ANCHOR_FAILURE else 'FAIL'}]\n")

    # ---- G4: marginals AND the joint distribution ----
    marg: collections.Counter[str] = collections.Counter()
    joint: collections.Counter[str] = collections.Counter()
    for r in raw:
        f = sorted(r["failed"])  # type: ignore[arg-type]
        for g in f:
            marg[g] += 1
        joint["+".join(f) if f else "(passed all)"] += 1
    print("  G4  gate marginals — every gate evaluated on every finding")
    for g, c in marg.most_common():
        print(f"      {g:10s} {c:4d}  {c / n:6.1%}")
    print("\n      joint distribution — which gates fire TOGETHER")
    for combo, c in joint.most_common(10):
        print(f"      {combo[:52]:52s} {c:4d}  {c / n:6.1%}")
    fired = sum(1 for g in ("G-quote", "G-fix", "G-outer", "G-nit") if marg[g] > 0)
    print(f"      [{'PASS' if fired >= 1 else 'FAIL'}] {fired} of 4 gates fired\n")

    # ---- G3: yield ----
    y = len(published) / len(prs)
    print(f"  G3  yield {len(published)}/{len(prs)} = {y:.2f} published per pull request")
    print(f"      [{'PASS' if y >= 0.5 else 'FAIL'}] bar is >= 0.50\n")

    # ---- the pre-registered stratification, so a favourable result is not composition ----
    print("  HUNK SIZE — the pre-registered confound. Proxy for enclosing function length.")
    print(f"      {'repository':22s} {'median hunk':>12} {'published':>10}")
    for repo in corpus.REPOS:
        hs = per_repo_hunks.get(repo, [])
        pub = sum(1 for p in published if p["repo"] == repo)
        med = statistics.median(hs) if hs else 0
        print(f"      {repo:22s} {med:12.0f} {pub:10d}")
    bands = [(0, 5, "<=5"), (6, 15, "6-15"), (16, 40, "16-40"), (41, 10**6, ">40")]
    print(f"\n      {'hunk size':>10} {'published':>10}   (wrong-rate added after adjudication)")
    for lo, hi, lab in bands:
        c = sum(1 for p in published if lo <= int(str(p["hunk_size"])) <= hi)
        print(f"      {lab:>10} {c:10d}")

    print("\n  G2 (published wrong-rate < 50%) and the UNFALSIFIABLE discriminator require blind")
    print("  adjudication and are NOT computed here. This run produced the findings to adjudicate.")
    return 0


sys.exit(main())
