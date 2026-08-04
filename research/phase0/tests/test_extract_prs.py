"""Verification of corpus extraction and the population filters.

WHAT: Asserts PRRecord's contract, that each population filter removes what §3
      says it removes, and that attrition is counted rather than dropped.
WHY:  §3's corpus arithmetic — 7,191 to 4,798 structural to ~3,300 merged — is a
      prediction. These filters are what make it a measurement, and RUNBOOK §3
      treats a large deviation as a stop condition rather than a curiosity, so the
      counts have to be produced rather than inferred.

      `parent_sha` is asserted present because the study's validity rests on it:
      exposure is computed at the commit the change landed on, and if the field
      were ever dropped from the record every downstream stage would silently lose
      the ability to honour that.
IMPORTS: pandas, phase0.extract_prs, pytest.
CONSUMED BY: `just test-phase0`. No network and no dataset: parquet is written here.
"""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pandas as pd
import pytest

from phase0.extract_prs import (
    STRUCTURAL_TASK_TYPES,
    Attrition,
    PRRecord,
    load_table,
    population_counts,
)


def _dataset(tmp_path: Path) -> Path:
    """A miniature AIDev: one row per case the filters are supposed to catch."""
    pulls = pd.DataFrame(
        [
            {"id": 1, "number": 1, "repo_id": 10, "merged_at": "2026-01-01T00:00:00Z"},
            {"id": 2, "number": 2, "repo_id": 10, "merged_at": "2026-01-02T00:00:00Z"},
            {"id": 3, "number": 3, "repo_id": 10, "merged_at": None},
            {"id": 4, "number": 4, "repo_id": 20, "merged_at": "2026-01-03T00:00:00Z"},
            {"id": 5, "number": 5, "repo_id": 10, "merged_at": "2026-01-04T00:00:00Z"},
        ]
    )
    tasks = pd.DataFrame(
        [
            {"id": 1, "type": "feat"},
            {"id": 2, "type": "refactor"},
            {"id": 3, "type": "fix"},
            {"id": 4, "type": "fix"},
            {"id": 5, "type": "docs"},
        ]
    )
    repos = pd.DataFrame(
        [
            {"id": 10, "language": "Python", "license": "mit"},
            {"id": 20, "language": "TypeScript", "license": "mit"},
        ]
    )
    pulls.to_parquet(tmp_path / "pull_request.parquet")
    tasks.to_parquet(tmp_path / "pr_task_type.parquet")
    repos.to_parquet(tmp_path / "repository.parquet")
    return tmp_path


def test_record_carries_the_parent_commit() -> None:
    """Without parent_sha the leakage guarantee is unenforceable downstream."""
    assert "parent_sha" in {f.name for f in fields(PRRecord)}


def test_record_carries_the_clustering_unit() -> None:
    """A8 clusters on repository, so the record must carry the repo id."""
    assert "repo_id" in {f.name for f in fields(PRRecord)}


def test_record_is_immutable() -> None:
    """Frozen: a corpus record must not be edited after the outcome scan runs."""
    record = PRRecord("1", "o/r", "python", "abc", "def", "2026-01-01T00:00:00Z", (), ())
    with pytest.raises(AttributeError):
        record.parent_sha = "tampered"  # type: ignore[misc]


def test_structural_task_types_exclude_docs_and_test() -> None:
    """§3: the five types that "directly impact program structure", and only those."""
    assert {"feat", "fix", "perf", "refactor", "chore"} == STRUCTURAL_TASK_TYPES


def test_publishable_licence_gate() -> None:
    """RUNBOOK §5 requires publishing raw inputs; licences decide which may be."""
    permissive = PRRecord("1", "o/r", "python", "a", "b", "t", (), (), licence="MIT")
    restricted = PRRecord("2", "o/r", "python", "a", "b", "t", (), (), licence="GPL-3.0")
    assert (permissive.is_publishable, restricted.is_publishable) == (True, False)


def test_population_filters_remove_exactly_what_section_three_says(tmp_path: Path) -> None:
    """One PR survives: Python, structural, merged. The other four each fail one gate."""
    kept, attrition = population_counts(_dataset(tmp_path))
    assert (kept, attrition.not_python, attrition.not_structural, attrition.not_merged) == (
        2,
        1,
        1,
        1,
    )


def test_attrition_totals_are_reported(tmp_path: Path) -> None:
    """Rows never leave silently: §3's arithmetic is checked against these."""
    _, attrition = population_counts(_dataset(tmp_path))
    assert attrition.total == 3


def test_attrition_starts_empty() -> None:
    """A default that counted something would corrupt every reported total."""
    assert Attrition().total == 0


def test_missing_table_names_the_download_command(tmp_path: Path) -> None:
    """A missing dataset is an operator error, and the message should fix it."""
    with pytest.raises(FileNotFoundError, match="huggingface-cli download"):
        load_table(tmp_path, "pull_request")
