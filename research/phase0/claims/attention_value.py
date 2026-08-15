"""Is the model's decision to SPEAK informative, even when what it says is wrong?

WHAT: For every unit the allocator funded on the aged corpus, records whether the model emitted a
      finding or stayed silent, and whether a later fix returned to that file within 90 days. Then
      cross-tabulates the two.
WHY:  Every measurement so far scores the CLAIM. None scores the LOCATION. A reviewer whose claims
      are 65% wrong could still be pointing at the right code -- and if the units it chooses to
      speak about are the ones a later fix returns to, that is a signal worth shipping even with
      the prose discarded.

      THIS IS THE ONE QUESTION THE ADJUDICATIONS CANNOT ANSWER. A rater judges whether a sentence
      is true of the code in front of them; they cannot see whether that code later broke. The
      aged corpus can, because every pull request in it predates the outcome window by more than a
      decade.

      THE NULL IS THE INTERESTING CASE. If speaking and staying silent land on later-fixed files at
      the same rate, the model's attention carries nothing beyond the ranker's, and the ranker is
      already measured. Say so plainly rather than reaching for a subgroup.
IMPORTS: stdlib only (collections, json, pathlib, subprocess, sys, math).
CONSUMED BY: nobody -- it prints.
"""

from __future__ import annotations

import collections
import json
import pathlib
import subprocess
import sys
from math import comb

SP = pathlib.Path(
    "/private/tmp/claude-501/-Users-dhanu-Documents-SaaS-quanta-mind/"
    "6063c1dc-2654-4975-b12a-47677aad0026/scratchpad/aged"
)
V = pathlib.Path(__file__).parent.parent / "vertex" / "triage"
WINDOW = 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")


class ReadFailed(RuntimeError):
    """A git read that did not exit zero."""


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
        for x in (V / "execution_findings.jsonl").read_text().splitlines()
        if x.strip()
    ]
    prs = {(p["repo"], p["number"]): p for p in json.loads((V / "corpus_aged.json").read_text())}

    hist: dict[str, list] = {}
    scored: list[tuple[bool, bool]] = []
    skipped: collections.Counter[str] = collections.Counter()

    for r in rows:
        repo = str(r["repo"])
        if repo not in hist:
            c = SP / repo.replace("/", "_")
            if not c.is_dir():
                hist[repo] = []
            else:
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
        f = str(r["file"])
        touches = [ts for ts, _m, fs in h if f in fs]
        if not touches:
            skipped["file never in history"] += 1
            continue
        # the PR's own touch: the newest commit at or before the merge date
        merged = pr.get("merged_at", "")
        import datetime

        try:
            cut = int(
                datetime.datetime.fromisoformat(str(merged).replace("Z", "+00:00")).timestamp()
            )
        except ValueError:
            skipped["unparseable merge date"] += 1
            continue
        before = [t for t in touches if t <= cut]
        if not before:
            skipped["no touch before merge"] += 1
            continue
        when = max(before)
        returned = any(
            ts > when and ts - when <= WINDOW and f in fs and any(w in m for w in FIXWORDS)
            for ts, m, fs in h
        )
        scored.append((bool(r["findings"]), returned))

    if not scored:
        print(f"  REFUSING TO REPORT — nothing scoreable. skips: {dict(skipped)}")
        return 1

    spoke = [ret for sp, ret in scored if sp]
    silent = [ret for sp, ret in scored if not sp]
    print(f"  {len(scored)} funded units scored; skips: {dict(skipped)}\n")
    print("  DID A LATER FIX RETURN TO THIS FILE WITHIN 90 DAYS?\n")
    print(f"  {'':22s} {'units':>6} {'fix returned':>14}")
    for lbl, g in (("the model SPOKE", spoke), ("the model was SILENT", silent)):
        if g:
            print(f"  {lbl:22s} {len(g):6d} {sum(g) / len(g):13.1%}")
    if spoke and silent:
        a, b = sum(spoke), len(spoke) - sum(spoke)
        c, d = sum(silent), len(silent) - sum(silent)
        diff = (sum(spoke) / len(spoke) - sum(silent) / len(silent)) * 100
        print(f"\n  difference {diff:+.1f} points   Fisher exact p = {fisher(a, b, c, d):.4f}")
        print("\n  If this is null, the model's choice of WHERE to speak carries nothing beyond")
        print("  the ranker's, and the ranker is already measured on 20 repositories.")
    return 0


sys.exit(main())
