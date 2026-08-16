"""Score the reviewer against what git did next, not against what a rater thought.

WHAT: For every funded unit on the aged corpus, records whether the model spoke, whether its
      snippets showed confusion, and whether a fix-word commit returned to that file within 90
      days of the merge. Cross-tabulates the model's behaviour against the outcome.
WHY:  Six designs were scored by asking a rater whether a claim was true of the code shown. That
      measures truth and not usefulness. A reviewer pointing at code that later breaks is worth
      something even when its sentences are wrong; a reviewer saying true things about code that
      never breaks is not.

      THE BAR IS THE RANKER, NOT CHANCE. Every unit here was already selected by the allocator,
      which hit 32.5% on the first forty. A model-derived signal that merely matches the ranker is
      a signal worth deleting, because the ranker costs nothing to run.

      No adjudication, no rubric, no rater pool -- the outcome is a commit. That is the point.
IMPORTS: stdlib only (collections, datetime, json, pathlib, subprocess, sys, math).
CONSUMED BY: nobody -- it prints and writes future_fix_scored.json.
"""

from __future__ import annotations

import collections
import datetime
import json
import pathlib
import subprocess
import sys
from math import comb

SP = pathlib.Path(
    "/private/tmp/claude-501/-Users-dhanu-Documents-SaaS-quanta-mind/"
    "6063c1dc-2654-4975-b12a-47677aad0026/scratchpad/aged"
)
RUNS = pathlib.Path(__file__).parent.parent / "vertex" / "triage" / "runs"
WINDOW = 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MIN_SIGNAL = 20  # pre-registered: fewer carrying the signal is UNDERPOWERED


class ReadFailed(RuntimeError):
    """A git read that did not exit zero. Never silently an empty history."""


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


def fisher(a: int, b: int, c: int, d: int) -> float:
    def p(a: int, b: int, c: int, d: int) -> float:
        return comb(a + b, a) * comb(c + d, c) / comb(a + b + c + d, a + c)

    obs, tot = p(a, b, c, d), 0.0
    for i in range(0, min(a + b, a + c) + 1):
        j, k = (a + b) - i, (a + c) - i
        ll = (c + d) - k
        if j < 0 or k < 0 or ll < 0:
            continue
        pr = p(i, j, k, ll)
        if pr <= obs + 1e-12:
            tot += pr
    return tot


def main() -> int:
    rows = [
        json.loads(x)
        for x in (RUNS / "future_fix_findings.jsonl").read_text().splitlines()
        if x.strip()
    ]
    prs = {
        (p["repo"], p["number"]): p for p in json.loads((RUNS / "corpus_aged_big.json").read_text())
    }

    hist: dict[str, list] = {}
    recs: list[dict[str, object]] = []
    skipped: collections.Counter[str] = collections.Counter()

    for r in rows:
        repo = str(r["repo"])
        if repo not in hist:
            c = SP / repo.replace("/", "_")
            hist[repo] = []
            if c.is_dir():
                try:
                    hist[repo] = history(c)
                except ReadFailed as exc:
                    print(f"  REFUSING TO REPORT — {exc}")
                    return 1
        h = hist[repo]
        if not h:
            skipped["no clone"] += 1
            continue
        pr = prs.get((repo, r["pr"]))
        if pr is None:
            skipped["pr missing"] += 1
            continue
        try:
            cut = int(
                datetime.datetime.fromisoformat(
                    str(pr["merged_at"]).replace("Z", "+00:00")
                ).timestamp()
            )
        except ValueError:
            skipped["bad merge date"] += 1
            continue
        f = str(r["file"])
        before = [ts for ts, _m, fs in h if f in fs and ts <= cut]
        if not before:
            skipped["file absent before merge"] += 1
            continue
        when = max(before)
        returned = any(
            ts > when and ts - when <= WINDOW and f in fs and any(w in m for w in FIXWORDS)
            for ts, m, fs in h
        )
        outs = [str(x["execution"]["outcome"]) for x in r["findings"]]
        recs.append(
            {
                "spoke": bool(r["findings"]),
                "n_findings": len(r["findings"]),
                "confused": any(o in ("CRASHED", "REFUTED", "SILENT") for o in outs),
                "confirmed": any(o == "CONFIRMED" for o in outs),
                "returned": returned,
            }
        )

    if not recs:
        print(f"  REFUSING TO REPORT — nothing scoreable. skips: {dict(skipped)}")
        return 1
    with open("future_fix_scored.json", "w") as fh:
        json.dump(recs, fh)

    base = sum(1 for r in recs if r["returned"]) / len(recs)
    print(f"  {len(recs)} funded units scored against git. skips: {dict(skipped)}")
    print(f"\n  THE RANKER'S OWN HIT RATE ON THESE UNITS: {base:.1%}")
    print("  every model signal below must beat THAT, not chance.\n")
    print(f"  {'signal':30s} {'units':>6} {'fix returned':>13} {'vs ranker':>10} {'p':>8}")

    def row(name: str, pred) -> None:
        yes = [r for r in recs if pred(r)]
        no = [r for r in recs if not pred(r)]
        if not yes or not no:
            return
        ry = sum(1 for r in yes if r["returned"]) / len(yes)
        a = sum(1 for r in yes if r["returned"])
        b = len(yes) - a
        c = sum(1 for r in no if r["returned"])
        d = len(no) - c
        flag = "" if len(yes) >= MIN_SIGNAL else "  UNDERPOWERED"
        print(
            f"  {name:30s} {len(yes):6d} {ry:12.1%} {(ry - base) * 100:+9.1f} "
            f"{fisher(a, b, c, d):8.3f}{flag}"
        )

    row("the model spoke", lambda r: r["spoke"])
    row("emitted >= 2 findings", lambda r: int(r["n_findings"]) >= 2)
    row("a snippet showed confusion", lambda r: r["confused"])
    row("a snippet CONFIRMED", lambda r: r["confirmed"])
    row("spoke AND was confused", lambda r: r["spoke"] and r["confused"])
    print(
        f"\n  pre-registered: CONFIRMED needs >=45% and p<0.05; NULL is within 5 points "
        f"of {base:.1%} or p>=0.05"
    )
    return 0


sys.exit(main())
