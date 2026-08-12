"""A54's confound check: is the outcome rule's looseness correlated with EXPOSURE?

WHAT: For every BROKE PR carrying an exposure classification, re-derives the commit that
      triggered the verdict and asks whether it shares a SYMBOL with the PR or only a
      FILE. Reports the file-only share separately for exposed and unexposed.
WHY:  The rule fires when any fix-worded commit touches any file the PR touched. Measured
      against 20 hand-read PRs it was loose 8 times of 8, always machine-BROKE. Exposure
      means unresolvable call sites, which cluster in dynamic-feature code, which Wang,
      Chen, Ma, Chen and Xu (SEKE 2015) measured as significantly more change-prone. More
      churn means more spurious fix commits in the same files, so the looseness could
      correlate with the treatment and manufacture a positive.

      A file-only overlap is the false-positive shape: a repair of what a PR did usually
      touches what the PR touched, while unrelated work in a shared file does not. The
      discriminator is imperfect in a KNOWN direction -- `anomstack#163`'s genuine repair
      added a missing `import`, a module-level edit overlapping no function symbol -- so
      it OVER-estimates the artefact share and errs toward declaring a confound that is
      not there. That is the safe direction.

      Reading, fixed in A54 before any number existed: <5pp uniform, RR readable with the
      level caveat; 5-15pp exposed higher, RR carries it as a bound; >15pp exposed higher,
      RR is confounded and must not be read as the thesis.
IMPORTS: phase0.outcome.scan, phase0.pipeline.{changed,records_file,worktree}.
CONSUMED BY: run by hand; `results/a54_confound.json`.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

from phase0.outcome.conclusion import Outcome
from phase0.outcome.scan import scan
from phase0.pipeline.changed import module_name, source_at, symbols_touched, touched_line_ranges
from phase0.pipeline.records_file import read
from phase0.pipeline.worktree import CloneFailed, cloned

ROOT = Path(__file__).resolve().parents[1]


def exposure_of(row: dict) -> str:
    prims = {s.get("primary") for s in (row.get("symbols") or [])}
    if "exposed" in prims:
        return "exposed"
    if "unexposed" in prims:
        return "unexposed"
    if "unanalyzed_resource" in prims:
        return "unanalyzed_resource"
    return "unclassified"


def commit_symbols(clone: Path, sha: str) -> set[str]:
    """Symbols the evidence commit touched, via the pipeline's own helpers."""
    from subprocess import run as sh

    out = sh(
        ["git", "-C", str(clone), "diff", "--name-only", f"{sha}^", sha],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    found: set[str] = set()
    for path in out.stdout.splitlines():
        if not path.endswith(".py"):
            continue
        ranges = touched_line_ranges(clone, f"{sha}^", sha, path)
        found |= symbols_touched(source_at(clone, f"{sha}^", path), ranges, module_name(path))
    return found


def main() -> int:
    workspace = Path(sys.argv[1])
    exposure = {}
    for line in (ROOT / "results" / "exposure_agent_FINAL.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            exposure[r["pr_id"]] = exposure_of(r)

    records = {r.pr_id: r for r in read(ROOT / "results" / "agent_walk2_records.jsonl")}
    broke = {}
    for line in (ROOT / "results" / "agent_walk2_journal.md").read_text().splitlines():
        if not line.startswith("| "):
            continue
        c = [x.strip() for x in line.strip("|").split("|")]
        if len(c) < 20 or c[0] == "repo" or c[2] != "yes" or c[10] != "broke":
            continue
        if exposure.get(c[1]) in ("exposed", "unexposed"):
            broke[c[1]] = exposure[c[1]]

    print(f"{len(broke)} BROKE PRs carry an exposure classification", flush=True)
    by_repo: dict[str, list[str]] = collections.defaultdict(list)
    for pid in broke:
        by_repo[records[pid].repo].append(pid)

    results = []
    for n, (repo, pids) in enumerate(sorted(by_repo.items()), 1):
        try:
            with cloned(repo, workspace) as clone:
                for pid in pids:
                    rec = records[pid]
                    verdict = scan(clone, rec)
                    if verdict.outcome is not Outcome.BROKE or not verdict.evidence_sha:
                        results.append(
                            {
                                "pr_id": pid,
                                "repo": repo,
                                "exposure": broke[pid],
                                "status": f"not reproduced ({verdict.outcome.value})",
                            }
                        )
                        continue
                    touched = commit_symbols(clone, verdict.evidence_sha)
                    shared = set(rec.changed_symbols) & touched
                    results.append(
                        {
                            "pr_id": pid,
                            "repo": repo,
                            "exposure": broke[pid],
                            "criterion": verdict.criterion.value,
                            "evidence_sha": verdict.evidence_sha[:12],
                            "symbol_overlap": len(shared),
                            "file_only": not shared,
                            "commit_symbols": len(touched),
                        }
                    )
        except CloneFailed as exc:
            for pid in pids:
                results.append(
                    {
                        "pr_id": pid,
                        "repo": repo,
                        "exposure": broke[pid],
                        "status": f"clone failed: {str(exc)[:80]}",
                    }
                )
        print(f"[{n}/{len(by_repo)}] {repo} ({len(pids)} PRs)", flush=True)

    usable = [r for r in results if "file_only" in r]
    out = {"broke_with_exposure": len(broke), "resolved": len(usable), "rows": results}
    for grp in ("exposed", "unexposed"):
        g = [r for r in usable if r["exposure"] == grp]
        fo = sum(1 for r in g if r["file_only"])
        out[grp] = {"n": len(g), "file_only": fo, "share": round(fo / len(g), 4) if g else None}
    if out["exposed"]["share"] is not None and out["unexposed"]["share"] is not None:
        out["gap_pp"] = round((out["exposed"]["share"] - out["unexposed"]["share"]) * 100, 2)
    (ROOT / "results" / "a54_confound.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
