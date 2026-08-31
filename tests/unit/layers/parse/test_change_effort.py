"""How big each changed file is, where to look inside it, and what must never be guessed.

WHAT: Drives `parse.change_effort.effort()` over diffs this file writes, and pins the two holes a
      live run opened in the first version.
WHY:  **THIS IS PUBLISHED ON A CUSTOMER'S PULL REQUEST, SO A WRONG NUMBER COSTS MORE THAN NO
      NUMBER.** The block exists because a list of eighty-two bare paths told a reviewer nothing
      about where to spend their time; it earns that only if every figure on it is right.

      **TWO DEFECTS CAME OUT OF RUNNING IT AND BOTH ARE PINNED BELOW.** Summing
      `ChangedUnit.lines_added` scored nothing for a file git named no declaration in, so **every
      brand-new file showed no size at all** — silently, and new files are the biggest ones in a
      change. And git's funcname heuristic offered `WHY: **A COMMENT CAN BE SCROLLED PAST...`, a
      line of module docstring, as the place to look.

      **DROPPING A LOCATION IS RIGHT; GUESSING ONE IS NOT.** An omitted declaration costs a reader
      nothing. A wrong one sends them to the wrong place with our confidence attached.
IMPORTS: quantamind.parse.change_effort.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.parse.change_effort import effort

EDITED = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -10,3 +10,4 @@ def handle(request):
 keep
-    old = 1
+    new = 2
+    other = 3
@@ -40,2 +42,3 @@ class Job:
+    done = True
"""

NEW_FILE = """diff --git a/src/fresh.py b/src/fresh.py
new file mode 100644
--- /dev/null
+++ b/src/fresh.py
@@ -0,0 +1,3 @@
+one
+two
+three
"""

PROSE_HEADER = """diff --git a/src/mod.py b/src/mod.py
--- a/src/mod.py
+++ b/src/mod.py
@@ -3,2 +3,3 @@ WHY:  **A COMMENT CAN BE SCROLLED PAST; A REQUIRED CHECK CANNOT.**
+added
"""


def test_a_file_reports_its_added_and_removed_lines() -> None:
    """The number a reviewer calibrates against. Four changed lines, not two hunks."""
    got = effort(EDITED, ["src/app.py"])["src/app.py"]

    assert (got.added, got.removed) == (3, 1)
    assert got.lines == 4


def test_a_brand_new_file_reports_its_size() -> None:
    """**THE HOLE A LIVE RUN OPENED.** A new file's first hunk header names no declaration, so
    summing per-unit counts scored it zero — and new files are the largest in a change."""
    got = effort(NEW_FILE, ["src/fresh.py"])["src/fresh.py"]

    assert (got.added, got.removed) == (3, 0)
    assert got.functions == ()
    assert got.render() == "3 lines"


def test_file_headers_are_not_counted_as_content() -> None:
    """`+++ b/path` and `--- a/path` start with the same characters as an added and a removed
    line. Counting them adds one to every file in the change."""
    assert effort(NEW_FILE, ["src/fresh.py"])["src/fresh.py"].added == 3


def test_a_declaration_is_reported_when_git_named_one() -> None:
    """Where to look, in git's own words — the same string GitHub shows on its hunk headers."""
    got = effort(EDITED, ["src/app.py"])

    assert got["src/app.py"].functions == ("def handle(request):", "class Job:")
    assert "`def handle(request):`" in got["src/app.py"].render()


def test_a_docstring_line_is_not_reported_as_a_place_to_look() -> None:
    """**THE OTHER LIVE DEFECT.** git takes the nearest line matching a pattern, which inside a
    module docstring is prose. The size still reports; only the location is withheld."""
    got = effort(PROSE_HEADER, ["src/mod.py"])["src/mod.py"]

    assert got.functions == ()
    assert got.render() == "1 line"


def test_a_path_outside_the_scope_is_absent() -> None:
    """The caller names what it intends to review. Reporting on the rest would describe files the
    reviewer was never shown."""
    assert effort(EDITED, ["src/other.py"]) == {}


def test_a_file_with_no_parsed_hunk_has_no_entry_rather_than_a_zero() -> None:
    """A pure rename changed no line. "0 lines" beside it is a wrong statement where saying
    nothing is a quiet one, and the renderer omits the annotation entirely."""
    rename = "diff --git a/src/a.py b/src/b.py\nrename from src/a.py\nrename to src/b.py\n"

    assert effort(rename, ["src/b.py"]) == {}


def test_one_line_is_singular() -> None:
    """Trivial, and the kind of thing that reaches a customer's pull request unnoticed."""
    assert effort(PROSE_HEADER, ["src/mod.py"])["src/mod.py"].render() == "1 line"
