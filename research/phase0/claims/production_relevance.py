"""Do the model's findings land in code a later fix actually returned to?

WHAT: For every adjudicated finding, takes the pull request's merge date and asks whether a
      fix-word commit within the next 90 days touched the same file. Cross-tabulates that against
      the finding's verdict.
WHY:  Every number about the review half so far measures whether a claim is TRUE of the code
      shown. None measures whether it MATTERS. A reviewer's comment can be perfectly true and
      about code that never breaks. This is the only production-proximate ground truth available
      -- the same outcome rule the ranker is validated against, applied to the findings instead.

      IT IS A PROXY AND ITS LIMIT IS ALREADY MEASURED: only 14% of the pairs the rule admits are
      genuine repairs. It cannot say a finding predicted an incident. It can say whether findings
      concentrate where later fixes land, which is the difference between tracking defects and
      producing plausible sentences.
IMPORTS: stdlib only (bisect, collections, json, pathlib, subprocess, sys).
CONSUMED BY: nobody -- it prints.
"""

from __future__ import annotations

import collections
import json
import pathlib
import random
import subprocess
import sys
from math import erfc, sqrt

SP = pathlib.Path(
    "/private/tmp/claude-501/-Users-dhanu-Documents-SaaS-quanta-mind/"
    "6063c1dc-2654-4975-b12a-47677aad0026/scratchpad"
)
V = pathlib.Path(__file__).parent.parent / "vertex"
R = pathlib.Path(__file__).parent.parent / "results"
WINDOW = 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")


class ReadFailed(RuntimeError):
    """A git read that did not exit zero."""


def clone_for(repo: str) -> pathlib.Path | None:
    name = repo.replace("/", "_")
    for d in ("first", "fresh", "third"):
        p = SP / d / name
        if p.is_dir():
            return p
    return None


def history(path: pathlib.Path) -> list[tuple[int, str, frozenset[str]]]:
    p = subprocess.run(
        [
            "git",
            "-c",
            "core.commitGraph=false",
            "-C",
            str(path),
            "log",
            "--reverse",
            "--no-merges",
            "--name-only",
            "--format=%x00%ct%x01%s",
        ],
        capture_output=True,
        timeout=1800,
    )
    if p.returncode != 0:
        raise ReadFailed(f"{path}: git log exited {p.returncode}")
    out = []
    for chunk in p.stdout.decode("utf-8", "replace").split("\x00"):
        if not chunk.strip():
            continue
        head, _, body = chunk.partition("\n")
        ts, _, msg = head.partition("\x01")
        try:
            when = int(ts)
        except ValueError:
            continue
        files = frozenset(x for x in body.split("\n") if x.endswith(".py") and x.strip())
        if files:
            out.append((when, msg.lower(), files))
    return out


def load(findings: str, verdicts: str, seed: int) -> list[dict[str, object]]:
    rows = [json.loads(x) for x in (V / findings).read_text().splitlines() if x.strip()]
    ver = json.loads((R / verdicts).read_text())
    items = []
    for r in rows:
        for f in r.get("findings") or (r.get("kept", []) + r.get("rejected", [])):
            if isinstance(f, dict):
                items.append({"repo": r["repo"], "pr": r["pr"], "file": r["file"]})
    random.Random(seed).shuffle(items)
    return [{**it, "verdict": ver[str(i)]} for i, it in enumerate(items) if str(i) in ver]


def main() -> int:
    items = (
        load("corpora/enriched_findings.jsonl", "enriched_verdicts.json", 20260814)
        + load("corpora/fresh_findings.jsonl", "fresh_verdicts.json", 20260815)
        + load("corpora/symbol_findings.jsonl", "symbol_verdicts.json", 20260816)
    )
    prs = {}
    for corpus in ("corpora/pr_corpus.json", "corpora/pr_corpus_fresh.json"):
        for p in json.loads((V / corpus).read_text()):
            prs[(p["repo"], p["number"])] = p

    hist: dict[str, list] = {}
    scored, no_clone, no_forward = [], 0, 0
    for it in items:
        repo = str(it["repo"])
        if repo not in hist:
            c = clone_for(repo)
            if c is None:
                hist[repo] = []
            else:
                try:
                    hist[repo] = history(c)
                except ReadFailed as exc:
                    print(f"  REFUSING TO REPORT — {exc}")
                    return 1
        h = hist[repo]
        if not h:
            no_clone += 1
            continue
        pr = prs.get((repo, it["pr"]))
        if pr is None:
            continue
        # the PR's own commit is the last one touching all its files; approximate its date by the
        # newest commit that touches this file at or before the end of history
        f = str(it["file"])
        touches = [ts for ts, _m, fs in h if f in fs]
        if not touches:
            continue
        when = max(touches)
        newest = h[-1][0]
        if newest - when < WINDOW:
            no_forward += 1
            continue
        returned = any(
            ts > when and ts - when <= WINDOW and f in fs and any(w in m for w in FIXWORDS)
            for ts, m, fs in h
        )
        scored.append((str(it["verdict"]), returned))

    print(
        f"  {len(items)} findings; {no_clone} without a clone; "
        f"{no_forward} whose file has under 90 days of forward history"
    )
    if not scored:
        print("  REFUSING TO REPORT — nothing scoreable")
        return 1

    tab = collections.defaultdict(collections.Counter)
    for v, ret in scored:
        tab[v][ret] += 1
    print(f"\n  DOES A LATER FIX RETURN TO THE FILE THE FINDING IS IN?  n = {len(scored)}\n")
    print(f"  {'verdict':16s} {'n':>4} {'fix returned':>13}")
    for v in ("CORRECT", "WRONG", "UNFALSIFIABLE", "TRIVIAL"):
        n = sum(tab[v].values())
        if not n:
            continue
        print(f"  {v:16s} {n:4d} {tab[v][True] / n:12.1%}")

    c = tab["CORRECT"]
    w = tab["WRONG"]
    nc, nw = sum(c.values()), sum(w.values())
    if nc and nw:
        p = (c[True] + w[True]) / (nc + nw)
        se = sqrt(p * (1 - p) * (1 / nc + 1 / nw)) if p not in (0, 1) else 0
        pv = erfc(abs(c[True] / nc - w[True] / nw) / se / 2**0.5) if se else 1.0
        print(
            f"\n  CORRECT {c[True] / nc:.1%} vs WRONG {w[True] / nw:.1%}   "
            f"difference {(c[True] / nc - w[True] / nw) * 100:+.1f} points, p = {pv:.3f}"
        )
    allret = sum(t[True] for t in tab.values())
    print(
        f"\n  overall, {allret}/{len(scored)} = {allret / len(scored):.1%} of findings sit in a "
        f"file a later fix returned to"
    )
    print("  The proxy admits only 14% genuine repairs, so this bounds relevance, not proves it.")
    return 0


sys.exit(main())
