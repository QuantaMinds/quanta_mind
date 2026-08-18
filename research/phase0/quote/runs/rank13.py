"""Half A over design thirteen's pull requests: rank the changed files, then say where we looked.

WHAT: For each pull request, scores every changed Python file by prior-commit count in the year
      before the base commit, ranks descending, and reports whether the reviewer's published
      findings landed inside the top three -- the ranks the allocator funds.
WHY:  Design thirteen measures Half B alone. The product is Half A deciding WHERE to look and Half
      B deciding WHAT to say, and a run that exercises only the second is not the product.

      THIS IS A DEMONSTRATION OF ALLOCATION, NOT A VALIDATION OF THE RANKER. The validated claim --
      top three misses 1.21% of the changes a later fix returns to against alphabetical order's
      3.12% -- needs FORWARD history, and these pull requests merged too recently to have any. A
      corpus drawn from the present cannot answer a question about the future, and this script does
      not ask one. It asks a present-tense question: given where the ranker sends the budget, would
      the findings we published have been inside it?

      THE <=3 STRATUM IS VACUOUS AND IS PRINTED SEPARATELY. With three or fewer files, "inside the
      top three" is true by construction and measures arithmetic, not ranking.
IMPORTS: stdlib only (bisect, collections, json, pathlib, subprocess, sys). Local: `corpus`.
CONSUMED BY: nobody -- it prints and writes results/rank13.json.
"""

from __future__ import annotations

import bisect
import collections
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
CLONES = HERE / "clones13"
RUN = HERE / "results" / "quote13_run.json"
OUT = HERE / "results" / "rank13.json"
YEAR = 365 * 86400
BUDGET = 3


class GitReadFailed(RuntimeError):
    """A git read that did not exit zero. Never silently a short history.

    `git log` on a blob-filtered clone can emit a truncated stream AND a non-zero exit. Four
    measurements in this project were voided by code that read the stream and ignored the code.
    """


def history(clone: pathlib.Path) -> dict[str, list[int]]:
    """{path: [commit timestamps]} for Python files, ascending. Raises on a bad read."""
    p = subprocess.run(
        [
            "git",
            "-C",
            str(clone),
            "log",
            "--no-merges",
            "--name-only",
            "--pretty=format:%x00%ct",
            "--",
            "*.py",
        ],
        capture_output=True,
        text=True,
        timeout=1800,
    )
    if p.returncode != 0:
        raise GitReadFailed(f"{clone.name}: git log exited {p.returncode}: {p.stderr[:160]}")
    idx: dict[str, list[int]] = collections.defaultdict(list)
    for blk in p.stdout.split("\x00")[1:]:
        lines = blk.split("\n")
        try:
            ts = int(lines[0].strip())
        except ValueError:
            continue
        for f in lines[1:]:
            if f.strip():
                idx[f.strip()].append(ts)
    for v in idx.values():
        v.sort()
    return idx


def commit_time(clone: pathlib.Path, sha: str) -> int | None:
    p = subprocess.run(
        ["git", "-C", str(clone), "show", "-s", "--format=%ct", sha],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if p.returncode != 0:
        return None
    try:
        return int(p.stdout.strip().split("\n")[-1])
    except ValueError:
        return None


def main() -> int:
    blob = json.loads(RUN.read_text())
    idxs: dict[str, dict[str, list[int]]] = {}
    for d in sorted(CLONES.iterdir()):
        if (d / ".git").is_dir():
            idxs[d.name] = history(d)
            print(f"  history {d.name:32s} {len(idxs[d.name]):6d} python files")

    strata = {s: collections.Counter() for s in ("<=3", ">=4")}
    rows = []
    for r in blob["results"]:
        repo, pr = str(r["repo"]), int(str(r["pr"]))
        clone = CLONES / repo.replace("/", "_")
        idx = idxs.get(clone.name)
        if idx is None:
            continue
        try:
            sha = corpus.base_sha(repo, pr)
        except corpus.FetchFailed:
            continue
        ts = commit_time(clone, sha)
        if ts is None:
            strata[">=4"]["base_unresolved"] += 1
            continue

        pub = r["published"].get("B", [])
        files = sorted({str(f["path"]) for f in pub} | set())
        # Rank the pull request's whole Python surface, not only the files we happened to hit.
        touched = sorted(
            {
                ln[6:].strip()
                for ln in corpus.diff(repo, pr).split("\n")
                if ln.startswith("+++ b/") and ln.endswith(".py")
            }
        )
        if not touched:
            continue

        def prior(f: str, _idx: dict[str, list[int]] = idx, _ts: int = ts) -> int:
            lst = _idx.get(f, [])
            return bisect.bisect_left(lst, _ts) - bisect.bisect_left(lst, _ts - YEAR)

        scores = {f: prior(f) for f in touched}
        ordered = sorted(touched, key=lambda f: (-scores[f], f))
        top3 = set(ordered[:BUDGET])
        stratum = "<=3" if len(touched) <= BUDGET else ">=4"
        s = strata[stratum]
        s["prs"] += 1
        s["findings"] += len(files)
        s["in_top3"] += sum(1 for f in files if f in top3)
        s["flat"] += len(set(scores.values())) == 1
        rows.append(
            {
                "repo": repo,
                "pr": pr,
                "files": len(touched),
                "stratum": stratum,
                "top3": sorted(top3),
                "finding_files": files,
                "hit": [f for f in files if f in top3],
                "scores": scores,
            }
        )

    print(f"\n  {'stratum':>8} {'PRs':>5} {'findings':>9} {'in top 3':>9} {'share':>7} {'flat':>5}")
    for st in ("<=3", ">=4"):
        c = strata[st]
        f = c["findings"] or 0
        share = (c["in_top3"] / f) if f else 0.0
        print(f"  {st:>8} {c['prs']:>5} {f:>9} {c['in_top3']:>9} {share:>6.1%} {c['flat']:>5}")
    print("\n  <=3 is VACUOUS -- top three is every file. Only >=4 carries information.")
    print("  This is where the budget would have gone, not evidence the ranking is right:")
    print("  that needs forward history these pull requests are too recent to have.")
    OUT.write_text(
        json.dumps({"strata": {k: dict(v) for k, v in strata.items()}, "rows": rows}, indent=1)
    )
    print(f"\n  written to {OUT}")
    return 0


import corpus  # noqa: E402  -- after the guard classes so a bad import cannot look like a bad read

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

sys.exit(main())
