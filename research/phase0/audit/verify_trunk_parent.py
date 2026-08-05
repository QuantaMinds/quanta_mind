"""Is each resolved parent GitHub's `merge_commit_sha^1`?

WHAT: Reads `parent_verification.json`, fetches each PR's merge commit from the API, and
      compares its FIRST parent against the parent the resolver recorded.
WHY:  Set equality on the diff proves the file list matches; it does not prove we diffed
      against the right commit, because a parent one commit off can reproduce the same
      files. The first-parent relationship is structural and an indirect merge cannot
      fake it. Over squashes and merge commits the check is near-tautological -- the
      resolver returns `merge^1` for both by construction -- so its real power is
      catching a PR misrouted to REBASE, which would return something else.

      An unresolved parent is stored as "" and `trunk.startswith("")` is true for every
      string, which made the first version report 20/20 when the answer was 19/20. That
      case is now rejected explicitly.
IMPORTS: stdlib json/subprocess; the `gh` CLI. Nothing from phase0.
CONSUMED BY: run by hand; writes results/trunk_parent_check.json.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

RESULTS = Path("E:/Code/quanta_mind/research/phase0/results")


def api(path: str, jq: str) -> dict:
    # encoding is explicit: the default on Windows is cp1252, and a commit message with a
    # non-Latin-1 byte in it made the decode raise inside gh's reader thread, which
    # surfaced as stdout=None rather than as an error anyone could read.
    out = subprocess.run(
        ["gh", "api", path, "--jq", jq],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    if out.returncode != 0 or not out.stdout:
        return {"_error": (out.stderr or "empty response").strip()[:200]}
    return json.loads(out.stdout)


def main() -> int:
    rows = json.loads((RESULTS / "parent_verification.json").read_text(encoding="utf-8"))
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    checked = []
    for row in rows:
        if only and row["band"] != only:
            continue
        repo, number = row["pr"].split("#")
        pull = api(f"repos/{repo}/pulls/{number}", "{merge_commit_sha: .merge_commit_sha}")
        merge_sha = pull.get("merge_commit_sha") or ""
        if not merge_sha:
            checked.append(
                {**_id(row), "verdict": "no_merge_sha", "detail": pull.get("_error", "")}
            )
            continue
        commit = api(f"repos/{repo}/commits/{merge_sha}", "{parents: [.parents[].sha]}")
        parents = commit.get("parents") or []
        if not parents:
            checked.append(
                {**_id(row), "verdict": "no_parents", "detail": commit.get("_error", "")}
            )
            continue
        trunk = parents[0]
        resolved = row["parent"]
        # An unresolved parent is stored as "". `trunk.startswith("")` is True for every
        # string, so the obvious comparison below reported agentops#819 -- whose parent
        # never resolved at all -- as confirmed. Checked explicitly rather than folded
        # into the match, which is the whole point of this exercise.
        if not resolved:
            checked.append({**_id(row), "merge_sha": merge_sha[:10], "verdict": "UNRESOLVED"})
            print(json.dumps(checked[-1]), flush=True)
            continue
        checked.append(
            {
                **_id(row),
                "merge_sha": merge_sha[:10],
                "merge_parents": len(parents),
                "trunk_first_parent": trunk[:10],
                "resolved_parent": resolved,
                # The resolved parent is stored abbreviated; compare on that prefix.
                "verdict": "trunk" if trunk.startswith(resolved) else "NOT_TRUNK",
            }
        )
        print(json.dumps(checked[-1]), flush=True)

    out = RESULTS / ("trunk_parent_check.json" if not only else f"trunk_parent_check_{only}.json")
    out.write_text(json.dumps(checked, indent=2) + "\n", encoding="utf-8")
    bad = [c for c in checked if c["verdict"] != "trunk"]
    print(f"\n{len(checked) - len(bad)}/{len(checked)} resolved to the trunk commit")
    for c in bad:
        print("  MISMATCH:", json.dumps(c))
    return 0


def _id(row: dict) -> dict:
    return {
        "band": row["band"],
        "pr": row["pr"],
        "shape": row["shape"],
        "base_ref": row["base_ref"],
    }


if __name__ == "__main__":
    os.environ.setdefault("GH_PAGER", "")
    raise SystemExit(main())
