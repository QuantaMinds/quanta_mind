"""Show ONE event end to end: what changed, what we ranked, what the fix later repaired.

WHAT: Finds an event where the ranker was right, prints the original change, the ranking with its
      reasons, the later fix, and whether the fix touched lines the change touched.
WHY:  **26.0% AGAINST 74.0% IS A NUMBER, AND A NUMBER IS NOT A MECHANISM UNTIL SOMEONE READS ONE
      CASE.** The claim is that the ranker names the right file and the defect is not in the diff a
      reviewer saw. That is either visible in a single example or it is not true.
IMPORTS: stdlib only. Local: `commit_stream`, `actionability`.
CONSUMED BY: read by a human. Writes nothing.
"""

from __future__ import annotations

import bisect
import collections
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from actionability import CLONES, FIXWORDS, MAX_FILES, WINDOW, YEAR
from commit_stream import stream
from git_reads import shas_matching, touched_lines

BUDGET = 3


def prior(idx: dict[str, list[int]], unit: str, ts: int) -> int:
    lst = idx.get(unit, [])
    return bisect.bisect_left(lst, ts) - bisect.bisect_left(lst, ts - YEAR)


def show(clone: pathlib.Path, sha: str, path: str, limit: int = 14) -> None:
    out = subprocess.run(
        ["git", "-C", str(clone), "show", "--unified=2", "--format=", sha, "--", path],
        capture_output=True,
        text=True,
        timeout=120,
    ).stdout.splitlines()
    body = [x for x in out if x.startswith(("+", "-", "@@")) and not x.startswith(("+++", "---"))]
    for line in body[:limit]:
        print(f"      {line[:104]}")
    if len(body) > limit:
        print(f"      ... {len(body) - limit} more lines")


def main() -> int:
    want = sys.argv[1] if len(sys.argv) > 1 else "disjoint"
    folder = CLONES / (sys.argv[2] if len(sys.argv) > 2 else "scrapy_scrapy")
    commits = stream(str(folder))
    shas = shas_matching(folder, commits)
    if shas is None:
        print("  the two git reads disagree; refusing to pair them")
        return 1
    idx: dict[str, list[int]] = collections.defaultdict(list)
    for ts, _, files in commits:
        for f in files:
            idx[f].append(ts)

    for i, (ts, msg, files) in enumerate(commits):
        if not (2 <= len(files) <= MAX_FILES):
            continue
        repairs = []
        for j in range(i + 1, len(commits)):
            ts2, msg2, files2 = commits[j]
            if ts2 - ts > WINDOW:
                break
            if any(w in msg2 for w in FIXWORDS):
                repairs += [(j, f) for f in files2 & files]
        if not repairs:
            continue
        score = {f: prior(idx, f, ts) for f in files}
        if len(set(score.values())) == 1:
            continue
        ranked = sorted(files, key=lambda f: (-score[f], f))
        top = set(ranked[:BUDGET])
        caught = [(j, f) for j, f in repairs if f in top]
        if not caught:
            continue
        j, path = caught[0]
        before, after = touched_lines(folder, shas[i], path), touched_lines(folder, shas[j], path)
        if not before or not after:
            continue
        overlap = bool(before & after)
        if (want == "overlap") != overlap:
            continue

        print(f"\n  THE CHANGE UNDER REVIEW   {shas[i][:10]}  {msg[:70]}")
        print(f"    files touched: {len(files)}")
        print(
            f"\n  WHAT WE WOULD HAVE SAID — ranked by fixes in the prior year, top {BUDGET} read:"
        )
        for rank, f in enumerate(ranked, 1):
            mark = "READ" if rank <= BUDGET else "  — "
            star = "  <-- the file the later fix returned to" if f == path else ""
            print(f"    {rank}. [{mark}] {score[f]:>3} prior fixes  {f[:58]}{star}")
        print(f"\n  THE LINES THAT CHANGE TOUCHED in {path}:")
        show(folder, shas[i], path)
        print(
            f"\n  THE FIX, {(commits[j][0] - ts) // 86400} days later   {shas[j][:10]}"
            f"  {commits[j][1][:60]}"
        )
        show(folder, shas[j], path)
        print(f"\n  change touched lines {sorted(before)[:8]}{'...' if len(before) > 8 else ''}")
        print(f"  fix    touched lines {sorted(after)[:8]}{'...' if len(after) > 8 else ''}")
        verdict = (
            "YES — the fix repaired code the reviewer saw"
            if overlap
            else "NO — the fix repaired code that was NOT in the reviewed diff"
        )
        print(f"\n  OVERLAP: {verdict}")
        return 0
    print("  no matching event found")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
