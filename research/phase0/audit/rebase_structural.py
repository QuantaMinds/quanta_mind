"""Confirm the merge shape without reading a single subject line.

WHAT: Counts how many commits back from the merge share its committer timestamp, and
      compares that verdict against the subject-based one.
WHY:  The prevalence survey reuses the resolver's own predicate, so both error directions
      survive it. The dangerous one is a FALSE SQUASH: a real rebase whose message was
      amended gives k <= 1, routes to squash, and returns `merge^1` -- which for a rebase
      is the PR's own second-to-last commit. Wrong parent, no error, downstream checks
      all pass.

      GitHub's rebase-merge replays each commit and rewrites committer information, so a
      rebase of N leaves N commits sharing one committer timestamp while a squash leaves
      exactly one. That shares no failure mode with subject matching.
IMPORTS: stdlib json/subprocess; the `gh` CLI. Nothing from phase0.
CONSUMED BY: run by hand; writes results/rebase_structural.json.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

RESULTS = Path("E:/Code/quanta_mind/research/phase0/results")


def api(path: str, jq: str) -> object:
    out = subprocess.run(
        ["gh", "api", path, "--jq", jq],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    if out.returncode != 0 or not out.stdout.strip():
        return None
    return json.loads(out.stdout)


def structural_run(repo: str, merge_sha: str, depth: int) -> int:
    """How many commits back from the merge share its committer timestamp.

    A rebase of N commits is replayed in one operation, so N commits carry the same
    committer time. A squash writes one. Author dates are preserved by a rebase and are
    therefore useless here -- the committer side is what GitHub rewrites.
    """
    chain = api(
        f"repos/{repo}/commits?sha={merge_sha}&per_page={min(depth, 30) + 2}",
        "[.[] | .commit.committer.date]",
    )
    if not isinstance(chain, list) or not chain:
        return 0
    stamps = [str(d)[:16] for d in chain]  # to the minute; a replay is not instantaneous
    run = 1
    for stamp in stamps[1:]:
        if stamp != stamps[0]:
            break
        run += 1
    return run


def main() -> int:
    rows = json.loads((RESULTS / "rebase_prevalence.json").read_text(encoding="utf-8"))
    wanted = [
        r for r in rows if r["shape"] == "rebase" or (r["commits"] > 1 and r["shape"] == "squash")
    ]
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    # Every rebase, plus multi-commit squashes as the control group.
    ordered = [r for r in wanted if r["shape"] == "rebase"] + [
        r for r in wanted if r["shape"] != "rebase"
    ][:limit]

    checked = []
    for row in ordered:
        head = Path(f"E:/Code/quanta_mind/research/phase0/data/gh_cache/pr-{row['pr_id']}.json")
        payload = json.loads(head.read_text(encoding="utf-8"))
        merge_sha = payload.get("merge_commit_sha")
        if not merge_sha:
            continue
        run = structural_run(str(row["repo"]), str(merge_sha), int(row["commits"]))
        expect = "rebase" if run >= 2 else "squash"
        checked.append(
            {
                **row,
                "structural_committer_run": run,
                "structural_shape": expect,
                "agrees": expect == row["shape"],
            }
        )
        print(json.dumps(checked[-1]), flush=True)

    (RESULTS / "rebase_structural.json").write_text(
        json.dumps(checked, indent=2) + "\n", encoding="utf-8"
    )
    disagree = [c for c in checked if not c["agrees"]]
    print(f"\n{len(checked) - len(disagree)}/{len(checked)} agree between subject and structure")
    for c in disagree:
        print("  DISAGREE:", json.dumps(c))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
