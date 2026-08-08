"""Re-scan targeting, and the double-count it would cause if the journal were naive.

WHAT: Asserts `choose` drops done-markers for its own targets and keeps them for
      everything else, refuses an unknown name, and that a second block for a
      repository supersedes the first rather than adding to it.
WHY:  The eight repositories a re-scan exists for are exactly the ones whose FIRST
      journal block says `clone_failed`. If `read_attempts` returned both blocks, the
      re-scan would reinstate the very attrition it removed, in the arm that decides
      A16's confounder -- and the run would still look like it worked.

      The unknown-name test guards the other direction: skipping a typo walks nothing,
      exits 0, and reports a re-scan that did not happen.
IMPORTS: phase0.pilot.targets, phase0.pipeline.journal, phase0.pilot.attempt, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0.pilot.attempt import Attempt
from phase0.pilot.targets import choose
from phase0.pipeline import journal, resume

POPULATION = ["a/one", "b/two", "c/three"]


def _attempt(repo: str, pr_id: str, admitted: bool, stage: str) -> Attempt:
    return Attempt(
        pr_id=pr_id,
        repo=repo,
        admitted=admitted,
        stage=stage,
        category="resource" if stage else "",
        commit_count=1,
        corpus_py_files=1,
        derived_files=1 if admitted else 0,
        changed_symbols=1 if admitted else 0,
        stars=500,
        outcome="clean" if admitted else "",
        base_on_default="yes",
        merge_on_base="yes",
        changed_lines=10,
    )


def test_a_plain_run_takes_the_first_n_and_honours_every_marker(tmp_path: Path) -> None:
    path = tmp_path / "j.md"
    journal.append_repo(path, "a/one", [_attempt("a/one", "1", True, "")])
    targets = choose(POPULATION, path, repos=2)
    assert targets.chosen == ["a/one", "b/two"] and targets.already == {"a/one"}


def test_a_rescan_drops_its_own_markers_and_keeps_the_others(tmp_path: Path) -> None:
    """The whole point of the flag: walk these again, resume everything else."""
    path = tmp_path / "j.md"
    journal.append_repo(path, "a/one", [_attempt("a/one", "1", False, "clone_failed")])
    journal.append_repo(path, "b/two", [_attempt("b/two", "2", True, "")])
    targets = choose(POPULATION, path, repos=99, only_repo=["a/one"], rescan_reason="r")
    assert targets.chosen == ["a/one"] and targets.already == {"b/two"}


def test_a_name_outside_the_population_is_refused_not_skipped(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="typo/nope"):
        choose(POPULATION, tmp_path / "j.md", repos=1, only_repo=["typo/nope"], rescan_reason="r")


def test_a_rescan_supersedes_the_failed_block_rather_than_adding_to_it(tmp_path: Path) -> None:
    """Read back the real file: one row per PR, and it is the later one."""
    path = tmp_path / "j.md"
    journal.append_repo(path, "a/one", [_attempt("a/one", "1", False, "clone_failed")])
    journal.append_repo(
        path, "a/one", [_attempt("a/one", "1", True, "")], rescan="rescan: blob_none_A29"
    )

    read = resume.read_attempts(path)
    assert len(read) == 1
    assert read[0].admitted is True and read[0].stage == ""
    # Superseded, not deleted -- the failure is still on disk as A29's evidence.
    assert path.read_text(encoding="utf-8").count("clone_failed") == 1
    assert "rescan: blob_none_A29" in path.read_text(encoding="utf-8")
