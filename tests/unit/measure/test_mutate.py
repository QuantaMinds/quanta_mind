"""Verification that the mutation sweep refuses rather than reporting a meaningless verdict.

WHAT: Drives `scripts/measure/mutate.py` over a temporary tree — its discovery, its refusals,
      the survivor verdict, and that it puts every file back.
WHY:  **A MUTATION SWEEP THAT RUNS AGAINST A RED SUITE REPORTS TOTAL COVERAGE.** Every mutation
      would be "caught", because the suite was failing before any of them was applied, and the
      output is indistinguishable from a genuinely well-covered tree. That is precisely the
      class of failure the tool was built to find, so it must not be able to commit it — the
      baseline refusal is the single most important behaviour here and is tested first.

      **AN EMPTY POPULATION IS THE SAME BUG.** A sweep that finds no constants prints "0
      survived", which reads as a clean result and is actually a broken search. Both refuse.

      **AND IT MUST PUT EVERYTHING BACK.** A mutation left on disk is a corrupted working tree
      that looks like ordinary work, so restoration is asserted by re-reading the file rather
      than assumed from the `finally`.
IMPORTS: pytest, scripts/measure/mutate.py. Nothing from `quantamind`.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "measure"))

import mutate

REFUSED = 2
SOURCE = "CAP = 15\nFLOOR = 0\nENABLED = True\nNAME = 'x'\n"


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    (tmp_path / "mod.py").write_text(SOURCE)
    return tmp_path


def test_discovery_finds_numeric_constants_only(tree: Path) -> None:
    """Bools and strings are not thresholds; `True` mutated to 0 would be a different bug."""
    found = mutate.targets_in([tree / "mod.py"])

    assert {t.name for t in found} == {"CAP", "FLOOR"}


def test_a_replacement_equal_to_the_original_is_not_emitted(tree: Path) -> None:
    """`FLOOR = 0` yields one mutation, not two. A no-op would be recorded as a survivor."""
    by_name = [t for t in mutate.targets_in([tree / "mod.py"]) if t.name == "FLOOR"]

    assert [t.new for t in by_name] == ["1"]


def test_a_red_baseline_refuses_instead_of_reporting(tree: Path, monkeypatch) -> None:
    """The failure the tool exists to find, committed by the tool itself. It must refuse."""
    monkeypatch.setattr(mutate, "suite_passes", lambda: False)

    with pytest.raises(mutate.Refused, match="fails before any mutation"):
        mutate.sweep(mutate.targets_in([tree / "mod.py"]))


def test_an_empty_population_refuses(tree: Path) -> None:
    """Nothing to mutate is not a clean sweep."""
    with pytest.raises(mutate.Refused, match="no numeric constants"):
        mutate.sweep([])


def test_a_moved_literal_refuses_rather_than_corrupting_the_file(tree: Path) -> None:
    """If the file changed under the sweep, writing at the recorded column would mangle it."""
    target = mutate.targets_in([tree / "mod.py"])[0]

    with pytest.raises(mutate.Refused, match="moved under the sweep"):
        mutate._write(target, "COMPLETELY = 'different'\n")


def test_survivors_are_named_and_the_file_is_restored(tree: Path, monkeypatch) -> None:
    """A suite that never fails means every mutation survives — and the file still comes back."""
    monkeypatch.setattr(mutate, "suite_passes", lambda: True)

    survivors, left = mutate.sweep(mutate.targets_in([tree / "mod.py"]))

    assert {t.name for t in survivors} == {"CAP", "FLOOR"}
    assert left == []
    assert (tree / "mod.py").read_text() == SOURCE


def test_a_suite_that_always_fails_reports_no_survivors(tree: Path, monkeypatch) -> None:
    """The other direction, so a passing sweep is not the tool simply never reporting."""
    calls = {"n": 0}

    def once_then_fail() -> bool:
        calls["n"] += 1
        return calls["n"] == 1  # the baseline passes, every mutation is then caught

    monkeypatch.setattr(mutate, "suite_passes", once_then_fail)

    survivors, left = mutate.sweep(mutate.targets_in([tree / "mod.py"]))

    assert survivors == []
    assert left == []
    assert (tree / "mod.py").read_text() == SOURCE


def test_the_tree_argument_is_checked(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A missing root is a refusal, not an empty sweep."""
    assert mutate.main(["mutate.py", "--all", "--root", str(tmp_path / "absent")]) == REFUSED
    assert "no tree at" in capsys.readouterr().err
