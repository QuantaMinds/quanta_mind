"""How often would the resolver call a PR a rebase?

WHAT: Applies `by_subject`'s rule -- k >= 2 consecutive subject matches walking back from
      the merge -- sourced entirely from the GitHub API, so it needs no clone.
WHY:  A28's hand-verification held no rebases at all, so the branch was verified only by
      unit test. A branch that never fires is a different risk from one that fires often
      and was never checked on real data, and the two need telling apart before either is
      recorded.

      It establishes prevalence, NOT correctness: it reuses the predicate under test, so
      it agrees with the resolver by construction. `rebase_structural.py` exists because
      of that limit.
IMPORTS: stdlib glob/json/subprocess; the `gh` CLI. Nothing from phase0.
CONSUMED BY: run by hand; writes results/rebase_prevalence.json.
"""

from __future__ import annotations

import glob
import json
import subprocess
import sys
from pathlib import Path

CACHE = Path("E:/Code/quanta_mind/research/phase0/data/gh_cache")
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


def subject(message: str) -> str:
    return message.split("\n", 1)[0].strip()


def main() -> int:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    rows = []
    for commits_file in sorted(glob.glob(str(CACHE / "pr-*-commits.json")))[:limit]:
        pr_id = Path(commits_file).name.removeprefix("pr-").removesuffix("-commits.json")
        head = CACHE / f"pr-{pr_id}.json"
        if not head.is_file():
            continue
        payload = json.loads(head.read_text(encoding="utf-8"))
        repo = ((payload.get("base") or {}).get("repo") or {}).get("full_name")
        merge_sha = payload.get("merge_commit_sha")
        if not repo or not merge_sha:
            continue
        subjects = [
            subject(c["commit"]["message"])
            for c in json.loads(Path(commits_file).read_text(encoding="utf-8"))
        ]
        if not subjects:
            continue

        # Walk back from the merge over as many commits as the PR has, and count how many
        # line up with the PR's subjects from the end -- `by_subject`'s rule exactly.
        chain = api(
            f"repos/{repo}/commits?sha={merge_sha}&per_page={min(len(subjects), 20) + 1}",
            "[.[] | .commit.message]",
        )
        if not isinstance(chain, list) or not chain:
            continue
        walked = [subject(str(m)) for m in chain]

        matched = 0
        for offset, walked_subject in enumerate(walked):
            index = len(subjects) - 1 - offset
            if index < 0 or subjects[index] != walked_subject:
                break
            matched += 1

        shape = (
            "rebase"
            if matched >= 2
            else (
                "merge_commit"
                if matched == 0
                and len(api(f"repos/{repo}/commits/{merge_sha}", "[.parents[].sha]") or []) >= 2
                else "squash"
            )
        )
        rows.append(
            {
                "pr_id": pr_id,
                "repo": repo,
                "commits": len(subjects),
                "consecutive_subject_matches": matched,
                "shape": shape,
            }
        )
        print(json.dumps(rows[-1]), flush=True)

    out = RESULTS / "rebase_prevalence.json"
    out.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    counts: dict[str, int] = {}
    for row in rows:
        counts[str(row["shape"])] = counts.get(str(row["shape"]), 0) + 1
    print(f"\nsurveyed {len(rows)} PRs: {counts}")
    multi = [r for r in rows if int(r["commits"]) > 1]  # type: ignore[arg-type]
    rebases = [r for r in multi if r["shape"] == "rebase"]
    print(f"multi-commit PRs: {len(multi)}, of which rebase: {len(rebases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
