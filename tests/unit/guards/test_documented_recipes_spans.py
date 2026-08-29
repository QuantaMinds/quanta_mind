"""The recipe guard must not read a command across the gap between two backtick spans.

WHAT: Runs `check_documented_recipes.main()` end to end over a fixture project -- a justfile with
      one recipe, a CLI with one registered subcommand, and a CONTRIBUTING.md -- and asserts on
      the exit code and the violations it prints.
WHY:  The guard scanned a line as `" ".join(BACKTICKED.findall(line))`, joining every code span
      before matching, so `quantamind` followed by `just` followed by `docs/engineering/CLI.md`
      produced the commands `quantamind just` and `just docs`. Neither appears in any span. It
      reported them against correct prose and cost a red build on a pointer sentence.

      **THESE TESTS GO THROUGH `main()`, NOT THROUGH THE HELPER THAT SPLITS THE SPANS.** An
      earlier draft exercised `_finds` with spans it built itself; restoring the join at the call
      site left it green, because the join is in `main()` and the test never went near it. It
      would have shipped as a regression test for a fault it could not see. The whole path --
      file on disk, line, spans, match, violation -- is what has to be covered, because the whole
      path is where the fault lived.

      The last test pins the OLD behaviour as a known answer: joining the spans DOES manufacture
      `just docs`. Reintroducing the join fails there with the reason attached.
IMPORTS: the guard under test, loaded from scripts/guard/records. Nothing from src/.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "guard" / "records"))

from check_documented_recipes import BACKTICKED, JUST_CALL, QM_CALL, main  # noqa: E402

# The sentence that broke it: three spans, the middle two adjacent across ordinary prose.
POINTER = (
    "Every command -- `quantamind` and `just` alike -- is documented in "
    "`docs/engineering/CLI.md` with its syntax."
)


def _run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prose: str) -> int:
    """Scan a one-document project whose justfile has `fixtures` and whose CLI has `config`."""
    (tmp_path / "justfile").write_text("fixtures:\n    echo pinned\n", encoding="utf-8")
    cli = tmp_path / "src" / "quantamind" / "serve" / "cli.py"
    cli.parent.mkdir(parents=True)
    cli.write_text(
        'UNBUILT: dict[str, str] = {"serve": "not built"}\n'
        'sub.add_parser("config")\n'
        'sub.add_parser("serve")\n',
        encoding="utf-8",
    )
    (tmp_path / "CONTRIBUTING.md").write_text(prose, encoding="utf-8")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    return main()


def test_adjacent_spans_do_not_synthesise_a_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The fault, end to end: correct prose must not produce a violation."""
    code = _run(tmp_path, monkeypatch, POINTER)
    output = capsys.readouterr().out

    assert code == 0, f"correct prose was reported as a violation:\n{output}"
    assert "just docs" not in output, "a recipe was read across the gap between two spans"
    assert "quantamind just" not in output, "a subcommand was read across the gap between spans"


def test_a_command_inside_one_span_is_still_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A fix that stops the guard matching anything is not a fix."""
    code = _run(tmp_path, monkeypatch, "Run `just fixtures`, then `quantamind config`.\n")
    output = capsys.readouterr().out

    assert code == 0, output
    assert "2 documented invocation(s) checked" in output, output


def test_an_unknown_command_inside_one_span_is_still_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The guard's actual job, unchanged: a command that does not exist is a violation."""
    code = _run(tmp_path, monkeypatch, "Run `just nope` and `quantamind nope` first.\n")
    output = capsys.readouterr().out

    assert code == 1, output
    assert "`just nope` names no recipe" in output, output
    assert "`quantamind nope` is not a registered subcommand" in output, output


def test_joining_the_spans_is_what_produced_the_phantom() -> None:
    """Known answer for the OLD behaviour, so the join cannot come back unnoticed."""
    spans = BACKTICKED.findall(POINTER)
    assert len(spans) == 3, f"the fixture must have three spans to be meaningful, got {spans}"
    joined = " ".join(spans)

    recipe = JUST_CALL.search(joined)
    command = QM_CALL.search(joined)
    assert recipe is not None and recipe.group("recipe") == "docs", (
        f"joining no longer manufactures `just docs` from {joined!r}; if the spans or the "
        f"patterns changed, this test is no longer pinning the fault it was written for"
    )
    assert command is not None and command.group("command") == "just"
