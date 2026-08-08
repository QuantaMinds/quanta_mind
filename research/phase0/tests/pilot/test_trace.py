"""The run record is written per repository, timestamped, and self-contained.

WHAT: That `RunTrace` flushes a timeline line per event, a full snapshot per repository,
      and a running shape -- and that a snapshot can be read without the journal.
WHY:  The journal lets a run RESUME; it cannot say why one died. It has no clock and no
      running totals, so "it slowed after repository 40" is not a statement anyone can
      make from it. A thirty-hour run that fails at hour twenty-eight is the case this
      exists for, and a record that only lands at the end is no record at all.

      So the assertions are about what is on disk MID-run, after one repository, not
      about what a finished run produces.
IMPORTS: phase0.pilot.{attempt,trace}, stdlib json/pathlib.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import json
from pathlib import Path

from phase0.pilot.attempt import Attempt
from phase0.pilot.trace import RunTrace


def _attempt(pr_id: str, admitted: bool, outcome: str = "") -> Attempt:
    return Attempt(
        pr_id=pr_id,
        repo="a/b",
        admitted=admitted,
        stage="" if admitted else "no_python",
        category="" if admitted else "restricted",
        commit_count=1,
        corpus_py_files=1,
        derived_files=1 if admitted else 0,
        changed_symbols=1 if admitted else 0,
        stars=742,
        outcome=outcome,
        base_on_default="yes",
        arm="OpenAI_Codex",
    )


def test_one_finished_repository_leaves_a_readable_record(tmp_path: Path) -> None:
    """Everything a diagnosis needs, on disk, before the run is over."""
    trace = RunTrace(tmp_path, {"arm": "agent", "population": 3566})
    rows = [_attempt("1", True, "broke"), _attempt("2", False)]
    trace.repo_done("a/b", 1, 30, rows, rows, clone_failures=0, started=trace.stamp())

    # Sharded in blocks of ten: repository 1 lands in `001-010`, not loose in `repos/`.
    snapshot = json.loads((tmp_path / "repos" / "001-010" / "001_a__b.json").read_text())
    assert snapshot["repo"] == "a/b"
    assert (snapshot["attempts"], snapshot["admitted"], snapshot["broke"]) == (2, 1, 1)
    assert snapshot["arms"] == ["OpenAI_Codex"]
    assert snapshot["rejected_by_stage"] == {"no_python": 1}
    # Self-contained: the rows are here in full, so no journal is needed to read it.
    assert [r["pr_id"] for r in snapshot["rows"]] == ["1", "2"]
    assert snapshot["started_utc"] <= snapshot["finished_utc"]

    shape = json.loads((tmp_path / "shape_latest.json").read_text())
    assert shape["repos_finished"] == 1
    assert shape["shape"]["records_built"] == 1
    assert shape["shape"]["outcome_broke"] == 1
    assert shape["trace_write_errors"] == []


def test_the_timeline_is_flushed_per_event_not_at_the_end(tmp_path: Path) -> None:
    """A buffered timeline loses exactly the lines describing the crash."""
    trace = RunTrace(tmp_path, {"arm": "agent"})
    trace.event("repo_start", repo="a/b", position=1)
    trace.event("clone_failed", repo="a/b", error="timeout after 600s")

    lines = [json.loads(x) for x in (tmp_path / "timeline.jsonl").read_text().splitlines()]
    assert [x["kind"] for x in lines] == ["run_start", "repo_start", "clone_failed"]
    assert lines[2]["error"] == "timeout after 600s"
    # Every line carries the one clock, in order.
    assert [x["ts"] for x in lines] == sorted(x["ts"] for x in lines)


def test_snapshots_shard_so_no_directory_exceeds_the_fan_out_cap(tmp_path: Path) -> None:
    """A full run walks hundreds of repositories; one directory would bury them all."""
    trace = RunTrace(tmp_path, {"arm": "agent"})
    rows = [_attempt("1", True, "clean")]
    for position in (1, 10, 11, 25):
        trace.repo_done(f"a/r{position}", position, 30, rows, rows, 0, trace.stamp())

    shards = sorted(p.name for p in (tmp_path / "repos").iterdir())
    assert shards == ["001-010", "011-020", "021-030"]
    assert (tmp_path / "repos" / "001-010" / "010_a__r10.json").is_file()
    assert (tmp_path / "repos" / "011-020" / "011_a__r11.json").is_file()
    assert max(len(list(p.iterdir())) for p in (tmp_path / "repos").iterdir()) <= 15
