"""Does the firing gate fire where triage would matter — on the large pull requests?

WHAT: Runs the shipped ranker over every qualifying pull request and cross-tabulates whether it
      fired against how many files the change touched.
WHY:  **THE FILE-LEVEL PITCH IS DEAD AND THE QUEUE-LEVEL ONE IS UNMEASURED.** The ranking places
      reviewer attention LATER than alphabetical order, so "read these three files first" cannot be
      supported. What survives is a claim about WHICH PULL REQUESTS should not go unreviewed, and
      that claim has never been checked against the one property that decides whether triage is
      worth anything: size.

      **THE TWO OUTCOMES SAY OPPOSITE THINGS ABOUT THE PRODUCT.** If firing rises with file count,
      the gate is already triaging — it speaks up on the changes that are most expensive to skip.
      If firing is flat in file count, the gate fires on three-file pull requests as readily as on
      twenty-file ones, and on a three-file change there is nothing to triage: the reviewer reads
      all of it or none of it.

      **THIS IS NOT A TEST OF WHETHER FIRING IS RIGHT.** It asks only where the gate speaks. Whether
      the pull requests it speaks on are the ones that later break is a different measurement and
      needs a customer's incident data.
IMPORTS: stdlib; the product's ranker through `serve.run_review`.
CONSUMED BY: read by a human; writes `results/firing_by_size.json`.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))

from borrowed_clones import root as clone_root  # noqa: E402

from quantamind.rank.order import NothingToRank  # noqa: E402
from quantamind.serve.run_review import NoHistory, review  # noqa: E402
from quantamind.serve.working_clone import CloneFailed, ensure  # noqa: E402

CORPUS = HERE.parent / "results" / "execution_corpus.json"
OUT = HERE.parent / "results" / "firing_by_size.json"
GH_TIMEOUT_S = 90
BANDS = ((1, 2, "1-2"), (3, 4, "3-4"), (5, 7, "5-7"), (8, 14, "8-14"), (15, 10**6, "15+"))


def changed(repo: str, pr: int) -> list[str]:
    done = subprocess.run(
        ["gh", "api", f"repos/{repo}/pulls/{pr}/files?per_page=100", "--jq", ".[].filename"],
        capture_output=True,
        text=True,
        timeout=GH_TIMEOUT_S,
    )
    return [x for x in done.stdout.splitlines() if x.strip()] if done.returncode == 0 else []


def main() -> int:
    rows = json.loads(CORPUS.read_text())["selected"]
    # **THE SHARED ROOT, NOT A FRESH ONE PER RUN.** A new mkdtemp every time is what put
    # 11 GB of duplicate clones on the disk; this reuses them and bounds the total.
    root = clone_root()
    out: list[dict[str, object]] = []

    for row in rows:
        repo, pr = str(row["repo"]), int(row["pr"])
        files = changed(repo, pr)
        if not files:
            continue
        try:
            clone = ensure(repo, root)
        except (CloneFailed, subprocess.TimeoutExpired) as exc:
            print(f"  {repo}#{pr}: {str(exc)[:60]}", flush=True)
            continue
        stamp = subprocess.run(
            ["git", "-C", str(clone), "show", "-s", "--format=%ct", str(row["base"])],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if stamp.returncode != 0 or not stamp.stdout.strip():
            continue
        try:
            with tempfile.TemporaryDirectory() as scratch:
                got = review(
                    clone,
                    repo,
                    files,
                    pathlib.Path(scratch) / "a.db",
                    as_of=int(stamp.stdout.strip()),
                )
        except (NoHistory, NothingToRank, ValueError) as exc:
            print(f"  {repo}#{pr}: {type(exc).__name__}", flush=True)
            continue
        out.append(
            {
                "repo": repo,
                "pr": pr,
                "files_changed": len(files),
                "ranked": len(got.ranking.units),
                "fired": bool(got.ranking.fired),
            }
        )

    OUT.write_text(json.dumps(out, indent=1))
    if not out:
        print("\n  NOTHING SCORED — the run measured nothing and is void, not a null.")
        return 1

    fired = sum(1 for r in out if r["fired"])
    print(f"\n  {len(out)} pull requests ranked, {fired} fired = {fired / len(out):.0%}\n")
    print(f"  {'files changed':<16}{'n':>5}{'fired':>7}{'rate':>8}")
    for lo, hi, name in BANDS:
        band = [r for r in out if lo <= int(str(r["files_changed"])) <= hi]
        if not band:
            continue
        f = sum(1 for r in band if r["fired"])
        print(f"  {name:<16}{len(band):>5}{f:>7}{f / len(band):>8.0%}")
    small = [r for r in out if int(str(r["files_changed"])) <= 4]
    large = [r for r in out if int(str(r["files_changed"])) >= 8]
    if small and large:
        sr = sum(1 for r in small if r["fired"]) / len(small)
        lr = sum(1 for r in large if r["fired"]) / len(large)
        print(
            f"\n  <=4 files: {sr:.0%} fire.  >=8 files: {lr:.0%} fire.  difference {lr - sr:+.0%}"
        )
        print("  A flat rate means the gate fires on changes with nothing to triage.")
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
