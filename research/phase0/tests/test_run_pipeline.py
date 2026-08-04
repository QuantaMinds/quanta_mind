"""Contract test for the pipeline orchestrator.

WHAT: Asserts run() is unimplemented and that the module does not reach the outcome
      scanner.
WHY:  The exposure pass and the outcome pass are separate on purpose -- if
      run_pipeline could see outcomes, an implementer could accidentally let the
      outcome influence classification, which is the leakage RUNBOOK section 1.2
      gates on. Asserting the import is absent is cheap and catches it structurally
      rather than by review.
IMPORTS: phase0.run_pipeline, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from phase0 import run_pipeline


def test_run_is_unimplemented() -> None:
    with pytest.raises(NotImplementedError):
        run_pipeline.run(Path("prs.jsonl"), Path("exposure.jsonl"), "python")


def test_pipeline_cannot_see_outcomes() -> None:
    """Exposure must be computable without knowing whether the PR broke anything."""
    tree = ast.parse(inspect.getsource(run_pipeline))
    imported = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "phase0.scan_outcome" not in imported
