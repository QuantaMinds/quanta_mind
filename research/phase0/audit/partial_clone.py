"""Can a partial clone recover the repositories the timeout excludes?

WHAT: Runs each timed-out repository through `blob:none` and `blob:limit=1m`, largest
      first, and applies a decision rule fixed before any result was seen.
WHY:  Nine clone failures removed repositories with a median size of 921,790 KB against
      80,404 KB for those that cloned. That is a resource exclusion selecting on
      repository size, which tracks project age, activity and release discipline -- and
      it is the ONLY one of the four doors on to A16's confounder that is a property of
      our clone command rather than of the data, so the only one that can be closed
      rather than bounded.

      `full` is deliberately absent. Every target is a repository the re-scan already
      tried to clone in full and timed out on, so re-running it would cost eight more
      timeouts to re-observe a result already in the journal. The baseline is measured.

      `blob:limit=1m` is tested alongside `blob:none` because it is the better fit for
      this workload: Python sources sit far below 1 MB and arrive in the initial pack,
      so only the binaries that make these repositories a gigabyte are skipped, and
      nothing is lazily fetched for the files the pipeline actually parses.

      DECISION RULE, fixed before looking: a variant wins only if EVERY target completes
      clone plus one full PR pipeline inside CLONE_TIMEOUT_S. Lazy-fetch counts break a
      tie and never move that rule. If neither variant wins, the current strategy stands
      and A17 keeps the bound -- a legitimate outcome, which is why the bound was
      recorded before this probe was designed.
IMPORTS: stdlib json/pathlib; audit.clone_variants.
CONSUMED BY: run by hand before the full run; writes results/partial_clone.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "E:/Code/quanta_mind/research/phase0/src")
sys.path.insert(0, str(Path(__file__).parent))

from clone_variants import probe

from phase0.pipeline.worktree import CLONE_TIMEOUT_S

RESULTS = Path("E:/Code/quanta_mind/research/phase0/results")
WORK = Path("E:/Code/quanta_mind/research/phase0/data/partial_clone_probe")

VARIANTS = {
    "blob_none": ["--filter=blob:none"],
    "blob_limit_1m": ["--filter=blob:limit=1m"],
}


def main() -> int:
    targets = json.loads((RESULTS / "partial_clone_targets.json").read_text(encoding="utf-8"))
    sizes = json.loads((RESULTS / "probe_sizes.json").read_text(encoding="utf-8"))
    # Largest first. One failure eliminates a variant, so the case most likely to
    # eliminate should run first rather than after an hour of confirmations.
    targets.sort(key=lambda entry: -sizes.get(entry["repo"], 0))

    # Resume: a crash mid-probe must not discard the hours already spent. Each measured
    # (repo, variant) is skipped rather than repeated.
    existing = RESULTS / "partial_clone.json"
    rows: list[dict] = (
        json.loads(existing.read_text(encoding="utf-8")) if existing.is_file() else []
    )
    done = {(r["repo"], r["variant"]) for r in rows}
    for entry in targets:
        for variant, flags in VARIANTS.items():
            if (entry["repo"], variant) in done:
                continue
            row = probe(entry["repo"], variant, flags, entry, WORK)
            rows.append(row)
            print(json.dumps(row), flush=True)
            (RESULTS / "partial_clone.json").write_text(
                json.dumps(rows, indent=2) + "\n", encoding="utf-8"
            )

    print("\nDECISION RULE (fixed before looking): a variant wins only if every target")
    print(f"completes clone + one full PR pipeline inside CLONE_TIMEOUT_S = {CLONE_TIMEOUT_S}s.")
    for variant in VARIANTS:
        got = [r for r in rows if r["variant"] == variant]
        passed = [r for r in got if r.get("within_timeout")]
        honoured = all(r.get("filter_actually_applied", False) for r in got if r["outcome"] == "ok")
        lazy = sum(int(r.get("lazy_fetches", 0)) for r in got)
        print(
            f"  {variant:<14} {len(passed)}/{len(got)} in time | filter honoured: "
            f"{honoured} | lazy fetches: {lazy}"
        )
        for row in got:
            if row["outcome"] != "ok":
                print(f"      {row['repo']}: {row['outcome']} -- {row.get('stderr', '')[:120]}")
    print("Lazy fetches break a tie only. They do not move the rule above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
