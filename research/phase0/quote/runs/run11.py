"""Design eleven: design nine unchanged beside the evidence arm, on one corpus.

WHAT: Reviews the same pull requests TWICE -- once with design nine's prompt verbatim (arm R, the
      replication) and once with the evidence field required (arm E) -- keeping every RAW finding,
      not only the published ones.
WHY:  The first attempt at this ran a single pass with the evidence field switched on and called
      its output "arm A, a replication of design nine". It was not. An arm carrying a new prompt
      field and a new gate is a new configuration, and a replication claim cannot rest on it.
      `reviewer.review(evidence=False)` is now design nine verbatim, asserted by a test that the
      word never appears in that prompt.

      RAW FINDINGS ARE KEPT. The first attempt discarded everything the gate rejected, which made
      the diagnostic question unanswerable: when G-evidence fires, is the cited evidence ABSENT
      from the diff, or merely unmatched by the string search -- whitespace, a paraphrase, a span
      across a hunk boundary? Those look identical in a joint distribution and mean opposite
      things. One measures the model's grounding, the other measures the gate's strictness.
IMPORTS: stdlib only (collections, json, pathlib, sys). Local: `corpus`, `gate`, `paths`,
      `reviewer`, and the Vertex `client`.
CONSUMED BY: nobody -- it prints and writes quote11_run.json.
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
OUT = pathlib.Path(__file__).resolve().parent.parent / "results" / "quote11_run.json"


def run_arm(client: Client, prs: list[dict], evidence: bool, label: str) -> dict[str, object]:
    """One review pass. Returns raw and published findings, and the per-PR diffs it used."""
    raw: list[dict[str, object]] = []
    published: list[dict[str, object]] = []
    stats: collections.Counter[str] = collections.Counter()
    for i, pr in enumerate(prs, 1):
        repo, num = str(pr["repo"]), int(str(pr["number"]))
        try:
            full = corpus.diff(repo, num)
        except corpus.FetchFailed:
            stats["fetch_failed"] += 1
            continue
        d, _removed, kept = paths.filter_diff(full)
        if kept == 0 or not d.strip():
            stats["nothing_reviewable"] += 1
            continue
        try:
            findings, finish = reviewer.review(client, str(pr["title"]), d, evidence=evidence)
        except reviewer.ReviewFailed:
            stats["review_failed"] += 1
            continue
        stats[f"finish:{finish}"] += 1
        added, sizes = gate.added_lines(d)
        kept_n = 0
        for f in findings:
            v = gate.check(f, d, added, sizes)
            v["repo"], v["pr"] = repo, num
            v["raw_evidence"] = str(f.get("evidence") or "")
            raw.append(v)
            if v["ok"]:
                published.append(v)
                kept_n += 1
        short = repo.split("/")[-1][:12]
        tag = f"{short:12s} #{num:<6d}"
        nraw = len(findings)
        print(f"    {label} {i:2d}/{len(prs)} {tag} raw {nraw:2d} -> {kept_n:2d}")
    return {"raw": raw, "published": published, "stats": dict(stats)}


def main() -> int:
    prs = corpus.pulls(corpus.REPOS_D11, corpus.PER_REPO)
    print(f"  {len(prs)} pull requests from {len(corpus.REPOS_D11)} untouched repositories\n")
    client = Client(MODEL)

    print("  ARM R -- design nine VERBATIM, the replication\n")
    arm_r = run_arm(client, prs, evidence=False, label="R")
    print("\n  ARM E -- the evidence field required\n")
    arm_e = run_arm(client, prs, evidence=True, label="E")

    OUT.write_text(json.dumps({"arm_r": arm_r, "arm_e": arm_e, "n_prs": len(prs)}, indent=1))

    for name, a in (("R design nine", arm_r), ("E + evidence", arm_e)):
        r, p = len(a["raw"]), len(a["published"])  # type: ignore[arg-type]
        rate = 1 - p / r if r else 0.0
        print(
            f"\n  {name:16s} raw {r:3d}  published {p:3d}  gated out {rate:.0%}  "
            f"yield {p / len(prs):.2f}/PR"
        )
        marg = collections.Counter(g for f in a["raw"] for g in f["failed"])  # type: ignore[union-attr]
        print(f"    gates fired: {dict(marg)}")
    print("\n  next: near_miss.py, then adjudicate.py 11")
    return 0


sys.exit(main())
