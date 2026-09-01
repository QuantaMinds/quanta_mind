"""Verification that the two convention thresholds are the numbers the reviewer ships with.

WHAT: Drives `ingest/standards/conventions.written` across `MIN_RULES` — below which a document
      is prose and is returned whole — and `MAX_CHARS`, the budget a rule list is cut to.
WHY:  **BOTH DECIDE WHAT A REVIEW IS TOLD THE TEAM'S RULES ARE, AND BOTH WERE FREELY MUTABLE.**
      `MIN_RULES` at 7 makes a short standard read as prose, so the argument is handed to the
      model instead of the rules. `MAX_CHARS` at 12001 stops bounding a document the prompt
      cannot carry. Neither mutation failed any test in any tier.

      **THE CUT IS MARKED, AND THAT IS THE POINT OF THE CAP.** Enforcing the first half of a
      standard and reporting it as the standard is worse than reading none of it, because nobody
      can see which half was applied.

      Three and six thousand are written out; a boundary phrased as `MIN_RULES - 1` reads the
      value under test and passes at any value.
IMPORTS: pytest, subprocess, quantamind.ingest.standards.conventions.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from quantamind.ingest.standards.conventions import MAX_CHARS, MIN_RULES, TRUNCATED, written

GIT_TIMEOUT_S = 30


def _repo(root: Path, files: dict[str, str]) -> Path:
    """A git repository holding `files` at HEAD. Same shape as the one in test_conventions.py."""
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
        ["commit", "--quiet", "-m", "conventions"],
    ):
        subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True, timeout=GIT_TIMEOUT_S
        )
    return root


RULES_FLOOR, CHAR_CAP = 3, 6_000


def test_the_thresholds_are_the_numbers_that_ship() -> None:
    assert MIN_RULES == RULES_FLOOR
    assert MAX_CHARS == CHAR_CAP


def test_a_document_with_exactly_three_rules_is_reduced_to_them(tmp_path: Path) -> None:
    """The boundary. At MIN_RULES = 7 the preamble and closing come back too."""
    doc = "Some preamble nobody needs.\n- one\n- two\n- three\nA closing argument.\n"
    clone = _repo(tmp_path / "three", {"AGENTS.md": doc})

    ((_, text),) = written(clone, "HEAD")

    assert text == "- one\n- two\n- three"


def test_a_document_with_two_rules_is_left_as_prose(tmp_path: Path) -> None:
    """The other side: two matches is not a list, so the document is returned whole."""
    doc = "Preamble.\n- one\n- two\nClosing.\n"
    clone = _repo(tmp_path / "two", {"AGENTS.md": doc})

    ((_, text),) = written(clone, "HEAD")

    assert "Preamble." in text and "Closing." in text


def test_a_rule_list_past_the_character_cap_is_cut_and_says_so(tmp_path: Path) -> None:
    """Rules alone can still exceed the budget, and the cut must be marked, not silent."""
    doc = "\n".join(f"- rule number {n} stated at some considerable length" for n in range(300))
    assert len(doc) > CHAR_CAP, "the fixture no longer exceeds the cap"
    clone = _repo(tmp_path / "long", {"AGENTS.md": doc})

    ((_, text),) = written(clone, "HEAD")

    assert text.endswith(TRUNCATED)
    assert len(text) == CHAR_CAP + len(TRUNCATED)
