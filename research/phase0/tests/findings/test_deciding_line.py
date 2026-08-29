"""Verification that no cited line is ever passed over in silence.

WHAT: Pins every outcome of `locate` — added, removed, header, absent, context-only, ambiguous,
      blank, marker-only — and that each carries a reason a human can act on.
WHY:  **THE FIRST VERSION SKIPPED WHAT IT COULD NOT EVALUATE.** A sheet citing `+++ b/path` as
      its deciding line passed the admissibility gate, produced an empty direction, and was then
      passed over by `if truth and said != truth` — so the check built to catch exactly that kind
      of sheet never fired on it, and a different gate did. Found by tracing a test that
      "passed", not by the test failing.

      **EVERY CASE HERE IS A WAY THROUGH THAT WAS OPEN.** Each asserts the specific reason and
      not merely that something was returned, because "returns a Placed" is true of the broken
      version too.
IMPORTS: pytest, phase0.findings.deciding_line.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import pytest

from phase0.findings.deciding_line import ADDED, REMOVED, is_header, locate

DIFF = """diff --git a/pkg/mod.py b/pkg/mod.py
index 1111111..2222222 100644
--- a/pkg/mod.py
+++ b/pkg/mod.py
@@ -1,4 +1,4 @@
 def keep(x):
-    return old_value
+    return new_value
     moved_line = 1
-    moved_line = 1
+    moved_line = 1
"""


def test_an_added_line_is_placed_as_added() -> None:
    got = locate("+    return new_value", DIFF)
    assert (got.direction, got.reason) == (ADDED, ""), got


def test_a_removed_line_is_placed_as_removed() -> None:
    got = locate("-    return old_value", DIFF)
    assert (got.direction, got.reason) == (REMOVED, ""), got


def test_the_marker_is_optional_on_the_cited_line() -> None:
    """A rater pasting the code without the +/- must not be treated as citing nothing."""
    assert locate("    return new_value", DIFF).direction == ADDED


@pytest.mark.parametrize(
    "header",
    [
        "+++ b/pkg/mod.py",
        "--- a/pkg/mod.py",
        "@@ -1,4 +1,4 @@",
        "diff --git a/x b/x",
        "index 1111111..2222222 100644",
    ],
)
def test_every_diff_header_is_refused_with_its_reason(header: str) -> None:
    """**THE ONE THAT GOT THROUGH.** Headers are in the diff text, so a substring test accepts
    them, and `"+++ b/x".lstrip("+")` yields `b/x`, which matches nothing and reads as merely
    unlocatable rather than as furniture.
    """
    got = locate(header, DIFF)
    assert not got.placed, got
    assert got.reason == "that is a diff header, not a line of code", got
    assert is_header(header)


def test_a_line_present_only_as_context_is_refused() -> None:
    """Unchanged context means the change did not touch it, which cannot decide a claim."""
    got = locate(" def keep(x):", DIFF)
    assert not got.placed, got
    assert "unchanged context" in got.reason, got


def test_a_line_both_added_and_removed_settles_nothing() -> None:
    """A moved block appears on both sides. Guessing a direction here would be inventing one."""
    got = locate("    moved_line = 1", DIFF)
    assert not got.placed, got
    assert "both added and removed" in got.reason, got


def test_a_line_absent_from_the_diff_is_refused() -> None:
    got = locate("+    never_written_here = 1", DIFF)
    assert not got.placed, got
    assert got.reason == "not found in the diff at all", got


@pytest.mark.parametrize("junk", ["", "   ", "\t", "`  `"])
def test_blank_and_whitespace_are_refused_with_a_reason(junk: str) -> None:
    """**GARBAGE MUST NOT PASS.** An empty cite is the cheapest way through any of these gates."""
    got = locate(junk, DIFF)
    assert not got.placed, got
    assert got.reason == "no line given", got


@pytest.mark.parametrize("marker", ["+", "-", "`+`", "  -  "])
def test_a_bare_marker_is_refused(marker: str) -> None:
    got = locate(marker, DIFF)
    assert not got.placed, got
    assert got.reason == "the line is only a marker", got


def test_every_unplaced_result_carries_a_reason() -> None:
    """A refusal with no reason is silence wearing a type, which is what rule 3 forbids."""
    expected = {
        "": "no line given",
        "+++ b/pkg/mod.py": "that is a diff header, not a line of code",
        " def keep(x):": "present only as unchanged context, so this change did not touch it",
        "    moved_line = 1": "appears as both added and removed, so it settles nothing",
        "+never_written_here = 1": "not found in the diff at all",
        "+": "the line is only a marker",
    }
    got = {cite: locate(cite, DIFF).reason for cite in expected}
    assert got == expected, got
