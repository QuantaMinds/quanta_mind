"""Verification that the anchor gate refuses a quote too short to identify anything.

WHAT: Drives `verify/anchor.locate` across the `MIN_QUOTE_CHARS` boundary and over the added-line
      parsing it depends on, asserting the derived line number rather than merely that something
      came back.
WHY:  **THIS MODULE HAD NO UNIT TEST, AND SETTING `MIN_QUOTE_CHARS` TO 0 BROKE NOTHING.** Every
      tier stayed green — `tests/unit`, `tests/property`, and `tests/live` against real
      repositories — with the gate that decides whether a model's finding is admissible at all
      switched fully off. Found by mutating every numeric constant in `src/quantamind` and
      re-running the suite: 41 of 65 constants survived both mutations, and this was the one that
      mattered most.

      **THE SHORT-QUOTE RULE IS WHAT STOPS A FINDING ANCHORING ANYWHERE.** `}` occurs in every
      file; a finding quoting it would attach to the first added line in the file and read as
      located. With the floor at 0 that is exactly what happens, and nothing said so.

      **`None` IS A REFUSAL, NOT AN ABSENCE**, per this module's own docstring, so the tests
      distinguish "refused because the quote is too short" from "refused because the quote is not
      in the diff" by asserting on the line a successful anchor derives.
IMPORTS: pytest, quantamind.verify.anchor, quantamind.types.finding.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.types.finding import Finding
from quantamind.verify.anchor import MIN_QUOTE_CHARS, added_lines, locate

DIFF = """diff --git a/src/pkg/thing.py b/src/pkg/thing.py
--- a/src/pkg/thing.py
+++ b/src/pkg/thing.py
@@ -10,3 +10,5 @@ def existing():
     unchanged_line()
+    result = compute(alpha, beta)
+    return result
     trailing_context()
"""


def _finding(quote: str, path: str = "src/pkg/thing.py") -> Finding:
    return Finding(path=path, quote=quote, claim="something is wrong here")


def test_the_floor_is_the_number_that_ships() -> None:
    """Eight, written out. The tests below are literals for the same reason.

    Phrasing a boundary test as `MIN_QUOTE_CHARS - 1` reads the value under test and moves with
    it: lowering the floor from 8 to 4 left every such test green on the first version of this
    file. Both sides of the boundary are now literal strings of known length.
    """
    assert MIN_QUOTE_CHARS == 8


def test_an_eight_character_quote_present_in_the_diff_anchors() -> None:
    """`compute(` is exactly eight characters and sits on an added line. It must resolve."""
    assert len("compute(") == 8

    located = locate(_finding("compute("), DIFF)

    assert located is not None, "a quote at the floor, present in the diff, was refused"
    assert located.line == 11, f"anchored to line {located.line}, expected 11"


def test_a_seven_character_quote_is_refused_even_though_it_is_present() -> None:
    """`compute` is seven characters and IS in the diff, so only the length rule can refuse it.

    This fails the moment the floor drops to 7 or below — which mutation showed it silently
    could, all the way to 0, with every tier of the suite still green.
    """
    assert len("compute") == 7
    assert "compute" in DIFF, "the fixture lost the short quote, so this test proves nothing"

    assert locate(_finding("compute"), DIFF) is None


def test_a_single_brace_does_not_anchor_anywhere() -> None:
    """The case the docstring names: punctuation must not attach to the first added line.

    The brace IS an added line, asserted first — so the refusal below is the length rule
    working, not the diff happening to lack the character.
    """
    tiny = "diff --git a/x b/x\n+++ b/x\n@@ -1 +1,2 @@\n+{\n"

    assert added_lines(tiny) == [("x", 1, "{")]
    assert locate(_finding("{"), tiny) is None


def test_a_long_quote_that_is_absent_is_also_refused() -> None:
    """The other refusal, so a passing anchor is not the gate simply accepting everything."""
    absent = "never_written_anywhere(gamma)"

    assert [text for _, _, text in added_lines(DIFF) if absent in text] == []
    assert locate(_finding(absent), DIFF) is None


def test_a_quote_in_another_file_does_not_anchor() -> None:
    """Path is part of the identity: the same code in a different file is a different claim."""
    assert {path for path, _, _ in added_lines(DIFF)} == {"src/pkg/thing.py"}
    assert locate(_finding("compute(alpha, beta)", path="src/pkg/other.py"), DIFF) is None


def test_indentation_alone_does_not_refuse_a_quote() -> None:
    """Whitespace is collapsed before comparing, per the module docstring."""
    located = locate(_finding("result   =    compute(alpha, beta)"), DIFF)

    assert located is not None
    assert located.line == 11


@pytest.mark.parametrize(
    ("index", "expected"),
    [
        (0, ("src/pkg/thing.py", 11, "    result = compute(alpha, beta)")),
        (1, ("src/pkg/thing.py", 12, "    return result")),
    ],
)
def test_added_lines_carries_new_file_numbers(index: int, expected: tuple[str, int, str]) -> None:
    """The line numbers `locate` derives come from here, so they are asserted directly."""
    added = added_lines(DIFF)

    assert len(added) == 2, f"parsed {len(added)} added lines, expected 2"
    assert added[index] == expected
