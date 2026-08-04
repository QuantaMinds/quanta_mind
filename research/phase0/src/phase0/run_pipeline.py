"""Orchestration: checkout, census, graph, classify, for every PR in the corpus.

WHAT: Drives the per-PR loop -- check out the PARENT commit, census it, run the
      graph tool over it, classify exposure -- and writes one JSON line per PR.
WHY:  RUNBOOK section 3 invokes this module by name; the module list in section 1
      omits it, which is a documentation slip corrected in that file. It exists
      separately from the individual stages because the per-PR log is the audit
      trail, and it must be written by one place with one schema:

          pr_id, repo, parent_sha, symbols[], call_sites, resolved, unresolved,
          pycg_status, pycg_duration_ms, outcome, outcome_evidence

      Checkout is the parent commit, always. Every stage below trusts that and
      cannot re-check it -- see classify_exposure.py for why that matters.
IMPORTS: extract_prs, census, run_graph, classify_exposure. Not scan_outcome --
      the outcome scan runs as a separate pass so exposure cannot see it.
CONSUMED BY: the run itself; tests/test_run_pipeline.py.
"""

from __future__ import annotations

from pathlib import Path

from phase0.extract_prs import Language


def run(prs: Path, out: Path, language: Language, graph_tool: str = "pycg") -> int:
    """Process every PR in the corpus and write exposure records. Returns the count.

    Raises:
        NotImplementedError: Day 3 of the run. See RUNBOOK section 3.
    """
    raise NotImplementedError("Phase 0 Day 3 — see docs/findings/PHASE0_RUNBOOK.md")
