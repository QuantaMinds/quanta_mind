"""Verification that `--json` emits JSON on every path a review can end on.

WHAT: Runs the real `review` code path against real git repositories and parses stdout as JSON
      in each of the three outcomes: a ranked review, a change in no language we read, and a
      clean tree.
WHY:  Two early exits printed a human sentence to stdout and returned 0 regardless of `--json`.
      A tool got a decode error and an exit code of success, so a developer whose change touched
      only Markdown saw exactly what a developer with a broken install saw. `render/json_report.py`
      carried a comment promising the opposite -- *"ONE OBJECT ON STDOUT AND NOTHING ELSE"* --
      which is a comment asserting a property the code did not have.

      **THE TEST PARSES, IT DOES NOT GREP.** Asserting that stdout contains `not_reviewed_because`
      would pass on the prose-plus-a-substring version. `json.loads` is the assertion, because
      the defect was that stdout was not JSON.

      **AND IT PINS THE KEYS ACROSS OUTCOMES.** A consumer that must branch on which shape it
      got is back to parsing prose; the point of the reason being a value is that the envelope
      does not change.
IMPORTS: pytest, quantamind.serve.commands.run_commit, quantamind.types.unreviewed.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from quantamind.serve.commands.run_commit import review_commit
from quantamind.types.review import NotReviewed

GIT_TIMEOUT_S = 30
ENVELOPE = {
    "schema",
    "origin",
    "not_reviewed_because",
    "files",
    "history",
    "findings",
    "rule_checks",
    "verdicts",
}


def _repo(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    for args in (
        ["init", "--quiet", "-b", "main"],
        ["config", "user.email", "t@example.com"],
        ["config", "user.name", "t"],
        ["add", "-A"],
        ["commit", "--quiet", "-m", "one"],
    ):
        subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True, timeout=GIT_TIMEOUT_S
        )
    return root


def _json_of(clone: Path, capsys: pytest.CaptureFixture[str]) -> dict[str, object]:
    """Run the real path and parse stdout. The parse IS the assertion."""
    code = review_commit(clone, "t/t", "", as_json=True)
    out = capsys.readouterr().out
    assert code == 0, out
    try:
        return dict(json.loads(out))
    except json.JSONDecodeError as broken:  # pragma: no cover - only on the defect returning
        pytest.fail(f"--json did not emit JSON ({broken}); stdout was:\n{out}")


def test_a_change_in_no_language_we_read_still_emits_json(tmp_path, capsys) -> None:
    """The common case for a docs-only or config-only change, and the one that was broken."""
    clone = _repo(tmp_path / "a", {"kept.py": "x = 1\n"})
    (clone / "NOTES.md").write_text("# just prose\n", encoding="utf-8")
    got = _json_of(clone, capsys)
    assert got["not_reviewed_because"] == NotReviewed.NO_SUPPORTED_LANGUAGE.value, got
    files = dict(got["files"])  # type: ignore[arg-type]
    assert files["changed"] == ["NOTES.md"], files
    assert files["reviewed"] == [], files
    # Everything that changed went unread. The residual is the product on this path too.
    assert files["unread"] == ["NOTES.md"], files


def test_a_clean_tree_still_emits_json(tmp_path, capsys) -> None:
    """Nothing pending is a real answer, and must not read as a crash to a tool."""
    clone = _repo(tmp_path / "b", {"kept.py": "x = 1\n"})
    got = _json_of(clone, capsys)
    assert got["not_reviewed_because"] == NotReviewed.NOTHING_PENDING.value, got


def test_a_ranked_review_reports_no_reason(tmp_path, capsys) -> None:
    """The key is present and null when a ranking ran, never absent."""
    clone = _repo(tmp_path / "c", {"kept.py": "x = 1\n"})
    (clone / "added.py").write_text("def go() -> None:\n    return None\n", encoding="utf-8")
    got = _json_of(clone, capsys)
    assert got["not_reviewed_because"] is None, got
    assert "added.py" in dict(got["files"])["changed"], got  # type: ignore[arg-type]


def test_the_envelope_is_identical_across_all_three_outcomes(tmp_path, capsys) -> None:
    """A consumer that has to branch on the shape is back to parsing prose."""
    clean = _repo(tmp_path / "d", {"kept.py": "x = 1\n"})
    prose = _repo(tmp_path / "e", {"kept.py": "x = 1\n"})
    (prose / "NOTES.md").write_text("# prose\n", encoding="utf-8")
    ranked = _repo(tmp_path / "f", {"kept.py": "x = 1\n"})
    (ranked / "added.py").write_text("def go() -> None:\n    return None\n", encoding="utf-8")

    shapes = [set(_json_of(c, capsys)) for c in (clean, prose, ranked)]
    assert shapes[0] == shapes[1] == shapes[2] == ENVELOPE, shapes


def test_every_reason_has_a_distinct_sentence_and_value() -> None:
    """A member added without either would raise at the moment a human or a tool needed it.

    Distinctness is the point: two reasons sharing a sentence tell a reader the same thing
    about two different states, which is the collapse this enum exists to prevent.
    """
    sentences = {reason: reason.sentence() for reason in NotReviewed}
    assert sentences == {
        NotReviewed.NOTHING_PENDING: "nothing to review",
        NotReviewed.NO_SUPPORTED_LANGUAGE: "none in a language we read",
    }, sentences
    values = [reason.value for reason in NotReviewed]
    assert values == ["nothing_pending", "no_supported_language"], values


def test_the_slash_command_names_only_keys_the_review_actually_emits(tmp_path, capsys) -> None:
    """**THE DRIFT A WRAPPER EXISTS TO CREATE.** `.claude/commands/qm-review.md` tells an agent
    which keys to read. If `json_report.py` renames one, the command keeps instructing the agent
    to read a key that is gone -- and an agent reading a missing key reports an empty review
    rather than failing, which is the silent version of the defect this file already covers.
    """
    command = Path(".claude/commands/qm-review.md")
    if not command.is_file():  # pragma: no cover - only when run from another directory
        pytest.skip("run from the repository root; the command file is path-relative")

    clone = _repo(tmp_path / "g", {"kept.py": "x = 1\n"})
    (clone / "added.py").write_text("def go() -> None:\n    return None\n", encoding="utf-8")
    got = _json_of(clone, capsys)

    text = command.read_text(encoding="utf-8")

    # **CHECKED IN BOTH DIRECTIONS, BECAUSE ONE DIRECTION ALONE GETS WEAKER WHEN BROKEN.**
    # The first version only validated whatever keys the file happened to name, so renaming
    # `files.unread` in the command removed it from the check and passed. A filter that admits
    # less when the thing it guards is broken is not a check -- AGENTS.md rule 14.
    # `files` itself is not required by name: the command names `files.reviewed` and
    # `files.unread`, which is what an agent actually reads. Requiring the bare key would fail
    # a correct command file, which is a check being wrong in the safe direction but still wrong.
    required_top = {"not_reviewed_because", "history", "findings"}
    unnamed = {k for k in required_top if f"`{k}`" not in text}
    assert not unnamed, f"the command must tell an agent to read these, and does not: {unnamed}"

    required_files = {"reviewed", "unread"}
    unnamed_files = {k for k in required_files if f"`files.{k}`" not in text}
    assert not unnamed_files, f"the command must name these files.* keys: {unnamed_files}"

    # And every key it names must actually be emitted, which is the other direction.
    named_top = {k for k in ENVELOPE if f"`{k}`" in text}
    missing = named_top - set(got)
    assert not missing, (
        f"the command tells an agent to read keys the review does not emit: {missing}"
    )
    absent = required_files - set(dict(got["files"]))  # type: ignore[arg-type]
    assert not absent, f"the review does not emit files.* keys the command names: {absent}"


def test_the_slash_command_does_not_advertise_the_suppressed_flag() -> None:
    """`serve/cli.py` hides `--deep` because the product publishes no model findings.

    A command file turning it on would be that drift with a friendlier entry point, so the
    prohibition is checked rather than trusted to whoever edits the file next.
    """
    command = Path(".claude/commands/qm-review.md")
    if not command.is_file():  # pragma: no cover
        pytest.skip("run from the repository root; the command file is path-relative")
    invocations = [
        line
        for line in command.read_text(encoding="utf-8").splitlines()
        if "quantamind review" in line
    ]
    assert invocations, "the command file invokes nothing"
    assert not any("--deep" in line for line in invocations), invocations
