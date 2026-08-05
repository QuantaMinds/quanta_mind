"""Verification of the orchestrator: ordering, checkpointing, isolation, leakage.

WHAT: Asserts the loop's five operational properties and the one structural
      guarantee — that the exposure pass cannot see outcomes.
WHY:  Each property was chosen because getting it wrong costs a re-run of a
      multi-day job, and none of them fails loudly:

      - Ordering is deterministic, so a partial run is a PREFIX of the full run
        and pilot results are comparable with full results rather than being two
        arbitrary samples.
      - The checkpoint is append-only and consulted on restart. A crash at hour 28
        should cost one PR, not the run.
      - One malformed PR must produce a record with a status, never abort the
        loop, and the record must name WHICH stage failed.
      - RunSummary carries no arm counts, so a pilot cannot surface an effect size
        before the controls have cleared.
      - run_pipeline must never import the outcome layer: if exposure could see
        outcomes, `PHASE0_RUNBOOK.md` “Exposure classifier tests” leakage becomes possible by
        accident. The rule is paired with a test that proves it can still fail.
IMPORTS: phase0.run_pipeline, phase0.pipeline.record, phase0.extract_prs, pytest.
CONSUMED BY: `just test-phase0`. No network: the clone step is substituted.
"""

from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import fields
from pathlib import Path

from phase0 import run_pipeline
from phase0.extract_prs import PRRecord
from phase0.pipeline import record


def _pr(pr_id: str, repo: str, files: tuple[str, ...] = ("acme/a.py",)) -> PRRecord:
    return PRRecord(
        pr_id=pr_id,
        repo=repo,
        language="python",
        parent_sha="",
        merged_sha="0" * 40,
        merged_at="2026-03-01T12:00:00Z",
        changed_files=files,
        changed_symbols=("target",),
        repo_id=repo,
    )


def _imported_modules(module: object) -> set[str]:
    """Every `from X import ...` target in a module's source."""
    tree = ast.parse(inspect.getsource(module))  # type: ignore[arg-type]
    return {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    }


def test_pipeline_cannot_see_outcomes() -> None:
    """Exposure must be computable without knowing whether the PR broke anything.

    This named `phase0.scan_outcome` until that module became the `phase0.outcome`
    package. The name it forbade then referred to nothing, so the assertion could not
    fail and the isolation it protects was unguarded -- run_pipeline could have imported
    `phase0.outcome.scan` and this test would still have been green.
    """
    leaked = {name for name in _imported_modules(run_pipeline) if name.startswith("phase0.outcome")}

    assert leaked == set()


def test_the_leak_rule_can_actually_fail() -> None:
    """The rule above is quiet. This is what proves it is quiet for the right reason.

    `handlabel/draw.py` genuinely imports the outcome layer, so the same rule applied to
    it must fire. Without this, a prefix that matched nothing -- another rename, a typo --
    would read exactly like isolation holding.
    """
    # importlib, not `from phase0.handlabel import draw`: that binds the FUNCTION named
    # draw, whose source contains no imports at all -- the rule then reads as isolation
    # holding on a module that is not even being looked at.
    draw = importlib.import_module("phase0.handlabel.draw")

    leaked = {name for name in _imported_modules(draw) if name.startswith("phase0.outcome")}

    assert leaked == {
        "phase0.outcome.conclusion",
        "phase0.outcome.scan",
        "phase0.outcome.window",
    }


def test_grouping_is_deterministic_and_sorted() -> None:
    """A partial run must be a prefix of the full run, not an arbitrary sample."""
    prs = [_pr("3", "z/z"), _pr("1", "a/a"), _pr("2", "a/a"), _pr("4", "m/m")]
    grouped = run_pipeline.group_by_repo(prs)
    assert list(grouped) == ["a/a", "m/m", "z/z"]


def test_prs_within_a_repo_are_ordered_by_id() -> None:
    prs = [_pr("22", "a/a"), _pr("11", "a/a"), _pr("33", "a/a")]
    assert [p.pr_id for p in run_pipeline.group_by_repo(prs)["a/a"]] == ["11", "22", "33"]


