"""Re-run the REAL pipeline for named PRs and dump every intermediate stage.

WHAT: For each `pr_id`, replays clone -> parent worktree -> scope -> census -> PyCG ->
      classify -> outcome scan, printing what each stage produced and comparing the
      result against the row the production run wrote.
WHY:  The study's numbers rest on a stack nobody has watched end to end. Every defect this
      project found was a stage producing a plausible value that a later stage consumed
      without question, so the check that matters is not "does it run" but "does each
      stage's output mean what the next stage assumes".

      It re-runs the PRODUCTION functions rather than reimplementing them -- a
      reimplementation would verify the reimplementation. And it diffs its own result
      against the recorded row: a trace that agrees with the run proves reproducibility,
      and one that disagrees is a finding either way.
IMPORTS: phase0.{scope,census,classify_exposure}, phase0.graph.run_graph,
      phase0.outcome.scan, phase0.pipeline.{measure,worktree,records_file}.
CONSUMED BY: run by hand; `results/trace_end_to_end.json`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from phase0 import scope
from phase0.census import count_call_sites
from phase0.classify_exposure import classify
from phase0.graph.run_graph import run as run_graph  # same alias measure.py uses
from phase0.outcome.scan import scan
from phase0.pipeline.records_file import read
from phase0.pipeline.worktree import CloneFailed, at_commit, cloned

ROOT = Path(__file__).resolve().parents[1]


def trace(rec, produced: dict, workspace: Path) -> dict:
    t: dict = {"pr_id": rec.pr_id, "repo": rec.repo, "stages": []}

    def stage(name: str, **kw):
        t["stages"].append({"stage": name, **kw})
        head = ", ".join(f"{k}={v}" for k, v in list(kw.items())[:4])
        print(f"    {name:<22} {head}", flush=True)

    stage(
        "0. record",
        parent_sha=rec.parent_sha[:10],
        merged_sha=rec.merged_sha[:10],
        base_ref=rec.base_ref,
        resolution=f"{rec.parent_resolution_method}/{rec.parent_resolution_rule}",
    )
    stage(
        "0b. record.changed",
        files=len(rec.changed_files),
        symbols=len(rec.changed_symbols),
        first_symbol=rec.changed_symbols[0] if rec.changed_symbols else None,
    )

    with cloned(rec.repo, workspace) as clone:
        stage("1. clone", path=str(clone.name), exists=clone.is_dir())
        with at_commit(clone, rec.parent_sha, "trace") as tree:
            if tree is None:
                stage("2. worktree", result="UNAVAILABLE")
                return t
            stage("2. worktree", at=rec.parent_sha[:10], note="PARENT commit, never the merge")

            resolved = scope.resolve(tree, rec.changed_files)
            if resolved is None:
                stage("3. scope", result="None -- nothing analysable")
                return t
            stage(
                "3. scope",
                package_root=resolved.package_root.name,
                files_in_scope=resolved.file_count,
                recorded_by_run=produced.get("scope_files"),
            )

            sites, unreadable = [], 0
            for path in resolved.files:
                try:
                    src = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    unreadable += 1
                    continue
                sites += count_call_sites(src, path=str(path), module=resolved.module_of(path))
            named = sum(1 for s in sites if s.callee_name)
            stage(
                "4. census",
                call_sites=len(sites),
                named=named,
                unnamed=len(sites) - named,
                unreadable_files=unreadable,
                recorded_by_run=produced.get("call_sites"),
            )

            graph = run_graph(resolved, timeout_s=600)
            edges = list(graph.edges)
            stage(
                "5. pycg",
                status=graph.status.value,
                edges=len(edges),
                mem_cap=graph.mem_cap,
                recorded_by_run=produced.get("graph_status"),
            )
            t["edge_sample"] = [f"{e.src} -> {e.dst}" for e in edges[:5]]

            edge_map: dict[str, set[str]] = {}
            for e in edges:
                edge_map.setdefault(e.src, set()).add(e.dst)

            rows = []
            for sym in rec.changed_symbols:
                res = classify(sym, sym.rsplit(".", 1)[-1], sites, edge_map, graph.status)
                naming = [s for s in sites if s.callee_name == sym.rsplit(".", 1)[-1]]
                inbound = [src for src, dsts in edge_map.items() if sym in dsts]
                rows.append(
                    {
                        "symbol": sym,
                        "primary": res.primary.value if res.primary else "",
                        "call_sites_naming_it": len(naming),
                        "graph_edges_into_it": len(inbound),
                        "single_site_pairs": res.single_site_pairs,
                        "multi_site_pairs": res.multi_site_pairs,
                    }
                )
                print(
                    f"      symbol {sym.split('.')[-1][:30]:<30} -> "
                    f"{rows[-1]['primary'] or 'NONE':<12}"
                    f" sites_naming={len(naming)} edges_in={len(inbound)}",
                    flush=True,
                )
            t["symbols"] = rows
            was = [s.get("primary") for s in (produced.get("symbols") or [])]
            now = [r["primary"] for r in rows]
            stage("6. classify", reproduced=(was == now), run_said=was, trace_said=now)

        verdict = scan(clone, rec)
        stage(
            "7. outcome",
            outcome=verdict.outcome.value,
            criterion=verdict.criterion.value if verdict.criterion else "",
            evidence=verdict.evidence_sha[:10] if verdict.evidence_sha else "",
            commits_examined=verdict.commits_examined,
        )
    return t


def main() -> int:
    workspace = Path(sys.argv[1])
    wanted = sys.argv[2:]
    records = {r.pr_id: r for r in read(ROOT / "results" / "agent_walk2_records.jsonl")}
    produced = {}
    for line in (ROOT / "results" / "exposure_agent_FINAL.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            produced[r["pr_id"]] = r

    out = []
    for pid in wanted:
        rec = records[pid]
        print(
            f"\n=== {rec.repo}  pr_id={pid} "
            f"(recorded scope_files={produced[pid].get('scope_files')}) ===",
            flush=True,
        )
        try:
            out.append(trace(rec, produced[pid], workspace))
        except CloneFailed as exc:
            print(f"    CLONE FAILED: {exc}", flush=True)
            out.append({"pr_id": pid, "repo": rec.repo, "error": str(exc)[:200]})
    import os

    tag = os.environ.get("TRACE_TAG", "all")
    (ROOT / "results" / f"trace_{tag}.json").write_text(json.dumps(out, indent=1) + "\n")
    print("\nwritten: results/trace_end_to_end.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
