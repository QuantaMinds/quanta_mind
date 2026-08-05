"""Measuring one PR at its parent commit: census, graph, classify.

WHAT: Runs the three measurement stages over one checked-out tree and assembles
      the audit record for it.
WHY:  Split from run_pipeline.py, which owns the loop — grouping, checkpointing
      and failure isolation. This module owns what happens to a single PR once a
      tree exists, and knows nothing about clones, restarts or ordering.

      It never imports scan_outcome. The outcome is scanned in a separate pass so
      that nothing on the exposure path can see whether a PR broke, which is the
      leakage `PHASE0_RUNBOOK.md` “Exposure classifier tests” calls the likeliest way to fake a
      positive by accident.
IMPORTS: phase0.scope, census, classify_exposure, run_graph, extract_prs, and
      pipeline.record. Never phase0.scan_outcome.
CONSUMED BY: run_pipeline.py; tests/controls/test_controls_corpus.py (end-to-end, no direct test).
"""

from __future__ import annotations

import time
from pathlib import Path

from phase0 import scope
from phase0.census import CallSite, count_call_sites, non_builtin
from phase0.classify_exposure import classify
from phase0.extract_prs import PRRecord
from phase0.graph.run_graph import GraphResult
from phase0.graph.run_graph import run as run_graph
from phase0.pipeline import record


def symbol_rows(
    pr: PRRecord, sites: list[CallSite], graph: GraphResult
) -> tuple[record.SymbolRow, ...]:
    """One row per changed symbol. An attrition status produces no rows at all.

    A7: SYNTAX_UNSUPPORTED is excluded from the study, so it must not reach
    classify() -- which refuses it loudly rather than inventing an arm.
    """
    if graph.status.is_attrition:
        return ()

    edges: dict[str, set[str]] = {}
    for edge in graph.edges:
        edges.setdefault(edge.src, set()).add(edge.dst)

    rows: list[record.SymbolRow] = []
    for symbol in pr.changed_symbols:
        result = classify(symbol, symbol.rsplit(".", 1)[-1], sites, edges, graph.status)
        rows.append(
            record.SymbolRow(
                symbol=symbol,
                primary=result.primary.value if result.primary else "",
                sensitivity_low=result.sensitivity_low.value if result.sensitivity_low else "",
                sensitivity_high=result.sensitivity_high.value if result.sensitivity_high else "",
                single_site_pairs=result.single_site_pairs,
                multi_site_pairs=result.multi_site_pairs,
            )
        )
    return tuple(rows)


def measure(tree: Path, pr: PRRecord, timeout_s: int) -> record.PRAudit | None:
    """Census, graph and classify one PR. None when there is nothing analysable.

    Timings are collected per stage because RUNBOOK's pilot sizes the full run
    from them; without per-stage numbers a slow run cannot be attributed.
    """
    timings: dict[str, int] = {}

    started = time.monotonic()
    resolved = scope.resolve(tree, pr.changed_files)
    timings["scope_ms"] = int((time.monotonic() - started) * 1000)
    if resolved is None:
        return None

    started = time.monotonic()
    sites: list[CallSite] = []
    for path in resolved.files:
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue  # unreadable file: counted by omission, never fatal
        sites += count_call_sites(source, path=str(path), module=resolved.module_of(path))
    timings["census_ms"] = int((time.monotonic() - started) * 1000)

    started = time.monotonic()
    graph = run_graph(resolved, timeout_s=timeout_s)
    timings["graph_ms"] = int((time.monotonic() - started) * 1000)

    interesting = non_builtin(sites)
    return record.PRAudit(
        pr_id=pr.pr_id,
        repo=pr.repo,
        repo_id=pr.repo_id,
        arm=pr.arm,
        task_type=pr.task_type,
        parent_sha=pr.parent_sha,
        merged_sha=pr.merged_sha,
        graph_status=graph.status.value,
        graph_detail=graph.detail,
        graph_detail_path=graph.detail_path,
        graph_detail_line=graph.detail_line,
        scope_files=resolved.file_count,
        call_sites=len(sites),
        non_builtin_sites=len(interesting),
        # A10's prevalence denominator: a site with no static callee name can be
        # attributed to no symbol, so the variable is structurally blind to it.
        no_static_callee_sites=sum(1 for s in interesting if not s.callee_name),
        symbols=symbol_rows(pr, sites, graph),
        duration_ms=timings,
    )
