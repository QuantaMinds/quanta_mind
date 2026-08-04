"""Corpus extraction: the AIDev dataset to a flat list of agent-authored PRs.

WHAT: Reads the AIDev dataset and emits one PRRecord per merged agent PR, filtered
      to a single language arm. Output is data/prs.jsonl.
WHY:  Every later stage keys off `parent_sha` -- exposure must be computed at the
      commit the agent branched from, never at the merged state. Capturing it here,
      once, is what makes that guarantee auditable rather than a convention each
      module is trusted to follow. RUNBOOK section 3 expects ~7,191 PRs total and
      calls extraction silently lossy below 3,000.
IMPORTS: stdlib only. Downstream: run_pipeline, classify_exposure, scan_outcome.
CONSUMED BY: run_pipeline.py; tests/test_extract_prs.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

Language = str  # "python" | "typescript" -- the two arms in scope, RUNBOOK section 7


@dataclass(frozen=True, slots=True)
class PRRecord:
    """One merged, agent-authored pull request."""

    pr_id: str
    repo: str
    language: Language
    parent_sha: str
    merged_sha: str
    merged_at: str  # ISO 8601 UTC
    changed_files: tuple[str, ...]
    changed_symbols: tuple[str, ...]


def extract(dataset: Path, language: Language) -> list[PRRecord]:
    """Load agent PRs for one language arm.

    Raises:
        NotImplementedError: Day 1 of the run. See RUNBOOK section 1.
    """
    raise NotImplementedError("Phase 0 Day 1 — see docs/findings/PHASE0_RUNBOOK.md")
