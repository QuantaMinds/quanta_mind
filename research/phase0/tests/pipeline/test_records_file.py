"""Verification that a persisted record is either complete or absent, never half-built.

WHAT: Asserts the round trip, and that a record missing a field the later stages depend on
      is refused rather than reconstructed with defaults.
WHY:  The refusal is the point. `PRRecord.base_ref` defaults to `""`, and a record read
      back with an empty `base_ref` would send the outcome scan to the clone's HEAD --
      which is the defect the whole corpus was re-measured to remove. A reader that fills
      defaults would reintroduce it silently, one layer below where it was fixed, which is
      exactly how it survived the first time.

      A torn final line is expected rather than exceptional: records are appended as each
      is built so a killed run keeps everything already written, and the cost of a kill
      mid-write must be one record and not the file.
IMPORTS: phase0.pipeline.records_file, phase0.extract_prs.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

from phase0.extract_prs import PRRecord
from phase0.pipeline import records_file


def _record(pr_id: str = "1", base_ref: str = "main") -> PRRecord:
    return PRRecord(
        pr_id=pr_id,
        repo="o/r",
        language="python",
        parent_sha="a" * 40,
        merged_sha="b" * 40,
        merged_at="2026-03-01T12:00:00Z",
        changed_files=("pkg/mod.py",),
        changed_symbols=("f",),
        base_ref=base_ref,
    )


def test_a_record_round_trips_with_its_tuples_intact(tmp_path: Path) -> None:
    """JSON has no tuples, and the later stages take frozensets of these fields."""
    path = tmp_path / "records.jsonl"
    records_file.append(path, _record())

    back = records_file.read(path)

    assert len(back) == 1
    assert back[0] == _record()
    assert isinstance(back[0].changed_files, tuple)


def test_a_record_without_a_base_ref_is_refused(tmp_path: Path) -> None:
    """The one field whose default is actively dangerous.

    An empty `base_ref` reads back as a record the outcome scan will walk from HEAD, which
    scored 15.5% of the corpus CLEAN. Skipping it loses one PR; reconstructing it with a
    default loses the finding.
    """
    path = tmp_path / "records.jsonl"
    records_file.append(path, _record(base_ref=""))

    assert records_file.read(path) == []


def test_a_torn_final_line_costs_one_record_not_the_file(tmp_path: Path) -> None:
    """Records are appended as they are built, so a kill mid-write is the normal case."""
    path = tmp_path / "records.jsonl"
    records_file.append(path, _record("1"))
    records_file.append(path, _record("2"))
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"pr_id": "3", "repo": "o/r", "merged')

    back = records_file.read(path)

    assert [r.pr_id for r in back] == ["1", "2"]


def test_ids_lets_a_restart_skip_what_is_already_built(tmp_path: Path) -> None:
    path = tmp_path / "records.jsonl"
    records_file.append(path, _record("1"))
    records_file.append(path, _record("2"))

    assert records_file.ids(path) == {"1", "2"}


def test_a_missing_file_is_empty_not_an_error(tmp_path: Path) -> None:
    """The first run has no file, and that is not a failure."""
    assert records_file.read(tmp_path / "nothing.jsonl") == []
    assert records_file.ids(tmp_path / "nothing.jsonl") == set()
