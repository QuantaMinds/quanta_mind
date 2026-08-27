"""Does walking from a pull request's base instead of HEAD ever change what we would read?

WHAT: For each merged pull request in a repository that targets a NON-default branch, scores its
      changed files two ways -- counting touches reachable from HEAD (what the product does) and
      from the pull request's own base (what arguably it should) -- and reports how often the
      top-three selection differs.
WHY:  **THE PRODUCT WALKS HEAD, AND SO DOES THE RESEARCH.** `ingest/commits.py` and
      `research/phase0/external/git_reads.py` both pass no revision, so `git log` defaults to HEAD.
      History reachable from a pull request's base but not from HEAD is therefore never counted.
      On `apache/airflow` 27 of the last 100 closed pull requests target a non-default branch, so
      this is not an edge case there.

      **THE QUESTION IS NOT WHETHER THE COUNTS DIFFER -- THEY MUST -- BUT WHETHER THE RANKING
      DOES.** The ranking is comparative and the product reads the top three. A count that is
      uniformly low across every changed file selects the same three files and changes nothing.
      Only a difference concentrated in some files can move the selection, and only a moved
      selection changes what a customer sees.

      **A NULL HERE IS THE USEFUL OUTCOME.** It would make the HEAD horizon a documented property
      rather than a defect, and would say so with a number instead of an argument. A positive
      result is a pre-registered arm with gate 2a re-run, because changing the walk changes the
      touch counts that carry the founding claim -- not a quiet edit to a `git log` invocation.

READINGS, fixed before the run:
      For each pull request: the top-three by touch count under each walk, compared as a SET
      (which files get read), and as an ORDER (which file is rank 1). Ties are broken
      alphabetically, exactly as `rank/` does, so a tie is not counted as a difference.
IMPORTS: stdlib only. Reads a clone; writes `results/walk_horizon.json`.
CONSUMED BY: read by a human.
"""

from __future__ import annotations

import collections
import json
import pathlib
import subprocess
import sys

YEAR = 365 * 86400
SUFFIXES = (".py", ".pyi", ".ts", ".tsx", ".js")
TIMEOUT = 600
OUT = pathlib.Path(__file__).resolve().parent / "results" / "walk_horizon.json"


def git(clone: pathlib.Path, args: list[str]) -> str:
    done = subprocess.run(
        ["git", "-C", str(clone), *args], capture_output=True, text=True, timeout=TIMEOUT
    )
    return done.stdout if done.returncode == 0 else ""


def touches_from(clone: pathlib.Path, rev: str, paths: list[str]) -> dict[str, list[int]]:
    """Commit times per path, reachable from `rev`. One git call, not one per path.

    `--full-history` because a pathspec turns on history simplification and drops commits that
    really did touch the path -- the same reason `ingest/commits.py` passes it.
    """
    out: dict[str, list[int]] = {p: [] for p in paths}
    text = git(
        clone,
        [
            "log",
            "--no-merges",
            "--full-history",
            "--name-only",
            "--format=%x00%ct",
            rev,
            "--",
            *paths,
        ],
    )
    for chunk in text.split("\x00"):
        head, _, body = chunk.partition("\n")
        if not head.strip():
            continue
        when = int(head.strip())
        for line in body.splitlines():
            if line in out:
                out[line].append(when)
    return out


def top_three(counts: dict[str, int]) -> list[str]:
    """The three the allocator would fund. **Ties broken alphabetically, exactly as `rank/` does**,
    so a tie that the product resolves one way is not scored as a disagreement here."""
    return [p for p, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))][:3]


def main() -> int:
    clone = pathlib.Path(sys.argv[1])
    pulls = json.loads(pathlib.Path(sys.argv[2]).read_text())
    rows, skipped = [], collections.Counter()

    for pull in pulls:
        n, base_sha = pull["number"], pull["base_sha"]
        head = git(clone, ["rev-parse", f"refs/remotes/pull/{n}"]).strip()
        if not head or not git(clone, ["rev-parse", "--verify", f"{base_sha}^{{commit}}"]).strip():
            skipped["head or base not in clone"] += 1
            continue
        merge_base = git(clone, ["merge-base", base_sha, head]).strip()
        if not merge_base:
            skipped["no merge base"] += 1
            continue
        changed = [
            p
            for p in git(clone, ["diff", "--name-only", f"{merge_base}...{head}"]).split()
            if p.endswith(SUFFIXES)
        ]
        if len(changed) < 2:  # a ranking of one file cannot differ
            skipped["fewer than two reviewable files"] += 1
            continue
        as_of = int(git(clone, ["show", "-s", "--format=%ct", merge_base]).strip() or 0)
        if not as_of:
            skipped["no base timestamp"] += 1
            continue

        window = range(as_of - YEAR, as_of)
        by_head = touches_from(clone, "HEAD", changed)
        by_base = touches_from(clone, merge_base, changed)
        head_counts = {p: sum(1 for t in ts if t in window) for p, ts in by_head.items()}
        base_counts = {p: sum(1 for t in ts if t in window) for p, ts in by_base.items()}

        rows.append(
            {
                "number": n,
                "base_ref": pull["base_ref"],
                "files": len(changed),
                "head_top3": top_three(head_counts),
                "base_top3": top_three(base_counts),
                "head_total": sum(head_counts.values()),
                "base_total": sum(base_counts.values()),
            }
        )
        same_set = set(rows[-1]["head_top3"]) == set(rows[-1]["base_top3"])
        print(
            f"  #{n:<7} {pull['base_ref']:<16} {len(changed):>3} files  "
            f"counts {rows[-1]['head_total']:>4} -> {rows[-1]['base_total']:<4} "
            f"top3 {'SAME' if same_set else 'DIFFERENT'}",
            flush=True,
        )

    set_diff = [r for r in rows if set(r["head_top3"]) != set(r["base_top3"])]
    order_diff = [r for r in rows if r["head_top3"] != r["base_top3"]]
    count_diff = [r for r in rows if r["head_total"] != r["base_total"]]

    print(f"\n  pull requests measured: {len(rows)}")
    for reason, n in skipped.most_common():
        print(f"    skipped, {reason}: {n}")
    print(f"\n  counts differ at all      {len(count_diff)}/{len(rows)}")
    print(f"  top-three SET differs     {len(set_diff)}/{len(rows)}   <- changes what is read")
    print(f"  top-three ORDER differs   {len(order_diff)}/{len(rows)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"rows": rows, "skipped": dict(skipped)}, indent=1))
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
