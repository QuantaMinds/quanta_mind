"""The four drifts that were live in the plan this morning, each required to fail the guard.

WHAT: Builds a miniature project -- a plan document and a `src/quantamind/` tree -- and runs
      `check_stage_table.main()` over it end to end. One case per rule, plus the honest version
      which must pass, plus the two false positives the first draft produced.
WHY:  **The guard was written after the drift, so nothing proves it would have caught it.** These
      cases are the actual text that was in `docs/plans/implementation.md`: `rank/order.py` "still
      to come" while it sat on disk, and the retrospective marked "not begun" while
      `quantamind retrospective` was live-tested.

      **Driven through `main()`, not through the helpers.** A regression test in this repository was
      written against `_finds()` in isolation while the fault lived at the call site, and it passed
      against the broken code. The unit a guard fails or passes on is a whole document.

      **The honest case matters as much as the four failures.** A guard that fires on everything is
      one people disable, and the first draft of this one condemned five rows of an unrelated
      three-column table before it was scoped to the summary table by its header.
IMPORTS: scripts/guard/records/check_stage_table.py. No product imports.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "guard" / "records"))

from check_stage_table import main  # noqa: E402

HONEST_ROW = "| **the retrospective** | **STARTED** | `serve/retrospective.py` built |"
HONEST_STEP = "1. **DONE.** `serve/retrospective.py` — walk closed pull requests."


def _run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    row: str = HONEST_ROW,
    step: str = HONEST_STEP,
    heading: str = "# Stage — The retrospective  ·  STARTED",
    with_stage: bool = True,
) -> int:
    """A one-stage project whose `serve/retrospective.py` genuinely exists.

    **`with_stage=False` IS THE CASE THAT SHIPPED WRONG.** The real plan carried seven summary
    rows and six stage sections, and the row without a section was the one that was false: rule 3
    reads a stage's STEPS, so a row nothing else describes was checked on its evidence cell alone.
    """
    package = tmp_path / "src" / "quantamind" / "serve"
    package.mkdir(parents=True)
    (package / "retrospective.py").write_text("x = 1\n", encoding="utf-8")
    plan = tmp_path / "docs" / "plans" / "implementation.md"
    plan.parent.mkdir(parents=True)
    plan.write_text(
        "| stage | status | evidence |\n"
        "|---|---|---|\n"
        f"{row}\n"
        "\n"
        "| unrelated | three | columns |\n"
        "|---|---|---|\n"
        "| **a gate** | **MET** | not a stage status at all |\n"
        "\n" + (f"{heading}\n\n### Steps\n\n{step}\n" if with_stage else ""),
        encoding="utf-8",
    )
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    return main()


def test_the_honest_plan_passes_and_an_unrelated_table_is_not_condemned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The second table's `**MET**` is a gate result, not a stage status.

    **The counts are asserted, not just the exit code.** A guard that matched no summary row and no
    stage section would also return 0, and would go on returning 0 after someone renamed the header
    it keys on -- passing for the reason that means it checked nothing. Ask what the check prints
    when the thing it checks is broken: without this line, the same 0.
    """
    assert _run(tmp_path, monkeypatch) == 0
    printed = capsys.readouterr().out
    assert "1 summary row(s), 1 stage section(s)" in printed, (
        f"the guard returned 0 without finding the row and stage it was given: {printed!r}"
    )


def test_an_absence_claim_about_a_module_that_exists_is_caught(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The exact wording that was live: 'still to come' about a file on disk."""
    row = "| **the retrospective** | **STARTED** | `serve/retrospective.py` still to come |"
    assert _run(tmp_path, monkeypatch, row=row) == 1
    assert "still to come" in capsys.readouterr().out


def test_a_done_step_naming_a_missing_module_is_caught(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    step = "1. **DONE.** `serve/never_written.py` — walk closed pull requests."
    assert _run(tmp_path, monkeypatch, step=step) == 1
    assert "no such file" in capsys.readouterr().out


def test_a_stage_called_not_begun_whose_modules_all_exist_is_caught(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`render` and `the retrospective` both sat here while shipping."""
    row = "| **the retrospective** | not begun | — |"
    code = _run(tmp_path, monkeypatch, row=row, heading="# Stage — The retrospective  ·  not begun")
    assert code == 1
    assert "marked not begun" in capsys.readouterr().out


def test_a_stage_naming_no_module_is_a_violation_rather_than_a_silent_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Unverifiable must not read as verified. This is how two stages went unchecked for months."""
    step = "1. **DONE.** Walk closed pull requests and rank each one."
    assert _run(tmp_path, monkeypatch, step=step) == 1
    assert "names no module" in capsys.readouterr().out


def test_a_heading_disagreeing_with_its_summary_row_is_caught(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Three places record one state; the plan had 'NEXT' in one and 'STARTED' in another."""
    assert _run(tmp_path, monkeypatch, heading="# Stage — The retrospective  ·  DONE") == 1
    assert "the summary row says" in capsys.readouterr().out


def test_a_row_marked_not_begun_is_caught_even_with_no_stage_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """**THE DRIFT RULE 3 COULD NOT SEE — issue #96.**

    `the reviewer — allocate, infer, verify` sat at NOT BEGUN in the real plan while `allocate/`,
    `infer/` and `verify/` all held modules. It had no stage section, so rule 3 -- which reads a
    stage's steps -- never ran for it, and `_check_claims` is only ever handed the evidence cell.
    The status cell was compared against the STATUSES vocabulary and nothing else.
    """
    row = "| **the retrospective** | **NOT BEGUN** | `serve/retrospective.py` is the replay |"
    assert _run(tmp_path, monkeypatch, row=row, with_stage=False) == 1
    out = capsys.readouterr().out
    assert "says NOT BEGUN" in out, f"the status cell was not checked: {out!r}"
    assert "serve/retrospective.py" in out, "the violation must name the module that exists"


def test_a_row_marked_not_begun_whose_module_is_absent_is_honest_and_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """**THE OTHER DIRECTION, OR THE RULE IS JUST A BAN ON THE WORDS.** A stage genuinely not
    begun must still be allowed to say so."""
    row = "| **the retrospective** | **NOT BEGUN** | `serve/never_written.py` will replay |"
    assert _run(tmp_path, monkeypatch, row=row, with_stage=False) == 0, (
        "an honest NOT BEGUN row was condemned"
    )
    assert "1 summary row(s), 0 stage section(s)" in capsys.readouterr().out
