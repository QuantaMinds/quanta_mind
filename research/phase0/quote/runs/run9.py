"""Design nine: the same reviewer, shown only files it can reason about.

WHAT: Reviews ninety merged pull requests from six untouched repositories, with lockfiles,
      dependency manifests and documentation stripped from each diff BEFORE the model is called,
      then runs every finding through the same model-free gate as design eight.
WHY:  Design eight failed at 60.8% wrong, and 18 of its 18 lockfile findings were WRONG -- the
      model claiming versions absent from PyPI and 2026 timestamps as future dates, neither of
      which it can decide from a diff. Every CORRECT finding it produced came from source code or
      a CI workflow.

      ONE THING CHANGES. Same prompt, same gate, same rubric, same sabotage controls. If the
      wrong-rate moves, the filter is why.
      → `docs/plans/preregistrations/reviewer/path-filter-preregistration.md`
IMPORTS: stdlib only (collections, json, pathlib, sys). Local: `corpus`, `gate`, `paths`,
      `reviewer`, and the Vertex `client`.
CONSUMED BY: nobody -- it prints and writes quote9_run.json.
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "vertex"))

import gate
import paths
import reviewer
from client import Client

import corpus

MODEL = "gemini-2.5-pro"
OUT = pathlib.Path(__file__).resolve().parent.parent / "results" / "quote9_run.json"
YIELD_BAR = 0.30  # H4, lowered from design eight's 0.50 and argued for in the pre-registration
MIN_FINDINGS = 25  # H5: below this the run is UNDERPOWERED, not a pass or a fail


def main() -> int:
    prs = corpus.pulls(corpus.REPOS_D9, corpus.PER_REPO_D9)
    print(f"  {len(prs)} merged pull requests from {len(corpus.REPOS_D9)} untouched repositories\n")
    client = Client(MODEL)

    raw: list[dict[str, object]] = []
    published: list[dict[str, object]] = []
    finishes: collections.Counter[str] = collections.Counter()
    stripped: collections.Counter[str] = collections.Counter()
    empty_after_filter = 0

    for i, pr in enumerate(prs, 1):
        repo, num = str(pr["repo"]), int(str(pr["number"]))
        try:
            full = corpus.diff(repo, num)
        except corpus.FetchFailed as exc:
            print(f"    {i:2d}/{len(prs)} {repo}#{num} FETCH FAILED: {str(exc)[:60]}")
            finishes["FETCH_FAILED"] += 1
            continue
        d, removed, kept = paths.filter_diff(full)
        for why, c in removed.items():
            stripped[why] += c
        if kept == 0 or not d.strip():
            empty_after_filter += 1
            tag = f"{repo.split('/')[-1][:14]:14s} #{num:<7d}"
            print(f"    {i:2d}/{len(prs)} {tag} nothing reviewable")
            continue
        try:
            findings, finish = reviewer.review(client, str(pr["title"]), d)
        except reviewer.ReviewFailed as exc:
            print(f"    {i:2d}/{len(prs)} {repo}#{num} REVIEW FAILED: {str(exc)[:60]}")
            finishes["REVIEW_FAILED"] += 1
            continue
        finishes[finish] += 1
        added, sizes = gate.added_lines(d)
        kept_n = 0
        for f in findings:
            v = gate.check(f, d, added, sizes)
            v["repo"], v["pr"] = repo, num
            raw.append(v)
            if v["ok"]:
                published.append(v)
                kept_n += 1
        print(
            f"    {i:2d}/{len(prs)} {repo.split('/')[-1][:14]:14s} #{num:<7d} "
            f"{kept:2d} files  raw {len(findings):2d} -> pub {kept_n:2d}  {finish}"
        )

    if not raw:
        print("  REFUSING TO REPORT — no findings produced at all")
        return 1
    OUT.write_text(json.dumps({"raw": raw, "published": published}, indent=1))

    n = len(raw)
    print(f"\n  finish reasons: {dict(finishes)}")
    print(f"  files stripped before review: {dict(stripped)}")
    print(f"  pull requests with nothing reviewable after filtering: {empty_after_filter}")
    print(f"  {n} raw findings, {len(published)} published, {len(prs)} pull requests\n")

    qf = sum(1 for r in raw if "G-quote" in r["failed"]) / n  # type: ignore[operator]
    print(f"  raw quote-failure {qf:.1%}  (design eight: 8.1%)")

    marg: collections.Counter[str] = collections.Counter()
    joint: collections.Counter[str] = collections.Counter()
    for r in raw:
        f = sorted(r["failed"])  # type: ignore[arg-type]
        for g in f:
            marg[g] += 1
        joint["+".join(f) if f else "(passed all)"] += 1
    print("\n  gate marginals")
    for g, c in marg.most_common():
        print(f"      {g:10s} {c:4d}  {c / n:6.1%}")
    print("  joint")
    for combo, c in joint.most_common(8):
        print(f"      {combo[:50]:50s} {c:4d}  {c / n:6.1%}")

    y = len(published) / len(prs)
    print(
        f"\n  H4  yield {len(published)}/{len(prs)} = {y:.2f} per pull request  bar >= {YIELD_BAR}"
    )
    print(f"      [{'PASS' if y >= YIELD_BAR else 'FAIL'}]")
    ok5 = len(published) >= MIN_FINDINGS
    print(f"\n  H5  {len(published)} published findings  bar >= {MIN_FINDINGS}")
    print(f"      [{'PASS' if ok5 else 'UNDERPOWERED'}]")

    print("\n  H1 (wrong-rate < 50%), H2 (UNFALSIFIABLE < 25%) and H3 (sabotage catch) need blind")
    print("  adjudication. Run adjudicate.py against quote9_run.json next.")
    return 0


sys.exit(main())
