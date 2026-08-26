"""The queue-level test again, with an outcome that is not true of almost every change.

WHAT: Same gate, same repositories, but a change counts as needing repair only when the later fix
      touched LINES the change touched — the actionability criterion — and within 30 days.
WHY:  **THE FIRST RUN'S OUTCOME WAS TRUE OF 81% OF CHANGES, WHICH CAPS THE ACHIEVABLE LIFT AT
      1.23x.** A pull request touches between two and twelve files, and the chance that ANY of them
      sees a fix-worded commit within ninety days is a union that approaches one in an active
      repository. The file-level outcome discriminates — that is the 1.21% against 3.12% — and at
      the pull-request level it says almost nothing.

      **THE BAR IN THAT RUN WAS 1.5x, ABOVE THE MAXIMUM POSSIBLE VALUE.** Recorded as a
      pre-registration error rather than a result: a bar nobody checked was reachable.

      **SO THE OUTCOME IS TIGHTENED, NOT THE GATE.** A fix that touches the same lines is the 26%
      the actionability study found reachable from a reviewed diff, and it should be far rarer at
      the change level.

BAR, FIXED BEFORE THIS RUN AND CHECKED AGAINST ITS CEILING FIRST:
      the ceiling is 1/base-rate and is printed before any lift is read. **PASS requires the lift
      to reach half the distance from 1.0 to that ceiling, with Fisher p < 0.01.** A bar stated as
      an absolute multiple is what went wrong last time.
IMPORTS: stdlib only. Local: `commit_stream`, `git_reads`.
CONSUMED BY: read by a human; writes `results/queue_triage_tight.json`.
"""

from __future__ import annotations

import bisect
import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import pathlib as _p
import sys as _s

_s.path.insert(0, str(_p.Path(__file__).resolve().parents[1]))
from commit_stream import ReadFailed, stream
from git_reads import shas_matching, touched_lines
from queue_triage import fisher

OUT = pathlib.Path(__file__).resolve().parents[1] / "results" / "queue_triage_tight.json"
CLONES = pathlib.Path("/Users/dhanu/.claude/jobs/4cdada9b/tmp/churn-clones")
YEAR, WINDOW = 365 * 86400, 30 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES, RECENT, PERCENTILE = 12, 400, 0.90
SAMPLE = 500  # git calls are the cost here; the first run needed none


def prior(idx: dict[str, list[int]], unit: str, ts: int) -> int:
    lst = idx.get(unit, [])
    return bisect.bisect_left(lst, ts) - bisect.bisect_left(lst, ts - YEAR)


def main() -> int:
    per: dict[str, list[dict[str, object]]] = {}
    for folder in sorted(CLONES.iterdir()):
        if not (folder / ".git").is_dir():
            continue
        try:
            commits = stream(str(folder))
        except ReadFailed:
            continue
        shas = shas_matching(folder, commits)
        if shas is None:
            print(f"  {folder.name}: the two git reads disagree — SKIPPED", flush=True)
            continue
        idx: dict[str, list[int]] = collections.defaultdict(list)
        for ts, _, files in commits:
            for f in files:
                idx[f].append(ts)

        rows: list[dict[str, object]] = []
        tops: list[int] = []
        for i, (ts, _msg, files) in enumerate(commits):
            if not (2 <= len(files) <= MAX_FILES):
                continue
            tops.append(max(prior(idx, f, ts) for f in files))
            if len(tops) < RECENT or len(rows) >= SAMPLE:
                continue
            window = sorted(tops[-RECENT:])
            floor = window[min(len(window) - 1, int(PERCENTILE * len(window)))]
            repaired = False
            for j in range(i + 1, len(commits)):
                ts2, msg2, files2 = commits[j]
                if ts2 - ts > WINDOW:
                    break
                if not any(w in msg2 for w in FIXWORDS):
                    continue
                for path in files2 & files:
                    before = touched_lines(folder, shas[i], path)
                    after = touched_lines(folder, shas[j], path)
                    if before and after and (before & after):
                        repaired = True
                        break
                if repaired:
                    break
            rows.append({"fired": tops[-1] > floor, "repaired": repaired})
        per[folder.name] = rows
        if rows:
            f = sum(1 for r in rows if r["fired"]) / len(rows)
            need = sum(1 for r in rows if r["repaired"])
            hit = sum(1 for r in rows if r["repaired"] and r["fired"])
            print(
                f"  {folder.name:<28} n={len(rows):<4} fires {f:>5.1%}  "
                f"repaired {need / len(rows):>5.1%}  caught {hit}/{need}",
                flush=True,
            )

    OUT.write_text(json.dumps(per, indent=1))
    rows = [r for v in per.values() for r in v]
    if not rows:
        print("\n  NOTHING SCORED — void, not a null.")
        return 1
    a = sum(1 for r in rows if r["repaired"] and r["fired"])
    b = sum(1 for r in rows if r["repaired"] and not r["fired"])
    c = sum(1 for r in rows if not r["repaired"] and r["fired"])
    d = sum(1 for r in rows if not r["repaired"] and not r["fired"])
    base = (a + b) / len(rows)
    rate = (a + c) / len(rows)
    print(f"\n  {len(rows)} changes, {len(per)} repositories")
    print(f"    base rate of a LINE-OVERLAPPING repair : {base:.1%}")
    print(f"    the gate fires on                       : {rate:.1%}")
    ceiling = 1 / base if base else 0.0
    print(f"\n    CEILING on the lift, printed BEFORE it : {ceiling:.2f}x")
    if a + b:
        lift = (a / (a + b)) / max(1e-9, rate)
        need = 1 + (ceiling - 1) / 2
        print(f"    observed lift                           : {lift:.2f}x")
        print(f"    PASS needs                              : {need:.2f}x  (half the distance)")
        print(f"    Fisher exact p                          : {fisher(a, b, c, d):.3e}")
        print(
            f"\n    -> {'PASS' if lift >= need and fisher(a, b, c, d) < 0.01 else 'does NOT pass'}"
        )
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