def test_failure_record_names_the_stage() -> None:
    """'PR 4821 failed' is useless at hour 30 of a run."""
    audit = run_pipeline.failed(_pr("1", "a/a"), "parent_commit", "ambiguous merge shape")
    assert (audit.stage_failed, audit.succeeded) == ("parent_commit", False)


def test_checkpoint_round_trips_completed_ids(tmp_path: Path) -> None:
    """Restart must skip what is done, or a reboot costs the whole run."""
    out = tmp_path / "exposure.jsonl"
    record.append(out, run_pipeline.failed(_pr("7", "a/a"), "clone", "gone"))
    record.append(out, run_pipeline.failed(_pr("9", "a/a"), "clone", "gone"))
    assert record.completed_ids(out) == {"7", "9"}


def test_truncated_final_line_is_skipped_not_fatal(tmp_path: Path) -> None:
    """A crash mid-write leaves a partial line; that PR is redone, not the run."""
    out = tmp_path / "exposure.jsonl"
    record.append(out, run_pipeline.failed(_pr("7", "a/a"), "clone", "gone"))
    with out.open("a", encoding="utf-8") as handle:
        handle.write('{"pr_id": "8", "repo": "a/a"')  # no newline, no closing brace
    assert record.completed_ids(out) == {"7"}


def test_clone_failure_records_every_pending_pr(tmp_path: Path, monkeypatch) -> None:
    """An unreachable repository is attrition for each of its PRs, not a crash."""

    def _explode(repo_full_name: str, workspace: Path, keep: bool = False):
        raise run_pipeline.worktree.CloneFailed(f"{repo_full_name}: gone")

    monkeypatch.setattr(run_pipeline.worktree, "cloned", _explode)
    out = tmp_path / "exposure.jsonl"
    summary = run_pipeline.run([_pr("1", "a/a"), _pr("2", "a/a")], out, tmp_path / "ws")
    assert (summary.clone_failures, summary.prs_recorded) == (2, 2)


def test_completed_prs_are_skipped_on_restart(tmp_path: Path, monkeypatch) -> None:
    """The second run must do no work for a PR already on disk."""

    def _explode(repo_full_name: str, workspace: Path, keep: bool = False):
        raise run_pipeline.worktree.CloneFailed("gone")

    monkeypatch.setattr(run_pipeline.worktree, "cloned", _explode)
    out = tmp_path / "exposure.jsonl"
    prs = [_pr("1", "a/a"), _pr("2", "a/a")]
    run_pipeline.run(prs, out, tmp_path / "ws")
    second = run_pipeline.run(prs, out, tmp_path / "ws")
    assert (second.prs_skipped, second.prs_recorded) == (2, 0)


def test_summary_carries_no_effect_size() -> None:
    """A pilot must not be able to surface a ratio before the controls clear."""
    names = {f.name for f in fields(run_pipeline.RunSummary)}
    assert names == {
        "prs_seen",
        "prs_recorded",
        "prs_skipped",
        "clone_failures",
        "stage_failures",
    }


def test_audit_record_carries_the_fields_that_cannot_be_added_later() -> None:
    """Every one of these means re-running the corpus if it is missing."""
    names = {f.name for f in fields(record.PRAudit)}
    required = {
        "parent_resolution_method",
        "no_static_callee_sites",
        "graph_status",
        "graph_detail_line",
        "duration_ms",
        "provenance",
        "stage_failed",
    }
    assert required <= names


def test_provenance_is_stamped_on_every_record() -> None:
    """If half the corpus is re-run after a fix, this is how you know which half."""
    audit = run_pipeline.failed(_pr("1", "a/a"), "clone", "gone")
    stamped = {f.name for f in fields(audit.provenance)}
    assert stamped == {
        "pycg_version",
        "tree_sitter_version",
        "python_version",
        "pipeline_git_sha",
    }
