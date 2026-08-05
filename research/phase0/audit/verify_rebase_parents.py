"""Verify the parents the REBASE branch produces -- the only shape where it can be wrong.

WHAT: For each rebase-detected PR, derives the trunk commit structurally, runs the real
      resolver against a clone, and compares the two.
WHY:  For a squash and a merge commit the resolver returns `merge^1` and `parents[0]` by
      construction, so checking them against GitHub's first parent proves nothing. For a
      rebase the correct parent is NOT `merge^1` -- it is the parent of the earliest
      replayed commit -- so this is the one shape where the check distinguishes a right
      answer from a wrong one.

      Ground truth does not reuse the resolver's rule: the trunk commit is the first one
      walking back whose committer timestamp differs from the replayed run.
IMPORTS: stdlib json/subprocess; the `gh` CLI, git; phase0.parent_commit for the resolver.
CONSUMED BY: run by hand; writes results/rebase_parent_check.json.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "E:/Code/quanta_mind/research/phase0/src")

from phase0.parent_commit import resolve

RESULTS = Path("E:/Code/quanta_mind/research/phase0/results")
CACHE = Path("E:/Code/quanta_mind/research/phase0/data/gh_cache")
WORK = Path(
    "C:/Users/dhanu/AppData/Local/Temp/claude/E--Code-quanta-mind/"
    "7c4d5815-bcd0-4f09-b85a-c71462f0a842/scratchpad/rebase_clones"
)


def api(path: str, jq: str) -> object:
    out = subprocess.run(
        ["gh", "api", path, "--jq", jq],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
        check=False,
    )
    if out.returncode != 0 or not out.stdout.strip():
        return None
    return json.loads(out.stdout)


def expected_parent(repo: str, merge_sha: str, commits: int) -> tuple[str, int]:
    """The trunk commit the replay landed on: first differing committer timestamp back."""
    chain = api(
        f"repos/{repo}/commits?sha={merge_sha}&per_page={commits + 3}",
        "[.[] | {sha: .sha, when: .commit.committer.date}]",
    )
    if not isinstance(chain, list) or not chain:
        return "", 0
    first = str(chain[0]["when"])[:16]
    walked = 0
    for entry in chain:
        if str(entry["when"])[:16] != first:
            return str(entry["sha"]), walked
        walked += 1
    return "", walked


def clone(repo: str) -> Path | None:
    target = WORK / repo.replace("/", "__")
    if target.is_dir():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    out = subprocess.run(
        ["git", "clone", "--quiet", f"https://github.com/{repo}.git", str(target)],
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    return target if out.returncode == 0 else None


def main() -> int:
    rows = [
        r
        for r in json.loads((RESULTS / "rebase_structural.json").read_text(encoding="utf-8"))
        if r["shape"] == "rebase"
    ]
    checked = []
    for row in rows:
        repo, pr_id = str(row["repo"]), str(row["pr_id"])
        payload = json.loads((CACHE / f"pr-{pr_id}.json").read_text(encoding="utf-8"))
        merge_sha = str(payload.get("merge_commit_sha") or "")
        subjects = tuple(
            c["commit"]["message"].split("\n", 1)[0].strip()
            for c in json.loads((CACHE / f"pr-{pr_id}-commits.json").read_text(encoding="utf-8"))
        )
        files = (
            tuple(
                f["filename"]
                for f in json.loads((CACHE / f"pr-{pr_id}-files.json").read_text(encoding="utf-8"))
            )
            if (CACHE / f"pr-{pr_id}-files.json").is_file()
            else ()
        )

        truth, replayed = expected_parent(repo, merge_sha, int(row["commits"]))
        path = clone(repo)
        if path is None:
            checked.append({**row, "verdict": "clone_failed"})
            print(json.dumps(checked[-1]), flush=True)
            continue

        got = resolve(path, merge_sha, frozenset(files), len(subjects), subjects)
        first = api(f"repos/{repo}/commits/{merge_sha}", "{p: [.parents[].sha][0]}")
        merge_first_parent = (first or {}).get("p", "") if isinstance(first, dict) else ""
        checked.append(
            {
                "pr": f"{repo}#{payload.get('number')}",
                "commits": row["commits"],
                "replayed_run": replayed,
                "shape_detected": got.shape.value,
                "resolver_parent": got.parent_sha[:12],
                "structural_truth": truth[:12],
                "merge_first_parent": str(merge_first_parent)[:12],
                # The point of the exercise: for a rebase these two MUST differ, or the
                # walk did nothing and squash would have given the same answer.
                "differs_from_merge_caret_1": got.parent_sha[:12] != str(merge_first_parent)[:12],
                "verdict": "correct" if got.parent_sha and got.parent_sha == truth else "MISMATCH",
            }
        )
        print(json.dumps(checked[-1]), flush=True)

    (RESULTS / "rebase_parent_check.json").write_text(
        json.dumps(checked, indent=2) + "\n", encoding="utf-8"
    )
    good = [c for c in checked if c.get("verdict") == "correct"]
    print(f"\n{len(good)}/{len(checked)} rebase parents match the structural truth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
