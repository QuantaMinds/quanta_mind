"""Design ten: three arms over ONE set of findings, so the comparison is exactly paired.

WHAT: Reviews sixty pull requests from six untouched repositories with design nine's configuration
      (arm A), then applies two filters to the SAME findings -- a free lexical marker (arm B) and a
      model-judged decidability gate (arm C) -- and writes all three memberships.
WHY:  B and C are subsets of A, so one adjudication scores all three. That is stronger pairing than
      the pre-registration assumed: the arms share not merely a corpus but every finding, and the
      rater grades findings without ever seeing an arm label.

      ARM A IS ALSO THE REPLICATION OF DESIGN NINE. Same configuration, repositories that did not
      shape it, bar already fixed at under 50% wrong on unique findings.

      THE LEXICAL MARKER WAS FITTED TO DESIGN NINE'S FINDINGS. Its performance there -- 93% of wrong
      caught for one correct lost -- is not an error rate, it is a description of the data it was
      written from. This run is the first time it meets findings it did not shape.
IMPORTS: stdlib only (collections, concurrent.futures, json, pathlib, sys). Local: `corpus`,
      `decidable`, `gate`, `paths`, `reviewer`, and the Vertex `client`.
CONSUMED BY: nobody -- it prints and writes quote10_run.json.
"""

from __future__ import annotations

import collections
import concurrent.futures
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "vertex"))

import decidable
import gate
import paths
import reviewer
from client import Client

import corpus

MODEL = "gemini-2.5-pro"
OUT = pathlib.Path(__file__).resolve().parent / "quote10_run.json"
GATE_WORKERS = 8


def review_all(client: Client, prs: list[dict]) -> tuple[list[dict], collections.Counter]:
    """Arm A: design nine's configuration, unchanged."""
    published: list[dict] = []
    stats: collections.Counter[str] = collections.Counter()
    for i, pr in enumerate(prs, 1):
        repo, num = str(pr["repo"]), int(str(pr["number"]))
        try:
            full = corpus.diff(repo, num)
        except corpus.FetchFailed as exc:
            print(f"    {i:2d}/{len(prs)} {repo}#{num} FETCH FAILED: {str(exc)[:56]}")
            stats["fetch_failed"] += 1
            continue
        d, removed, kept = paths.filter_diff(full)
        for why, c in removed.items():
            stats[f"stripped:{why}"] += c
        if kept == 0 or not d.strip():
            stats["nothing_reviewable"] += 1
            short = repo.split("/")[-1][:13]
            print(f"    {i:2d}/{len(prs)} {short:13s} #{num:<6d} nothing reviewable")
            continue
        try:
            findings, finish = reviewer.review(client, str(pr["title"]), d)
        except reviewer.ReviewFailed as exc:
            print(f"    {i:2d}/{len(prs)} {repo}#{num} REVIEW FAILED: {str(exc)[:56]}")
            stats["review_failed"] += 1
            continue
        stats[f"finish:{finish}"] += 1
        added, sizes = gate.added_lines(d)
        kept_n = 0
        for f in findings:
            v = gate.check(f, d, added, sizes)
            if v["ok"]:
                v["repo"], v["pr"] = repo, num
                published.append(v)
                kept_n += 1
        print(
            f"    {i:2d}/{len(prs)} {repo.split('/')[-1][:13]:13s} #{num:<6d} "
            f"{kept:2d} files  raw {len(findings):2d} -> A {kept_n:2d}  {finish}"
        )
    return published, stats


def apply_model_gate(client: Client, arm_a: list[dict]) -> tuple[set[int], int]:
    """Arm C membership: indices of arm A that the model says are decidable from the diff."""
    keep: set[int] = set()
    errors = 0

    def one(idx: int) -> tuple[int, bool | None, str]:
        f = arm_a[idx]
        try:
            d = corpus.diff(str(f["repo"]), int(str(f["pr"])))
            ok, needs = decidable.judge_one(client, str(f["claim"]), str(f["quote"]), d)
            return idx, ok, needs
        except (decidable.GateFailed, corpus.FetchFailed, OSError):
            return idx, None, ""

    with concurrent.futures.ThreadPoolExecutor(max_workers=GATE_WORKERS) as pool:
        for idx, ok, needs in pool.map(one, range(len(arm_a))):
            if ok is None:
                errors += 1  # counted, never silently kept or dropped
                continue
            arm_a[idx]["decidable"] = ok
            arm_a[idx]["needs"] = needs
            if ok:
                keep.add(idx)
    return keep, errors


def main() -> int:
    prs = corpus.pulls(corpus.REPOS_D10, corpus.PER_REPO_D10)
    print(f"  {len(prs)} pull requests from {len(corpus.REPOS_D10)} untouched repositories\n")
    client = Client(MODEL)

    arm_a, stats = review_all(client, prs)
    if not arm_a:
        print("  REFUSING TO REPORT — arm A produced nothing")
        return 1

    # Arm B: the free lexical marker, fitted on design nine, meeting fresh findings.
    b_drop = {i for i, f in enumerate(arm_a) if decidable.keyword_flag(str(f["claim"]))}
    arm_b = set(range(len(arm_a))) - b_drop

    print(f"\n  arm A: {len(arm_a)} published across {len(prs)} pull requests")
    print(f"  arm B: {len(arm_b)} kept, {len(b_drop)} dropped by the lexical marker")
    print(f"\n  running the model gate over all {len(arm_a)} findings...")
    arm_c, gate_errors = apply_model_gate(client, arm_a)
    print(
        f"  arm C: {len(arm_c)} kept, {len(arm_a) - len(arm_c) - gate_errors} dropped, "
        f"{gate_errors} gate errors"
    )

    agree = len(arm_b & arm_c)
    print(
        f"\n  B and C agree on {agree} of {len(arm_a)} findings "
        f"({agree / len(arm_a):.0%}); B keeps {len(arm_b)}, C keeps {len(arm_c)}"
    )

    OUT.write_text(
        json.dumps(
            {
                "arm_a": arm_a,
                "arm_b": sorted(arm_b),
                "arm_c": sorted(arm_c),
                "gate_errors": gate_errors,
                "stats": dict(stats),
            },
            indent=1,
        )
    )
    print(f"\n  stats: {dict(stats)}")
    print(f"\n  J4 arm B yield {len(arm_b)}/{len(prs)} = {len(arm_b) / len(prs):.2f}  bar >= 0.30")
    print(f"     arm C yield {len(arm_c)}/{len(prs)} = {len(arm_c) / len(prs):.2f}")
    print("  J5 unique-finding counts are computed at adjudication time")
    print("\n  J1, J2, J3 need the blind adjudication of arm A. Run adjudicate.py 10 next --")
    print("  one rating pass scores all three arms, because B and C are subsets of A.")
    return 0


sys.exit(main())
