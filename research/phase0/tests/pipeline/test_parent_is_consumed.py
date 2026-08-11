"""`run_pipeline.one_pr` CONSUMES the record's parent. It must never re-derive one.

WHAT: Known-answer tests over a real git repository, built so that the record's parent
      and the resolver's answer are DIFFERENT commits.
WHY:  `one_pr` used to call `parent_commit.resolve` itself, passing the PR's FILE count
      where a commit count belongs and omitting the commit subjects entirely -- so A28's
      corpus-free rule never ran and the corpus-derived file rules decided every PR. It
      then overwrote a `parent_sha` the record already carried.

      A test asserting only "a parent was used" returns the same result under both
      behaviours, which is rule 14's question and the reason these fixtures are built
      the way they are: the two candidate behaviours are made to give distinguishable
      shas, and `test_the_two_answers_actually_differ` proves they do before either
      assertion below is trusted. Without it these would be green against a `one_pr`
      that had quietly gone back to resolving.
IMPORTS: GitPython, phase0.run_pipeline, phase0.parent_commit, phase0.extract_prs.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from git import Actor, Repo

from phase0 import run_pipeline
from phase0.extract_prs import PRRecord
from phase0.parent_commit import resolve

AUTHOR = Actor("Fixture", "fixture@example.com")


def _commit(repo: Repo, path: str, body: str, message: str) -> str:
    target = Path(repo.working_tree_dir or "") / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    repo.index.add([path])
    return repo.index.commit(message, author=AUTHOR, committer=AUTHOR).hexsha


def _three_commits(tmp_path: Path) -> tuple[Path, str, str, str]:
    """A -> B -> C, all touching the same file. Returns (path, A, B, C)."""
    clone = tmp_path / "repo"
    clone.mkdir()
    repo = Repo.init(clone, initial_branch="main")
    first = _commit(repo, "acme/a.py", "# one\n", "chore: seed")
    second = _commit(repo, "acme/a.py", "# two\n", "feat: middle")
    third = _commit(repo, "acme/a.py", "# three\n", "feat: change target")
    repo.close()
    return clone, first, second, third


def _record(parent_sha: str, merged_sha: str) -> PRRecord:
    return PRRecord(
        pr_id="1",
        repo="acme/acme",
        language="python",
        parent_sha=parent_sha,
        merged_sha=merged_sha,
        merged_at="2026-03-01T12:00:00Z",
        changed_files=("acme/a.py",),
        changed_symbols=("target",),
        repo_id="acme/acme",
        parent_resolution_method="squash",
        parent_resolution_rule="subject_sequence",
    )


def test_the_two_answers_actually_differ(tmp_path: Path) -> None:
    """The premise the other tests rest on, asserted rather than assumed.

    If the resolver happened to return the same sha the record names, every assertion
    below would pass under either behaviour and prove nothing.
    """
    clone, first, second, third = _three_commits(tmp_path)
    resolved = resolve(clone, third, frozenset({"acme/a.py"}), 1)
    assert resolved.parent_sha == second
    assert resolved.parent_sha != first


def test_one_pr_checks_out_the_recorded_parent(tmp_path: Path, monkeypatch) -> None:
    """The record names A; the resolver would say B. The checkout must go to A."""
    clone, first, second, third = _three_commits(tmp_path)
    asked: list[str] = []

    class _Nothing:
        def __enter__(self) -> None:
            return None

        def __exit__(self, *exc: object) -> None:
            return None

    def _spy(clone_path: Path, sha: str, slot: str):  # type: ignore[no-untyped-def]
        asked.append(sha)
        return _Nothing()

    monkeypatch.setattr(run_pipeline.worktree, "at_commit", _spy)
    run_pipeline.one_pr(clone, _record(first, third), 0, 30)

    assert asked == [first], f"checked out {asked}, not the recorded parent {first}"
    assert second not in asked, "the resolver's answer was used instead of the record's"


def test_an_absent_parent_is_a_typed_failure_not_a_recomputation(
    tmp_path: Path, monkeypatch
) -> None:
    """No parent on the record is malformed input, and must fail as such.

    Re-deriving one here is what the old code did, and it turns a corrupt record into a
    plausible measurement -- the failure mode this whole file guards.
    """
    clone, _first, _second, third = _three_commits(tmp_path)
    asked: list[str] = []

    def _spy(clone_path: Path, sha: str, slot: str):  # type: ignore[no-untyped-def]
        asked.append(sha)
        raise AssertionError("a worktree was opened for a record with no parent")

    monkeypatch.setattr(run_pipeline.worktree, "at_commit", _spy)
    audit = run_pipeline.one_pr(clone, _record("", third), 0, 30)

    assert audit.stage_failed == "parent_commit"
    assert asked == []
    assert not audit.succeeded


def test_the_resolution_travels_from_the_record_onto_the_audit(tmp_path: Path, monkeypatch) -> None:
    """Method AND rule are copied, not recomputed. Empty would mean UNRECORDED."""
    clone, first, _second, third = _three_commits(tmp_path)

    def _fails(clone_path: Path, sha: str, slot: str):  # type: ignore[no-untyped-def]
        raise RuntimeError("clone gone")

    monkeypatch.setattr(run_pipeline.worktree, "at_commit", _fails)
    audit = run_pipeline.one_pr(clone, _record(first, third), 0, 30)

    assert audit.parent_resolution_method == "squash"
    assert audit.parent_resolution_rule == "subject_sequence"


@pytest.mark.parametrize("field_name", ["parent_resolution_method", "parent_resolution_rule"])
def test_an_older_record_reads_as_unrecorded_not_as_a_verdict(
    tmp_path: Path, monkeypatch, field_name: str
) -> None:
    """A records file written before these fields must not acquire one by default."""
    clone, first, _second, third = _three_commits(tmp_path)
    older = PRRecord(
        pr_id="1",
        repo="acme/acme",
        language="python",
        parent_sha=first,
        merged_sha=third,
        merged_at="2026-03-01T12:00:00Z",
        changed_files=("acme/a.py",),
        changed_symbols=("target",),
        repo_id="acme/acme",
    )

    def _fails(clone_path: Path, sha: str, slot: str):  # type: ignore[no-untyped-def]
        raise RuntimeError("clone gone")

    monkeypatch.setattr(run_pipeline.worktree, "at_commit", _fails)
    audit = run_pipeline.one_pr(clone, older, 0, 30)

    assert getattr(audit, field_name) == ""
