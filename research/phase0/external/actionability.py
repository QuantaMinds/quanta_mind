"""When the ranker is RIGHT, could a reviewer have done anything? The missing link, measured.

WHAT: Takes the events where top-three-by-fix-history correctly predicted the file a later fix
      returned to, and asks whether that fix touched LINES THE ORIGINAL CHANGE TOUCHED. Reports the
      overlapping share, which is the share of correct predictions a reviewer could have acted on.
WHY:  **THE RANKER IS VALIDATED AND FIVE PRODUCT FRAMINGS HAVE FAILED, NONE OF THEM AT THE SIGNAL.**
      That permits two readings — the framing is not found yet, or the signal is real and INERT,
      predicting something true that nobody can act on. **This measures the second one directly.**

      The chain the product rests on is: we rank the risky file (measured) -> the reviewer reads it
      (unmeasured) -> they find the defect (unmeasured) -> it never reaches production (unmeasured).
      **The second link has a testable failure mode.** If the later fix repairs code the reviewed
      change never touched -- a different function, a line added months afterwards -- then pointing
      at that file was CORRECT and USELESS: no reviewer reading that diff could have found the
      defect, because it was not in the diff.

      **THIS IS THE `scan.py` FILE-LEVEL RULE'S KNOWN WEAKNESS TURNED INTO A MEASUREMENT.** The
      outcome rule counts a repair when a fix-worded commit touches any FILE the change touched,
      and `PHASE0_PREREGISTRATION.md` A53 records an attempt to tighten it to symbol overlap that
      was WITHDRAWN because it lost real repairs. This does not change the rule. It reports what
      share of what the rule admits is reachable from the diff.

      **LINE OVERLAP IS A FLOOR, NOT THE ANSWER.** A fix to a caller of the function under review is
      genuinely reachable and will not overlap. So a low overlap does not prove inertness; it bounds
      how much of the signal is *directly* actionable and forces the rest to be argued rather than
      assumed.
IMPORTS: stdlib only. Local: `commit_stream`.
CONSUMED BY: read by a human; writes `results/actionability.json`.
"""

from __future__ import annotations

import bisect
import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from commit_stream import ReadFailed, stream
from git_reads import shas_matching, touched_lines

OUT = pathlib.Path(__file__).resolve().parent / "results" / "actionability.json"
CLONES = pathlib.Path("/Users/dhanu/.claude/jobs/4cdada9b/tmp/churn-clones")
YEAR, WINDOW = 365 * 86400, 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES, MAX_EVENTS, BUDGET = 12, 400, 3


def prior(idx: dict[str, list[int]], unit: str, ts: int) -> int:
    lst = idx.get(unit, [])
    return bisect.bisect_left(lst, ts) - bisect.bisect_left(lst, ts - YEAR)


def main() -> int:
    totals = collections.Counter()
    per: dict[str, dict[str, int]] = {}

    for folder in sorted(CLONES.iterdir()):
        if not (folder / ".git").is_dir():
            continue
        name = folder.name
        try:
            commits = stream(str(folder))
        except ReadFailed as exc:
            print(f"  {name}: {str(exc)[:60]}", flush=True)
            continue
        # **THE SHA COMES FROM THE SAME READ AS THE COMMIT, NOT A SECOND `git log`.** A separate
        # log returns EVERY commit; `stream()` keeps only those touching a `.py` file, so the two
        # lists differ — 50,095 against 34,360 on ansible — and zipping them pairs commit *i* of
        # one with commit *i* of the other. The first version did exactly that and the guard below
        # refused all six repositories rather than measure the wrong diffs.
        shas = shas_matching(folder, commits)
        if shas is None:
            print(f"  {name}: the sha read and the commit read disagree — SKIPPED", flush=True)
            continue

        idx: dict[str, list[int]] = collections.defaultdict(list)
        for ts, _, files in commits:
            for f in files:
                idx[f].append(ts)

        seen = collections.Counter()
        for i, (ts, _msg, files) in enumerate(commits):
            if not (2 <= len(files) <= MAX_FILES):
                continue
            repairs: list[tuple[int, str]] = []
            for j in range(i + 1, len(commits)):
                ts2, msg2, files2 = commits[j]
                if ts2 - ts > WINDOW:
                    break
                if any(w in msg2 for w in FIXWORDS):
                    for f in files2 & files:
                        repairs.append((j, f))
            if not repairs:
                continue
            score = {f: prior(idx, f, ts) for f in files}
            vals = sorted(score.values(), reverse=True)
            if len(set(vals)) == 1:
                continue
            top = set(sorted(files, key=lambda f: (-score[f], f))[:BUDGET])
            caught = [(j, f) for j, f in repairs if f in top]
            if not caught:
                continue
            seen["events_hit"] += 1
            j, path = caught[0]
            before = touched_lines(folder, shas[i], path)
            after = touched_lines(folder, shas[j], path)
            if not before or not after:
                seen["unreadable"] += 1
                continue
            seen["measured"] += 1
            seen["overlapping" if (before & after) else "disjoint"] += 1
            if seen["measured"] >= MAX_EVENTS:
                break

        per[name] = dict(seen)
        m = seen["measured"]
        if m:
            print(
                f"  {name:<28} {m:>4} measured  overlap {seen['overlapping'] / m:>6.1%}", flush=True
            )
        totals.update(seen)

    OUT.write_text(json.dumps({"per_repo": per, "totals": dict(totals)}, indent=1))
    m = totals["measured"]
    print(f"\n  {totals['events_hit']} events the ranker got RIGHT, {m} with both diffs readable")
    if m:
        print(
            f"    the later fix touched lines the change touched : {totals['overlapping']:>5}"
            f" = {totals['overlapping'] / m:.1%}"
        )
        print(
            f"    the later fix touched only OTHER lines         : {totals['disjoint']:>5}"
            f" = {totals['disjoint'] / m:.1%}"
        )
        print("\n  The second row is where the ranking was right about the FILE and the defect was")
        print("  not in the diff a reviewer read. A floor, not the answer: a fix to a caller is")
        print("  reachable and will not overlap.")
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
