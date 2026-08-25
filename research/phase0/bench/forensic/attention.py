"""Where human attention landed, against our ranking and against the two orderings that confound it.

WHAT: For each pull request that carries human inline review comments, ranks the changed files with
      the SHIPPED ranker and reports where the commented files sit under three orderings: ours,
      alphabetical, and by diff size. Paired per pull request.
WHY:  **THE QUESTION IS REDUNDANCY AND CONVERGENCE, NOT ORIENTATION, AND THE DIFFERENCE DECIDES
      WHAT A RESULT MEANS.** Reviewers here never saw the ranking, so concordance says attention
      already goes where we would point -- which argues the ranking is REDUNDANT -- and discordance
      says it is either wrong or pointing where humans systematically fail. **Both directions are
      ambiguous for the product.** The one outcome that decides anything alone is a null:
      indistinguishable from alphabetical means the routing line is decoration.

      **ALPHABETICAL IS THE CONTROL, NOT RANDOM.** GitHub's files API returns changed files in
      alphabetical order in 29 of 29 sampled pull requests, and reviewers read top-down. Against
      random, a positive result cannot be told from presentation order. **That the RENDERED page
      matches the API order is NOT verified** -- GitHub ships file-tree navigation and sort
      controls -- and if it does not, this control measures the wrong thing.

      **DIFF SIZE IS THE SECOND CONTROL AND IT IS NOT OPTIONAL.** Reviewers comment more on files
      with more changed lines, and files with high fix histories are often large hot files. Without
      it a positive result is confounded by surface area.

      **PRE-REGISTERED AS UNDERPOWERED.** 38 pull requests, a median of ONE commented file each,
      and 16 of the 38 from two repositories. This is reported as exploratory and the per-repository
      breakdown travels with it; a pooled statistic over that mix is a repo artefact.
IMPORTS: stdlib; the product's ranker through `serve.run_review`.
CONSUMED BY: read by a human; writes `results/attention.json`.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "src"))

from quantamind.serve.run_review import review  # noqa: E402
from quantamind.serve.working_clone import CloneFailed, ensure  # noqa: E402

CORPUS = HERE.parent / "results" / "execution_corpus.json"
OUT = HERE.parent / "results" / "attention.json"
GH_TIMEOUT_S = 90


def gh(path: str, jq: str) -> list[str]:
    done = subprocess.run(
        ["gh", "api", path, "--jq", jq], capture_output=True, text=True, timeout=GH_TIMEOUT_S
    )
    return [x for x in done.stdout.splitlines() if x.strip()] if done.returncode == 0 else []


def attended(repo: str, pr: int) -> list[str]:
    """Files carrying at least one inline review comment from a human.

    **INLINE ONLY, AND THE DEFINITION IS FIXED HERE.** Review summaries and pull-request body
    comments carry no file path, so they cannot place attention on a file. Bots are excluded by the
    `[bot]` login suffix.
    """
    return sorted(
        set(
            gh(
                f"repos/{repo}/pulls/{pr}/comments?per_page=100",
                '.[]|select(.user.login|endswith("[bot]")|not)|.path',
            )
        )
    )


def sizes(repo: str, pr: int) -> dict[str, int]:
    """{path: changed lines} for the pull request. The confounder, measured rather than assumed."""
    out: dict[str, int] = {}
    for line in gh(
        f"repos/{repo}/pulls/{pr}/files?per_page=100", '.[]|"\\(.filename) \\(.changes)"'
    ):
        path, _, count = line.rpartition(" ")
        if path:
            out[path] = int(count or 0)
    return out


def mean_normalised_rank(order: list[str], hit: set[str]) -> float | None:
    """Where the attended files sit in `order`, 0 = first, 1 = last. None when nothing landed."""
    marks = [i / max(1, len(order) - 1) for i, p in enumerate(order) if p in hit]
    return sum(marks) / len(marks) if marks else None


def main() -> int:
    rows = json.loads(CORPUS.read_text())["selected"]
    root = pathlib.Path(tempfile.mkdtemp(prefix="attention-"))
    out: list[dict[str, object]] = []

    for row in rows:
        repo, pr = str(row["repo"]), int(row["pr"])
        hit = set(attended(repo, pr))
        changed = sizes(repo, pr)
        if not hit or len(changed) < 3 or not (hit & set(changed)):
            continue
        try:
            clone = ensure(repo, root)
        except (CloneFailed, subprocess.TimeoutExpired) as exc:
            print(f"  {repo}#{pr}: {str(exc)[:70]}", flush=True)
            continue
        stamp = subprocess.run(
            ["git", "-C", str(clone), "show", "-s", "--format=%ct", str(row["base"])],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if stamp.returncode != 0 or not stamp.stdout.strip():
            continue
        with tempfile.TemporaryDirectory() as scratch:
            got = review(
                clone,
                repo,
                sorted(changed),
                pathlib.Path(scratch) / "a.db",
                as_of=int(stamp.stdout.strip()),
            )
        ours = [u.unit.site.path for u in got.ranking.units]
        if len(ours) < 3:
            continue
        alpha = sorted(ours)
        bysize = sorted(ours, key=lambda p: -changed.get(p, 0))
        record = {
            "repo": repo,
            "pr": pr,
            "files": len(ours),
            "attended": sorted(hit & set(ours)),
            "ours": mean_normalised_rank(ours, hit),
            "alphabetical": mean_normalised_rank(alpha, hit),
            "by_diff_size": mean_normalised_rank(bysize, hit),
        }
        if record["ours"] is None:
            continue
        out.append(record)
        print(
            f"  {repo:<28}#{pr:<6} {len(ours):>2} files  ours={record['ours']:.2f}  "
            f"alpha={record['alphabetical']:.2f}  size={record['by_diff_size']:.2f}",
            flush=True,
        )

    OUT.write_text(json.dumps(out, indent=1))
    print(f"\n  {len(out)} pull requests scored -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
