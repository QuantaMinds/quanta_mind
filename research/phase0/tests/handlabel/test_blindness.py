"""Verification that the sheet cannot leak an answer to the labeller.

WHAT: Pins the structural guarantees on the evidence side — no import path from the
      sheet or the window walker to a verdict, no per-commit annotation derived from
      the classifier's pattern, and an unreadable window that refuses to be labelled.
WHY:  §7's gate is the one measurement in Phase 0 whose validity depends entirely on
      the order two things happen in, and order is not something a green test usually
      checks. These check it by making the leak impossible rather than discouraged.
IMPORTS: ast, pytest, phase0.handlabel.{sheet,window,select}, phase0.{fix_signals,scan_outcome}.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from phase0 import fix_signals, scan_outcome
from phase0.handlabel import sheet as sheet_module
from phase0.handlabel import window as window_module
from phase0.handlabel.select import Candidate, Selection
from phase0.handlabel.sheet import render_sheet
from phase0.handlabel.window import Window, WindowCommit, unavailable

FORBIDDEN = {"scan_outcome", "fix_signals"}


def _imported_modules(module_path: Path) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


@pytest.mark.parametrize("module", [sheet_module, window_module])
def test_no_import_path_to_a_verdict(module: object) -> None:
    """The guarantee is structural: the code that decides is not reachable from here.

    Both modules, because the split into `sheet` and `window` would otherwise let the
    banned import reappear in the half the test stopped looking at.

    If this ever fails, the fix is to remove the import, never to relax the test — the
    sheet's whole value is that it cannot render an answer even by accident.
    """
    imported = _imported_modules(Path(str(module.__file__)))
    leaked = {name for name in imported if any(bad in name for bad in FORBIDDEN)}
    assert leaked == set()


def test_the_window_constant_tracks_the_scanner() -> None:
    """Restated rather than imported, so it must be pinned or it will drift."""
    assert window_module.WINDOW_DAYS == scan_outcome.WINDOW_DAYS


def _candidate(index: int) -> Candidate:
    return Candidate(
        pr_id=1000 + index,
        repo="acme/widget",
        number=index,
        merged_at="2025-03-01T00:00:00Z",
        title=f"change {index}",
        commit_shas=("a" * 40,),
        changed_files=("acme/widget.py",),
    )


def _selection(count: int = 20) -> Selection:
    return Selection(
        candidates=tuple(_candidate(i) for i in range(1, count + 1)),
        population=count * 3,
        stride=3,
        manifest_sha256="deadbeef",
    )


def test_no_commit_is_annotated_from_its_message() -> None:
    """The leak that matters: marking WHICH commits look like fixes.

    An earlier version of this test asserted the sheet contained none of the regex's
    vocabulary at all, and it failed on the sheet's own instructions — correctly. §3.2
    defines the outcome as a revert-or-fix, and a labeller who is not told that is
    labelling a different variable, so the comparison would be meaningless. The words
    have to be in the prose.

    What must never appear is a per-commit verdict. Two commits, one whose message
    matches the classifier's pattern and one that does not, must render to byte-identical
    structure — same lines, same markers, differing only in the message and sha.
    """
    matching = "hotfix: repair the regression this introduced"
    plain = "add a paragraph to the readme"
    assert fix_signals.mentions_breakage(matching) and not fix_signals.mentions_breakage(plain)

    def shape(message: str) -> list[str]:
        commit = WindowCommit("f" * 40, "2025-03-02T00:00:00+00:00", "Dev", message, ())
        rendered = render_sheet(_selection(1), {1001: Window(commits=(commit,))})
        return [line for line in rendered.splitlines() if message not in line]

    assert shape(matching) == shape(plain)


def test_an_unreadable_window_is_not_offered_for_labelling() -> None:
    """The bug this package shipped with, pinned.

    Thirteen of thirteen clones failed and the sheet rendered twenty quiet weeks. A
    labeller marks those clean, the classifier returns CLEAN on unreadable history for
    its own reasons, and the gate reports 20/20 PASS on no data whatsoever.
    """
    rendered = render_sheet(_selection(1), {1001: unavailable("clone failed")})
    assert "HISTORY UNAVAILABLE — DO NOT LABEL" in rendered
    assert "broke / clean" not in rendered  # no label prompt is offered
    assert "1 of 1 PRs have unreadable history" in rendered


def test_a_quiet_week_and_an_unreadable_repo_render_differently() -> None:
    """The distinction is the whole point; assert it survives at the rendered level."""
    quiet = render_sheet(_selection(1), {1001: Window(commits=())})
    broken = render_sheet(_selection(1), {1001: unavailable("clone failed")})
    assert "No commits landed in the window" in quiet
    assert "DO NOT LABEL" not in quiet
    assert quiet != broken


def test_a_missing_window_is_treated_as_unreadable_not_as_quiet() -> None:
    """A caller bug must fail loudly rather than default to an empty week."""
    rendered = render_sheet(_selection(1), {})
    assert "DO NOT LABEL" in rendered
