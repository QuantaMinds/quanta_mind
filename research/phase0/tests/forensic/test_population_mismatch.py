"""Replay the defect that voided four analyses, and require the guard to refuse it.

WHAT: Feeds `assert_intersects` the REAL artefacts in the two shapes that matter -- candidates
      against `ours_caught`, which must raise, and goldens against it, which must not.
WHY:  **A guard nobody has watched fail is a guard nobody should trust.** The mis-read it exists
      to catch produced no exception and a plausible 68/32 split, so a test asserting only that
      the guard imports would certify nothing. The second case is the one that matters most: a
      guard could pass the first by refusing everything, which is the exact failure mode it is
      itself written to catch. → `docs/CORRECTIONS.md` entry 7.
IMPORTS: stdlib, pytest, and `bench/forensic/population.py`.
CONSUMED BY: `uv run pytest tests/forensic` and `just check`.
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "bench" / "forensic"))

from population import PopulationMismatch, assert_intersects  # noqa: E402


def test_the_actual_defect_raises_on_real_data() -> None:
    """`candidate in ours_caught` over the REAL artefacts, which is what nobody caught."""
    detail = json.loads((ROOT / "bench" / "results" / "gap_detail.json").read_text())
    labels = json.loads((ROOT / "bench" / "results" / "candidate_labels.json").read_text())
    caught = [g for d in detail for g in d["ours_caught"]]
    candidates = [r["text"] for r in labels if r["arm"] == "OURS"]
    assert caught and candidates, "fixtures are empty; this test would pass vacuously"

    with pytest.raises(PopulationMismatch) as raised:
        assert_intersects("our candidates against ours_caught", candidates, caught)
    assert "NOT ONE appears in both" in str(raised.value)


def test_the_correct_comparison_is_allowed_through() -> None:
    """Goldens against `ours_caught` is the field used for what it holds, and must NOT raise.

    Without this the guard could pass by refusing everything, which is the failure mode it is
    itself written to catch.
    """
    detail = json.loads((ROOT / "bench" / "results" / "gap_detail.json").read_text())
    goldens = [g for d in detail for g in d["golden"]]
    caught = [g for d in detail for g in d["ours_caught"]]
    assert assert_intersects("goldens against ours_caught", goldens, caught) > 0


def test_one_side_empty_is_a_result_not_an_error() -> None:
    """An arm that emitted nothing is a real outcome and must not be turned into a raise."""
    assert assert_intersects("nothing emitted", [], ["a", "b"]) == 0
    assert assert_intersects("nothing expected", ["a"], []) == 0
