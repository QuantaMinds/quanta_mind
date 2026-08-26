"""Does the firing gate concentrate the changes that later need a fix? The queue-level claim.

WHAT: For every admissible change on the six out-of-sample repositories, computes whether the
      percentile gate would have fired and whether a fix returned within ninety days, then reports
      what share of the fix-returning changes the gate caught against what a random pick of the
      same size would catch.
WHY:  **EVERY MEASUREMENT IN THIS PROJECT SO FAR IS FILE-LEVEL AND THE ONLY SURVIVING FRAMING IS
      NOT.** Which file to read, where attention lands, where the fix touches — all file-level, all
      closed. What is left is *"you are already merging a third of your pull requests unreviewed;
      here are the ones that must not be."* That is a claim about WHICH CHANGES, and it has never
      been tested.

      **THE NULL IS THE GATE'S OWN FIRING RATE, NOT CHANCE.** A gate firing on 20% of changes
      catches 20% of anything if it fires at random. The question is whether it catches MORE than
      20% of the changes that later needed repair. Comparing against 50%, or against nothing, would
      make an unremarkable gate look like triage.

      **AND THE CONFOUND IS NAMED BEFORE THE RUN RATHER THAN AFTER.** Changes touching hot files
      get fix-returns partly because hot files are repaired often regardless of any particular
      change. **For the queue-level claim that is the mechanism and not an artefact** — a customer
      deciding what to skip does not care whether the fragility belongs to the change or to the
      file it lands in. It would be an artefact for a claim about the CHANGE being risky, and this
      document does not make that claim.

BAR, FIXED HERE BEFORE THE RUN:
      **PASS** — the gate catches ≥ 1.5x its own firing rate, and Fisher exact p < 0.01.
      **INCONCLUSIVE** — lift between 1.2x and 1.5x.
      **FAIL** — lift below 1.2x. At that point every framing this project has tried is closed and
      the honest reading is that the signal is real and inert.
IMPORTS: stdlib only. Local: the commit reader.
CONSUMED BY: read by a human; writes `results/queue_triage.json`.
"""

from __future__ import annotations

import bisect
import collections
import json
import pathlib
import statistics
import sys
from math import comb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import pathlib as _p
import sys as _s

_s.path.insert(0, str(_p.Path(__file__).resolve().parents[1]))
from commit_stream import ReadFailed, stream

OUT = pathlib.Path(__file__).resolve().parents[1] / "results" / "queue_triage.json"
CLONES = pathlib.Path("/Users/dhanu/.claude/jobs/4cdada9b/tmp/churn-clones")
YEAR, WINDOW = 365 * 86400, 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES = 12
RECENT = 400  # the window the product calibrates its floor over
PERCENTILE = 0.90  # the product's top-decile gate


def prior(idx: dict[str, list[int]], unit: str, ts: int) -> int:
    lst = idx.get(unit, [])
    return bisect.bisect_left(lst, ts) - bisect.bisect_left(lst, ts - YEAR)


def fisher(a: int, b: int, c: int, d: int) -> float:
    n = a + b + c + d
    if n == 0 or not all(x >= 0 for x in (a, b, c, d)):
        return 1.0
    observed = comb(a + b, a) * comb(c + d, c) / comb(n, a + c)
    total = 0.0
    for i in range(0, min(a + b, a + c) + 1):
        j = a + c - i
        if j < 0 or j > c + d:
            continue
        p = comb(a + b, i) * comb(c + d, j) / comb(n, a + c)
        if p <= observed + 1e-12:
            total += p
    return min(1.0, total)


def run(commits: list, idx: dict) -> list[dict[str, object]]:
    """One record per change: would the gate fire, and did a fix return."""
    out: list[dict[str, object]] = []
    tops: list[int] = []
    for i, (ts, _msg, files) in enumerate(commits):
        if not (2 <= len(files) <= MAX_FILES):
            continue
        top = max(prior(idx, f, ts) for f in files)
        tops.append(top)
        if len(tops) < RECENT:
            continue  # not enough history to calibrate a floor, so no decision is made
        # **THE FLOOR IS THE REPOSITORY'S OWN RECENT DISTRIBUTION, as the product computes it.**
        # A fixed absolute threshold fired on 198 of 200 real changes when it was tried.
        window = sorted(tops[-RECENT:])
        floor = window[min(len(window) - 1, int(PERCENTILE * len(window)))]
        returned = False
        for ts2, msg2, files2 in commits[i + 1 :]:
            if ts2 - ts > WINDOW:
                break
            if any(w in msg2 for w in FIXWORDS) and (files2 & files):
                returned = True
                break
        out.append({"fired": top > floor, "fix_returned": returned, "top": top, "floor": floor})
    return out


def main() -> int:
    per: dict[str, list[dict[str, object]]] = {}
    for folder in sorted(CLONES.iterdir()):
        if not (folder / ".git").is_dir():
            continue
        try:
            commits = stream(str(folder))
        except ReadFailed as exc:
            print(f"  {folder.name}: {str(exc)[:60]}", flush=True)
            continue
        idx: dict[str, list[int]] = collections.defaultdict(list)
        for ts, _, files in commits:
            for f in files:
                idx[f].append(ts)
        rows = run(commits, idx)
        per[folder.name] = rows
        if rows:
            fired = sum(1 for r in rows if r["fired"])
            hit = sum(1 for r in rows if r["fix_returned"] and r["fired"])
            need = sum(1 for r in rows if r["fix_returned"])
            print(
                f"  {folder.name:<28} n={len(rows):<5} fires {fired / len(rows):>5.1%}  "
                f"caught {hit}/{need} of the fix-returning = "
                f"{hit / max(1, need):>5.1%}",
                flush=True,
            )

    OUT.write_text(json.dumps(per, indent=1))
    rows = [r for v in per.values() for r in v]
    if not rows:
        print("\n  NOTHING SCORED — void, not a null.")
        return 1
    a = sum(1 for r in rows if r["fix_returned"] and r["fired"])
    b = sum(1 for r in rows if r["fix_returned"] and not r["fired"])
    c = sum(1 for r in rows if not r["fix_returned"] and r["fired"])
    d = sum(1 for r in rows if not r["fix_returned"] and not r["fired"])
    rate = (a + c) / len(rows)
    caught = a / max(1, a + b)
    print(f"\n  {len(rows)} changes across {len(per)} repositories")
    print(f"    the gate fires on                    : {rate:.1%}")
    print(f"    of changes a fix later returned to    : {a + b}")
    print(f"    the gate fired on                     : {a} = {caught:.1%}")
    print(f"\n    LIFT over its own firing rate        : {caught / max(1e-9, rate):.2f}x")
    print(f"    Fisher exact p                        : {fisher(a, b, c, d):.3e}")
    print("\n    BAR: >=1.5x and p<0.01 PASSES.  1.2-1.5x inconclusive.  <1.2x FAILS.")
    per_repo = [
        (
            sum(1 for r in v if r["fix_returned"] and r["fired"])
            / max(1, sum(1 for r in v if r["fix_returned"]))
        )
        / max(1e-9, sum(1 for r in v if r["fired"]) / max(1, len(v)))
        for v in per.values()
        if v
    ]
    if len(per_repo) > 1:
        print(f"\n    per-repository lift: {[f'{x:.2f}' for x in per_repo]}")
        print(
            f"    median {statistics.median(per_repo):.2f}x — a pooled number over six "
            f"repositories is a repo mix until this is read"
        )
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
