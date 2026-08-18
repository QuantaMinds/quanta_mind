"""Conservation, and the thing conservation alone cannot see.

WHAT: Asserts that every hunk lands in exactly one list, that an unsupported language is RECORDED
      rather than skipped, and that the parser actually resolves things.
WHY:  **Conservation is necessary and not sufficient.** A parser that resolved nothing at all would
      satisfy `units + unresolved == hunks` perfectly — every hunk unresolved, nothing lost, and a
      coverage line reporting that we read none of the change. So the resolution rate is asserted
      beside it, and the sabotage below breaks the naming pass specifically to prove the pair
      catches what neither catches alone.
IMPORTS: quantamind.parse.units, quantamind.parse.languages, quantamind.types.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.parse.languages import Depth, Language, depth_of, language_of, supported
from quantamind.parse.units import units_in
from quantamind.types.verdict import Construct, Reason

PY_DIFF = """diff --git a/pkg/pay.py b/pkg/pay.py
--- a/pkg/pay.py
+++ b/pkg/pay.py
@@ -10,6 +10,8 @@ def settle(order):
     total = order.amount
+    if order.refunded:
+        return None
@@ -40,3 +42,4 @@ class Ledger:
     def write(self, row):
+        self.rows.append(row)
"""

NO_NAME_DIFF = """diff --git a/pkg/pay.py b/pkg/pay.py
--- a/pkg/pay.py
+++ b/pkg/pay.py
@@ -1,3 +1,4 @@
 import os
+import sys
"""

RUST_DIFF = """diff --git a/src/main.rs b/src/main.rs
--- a/src/main.rs
+++ b/src/main.rs
@@ -5,3 +5,4 @@ fn main() {
     println!("hi");
+    println!("there");
"""


def test_every_hunk_lands_in_exactly_one_list() -> None:
    parsed = units_in(PY_DIFF)
    assert parsed.hunks == 2
    assert parsed.conserved(), (
        f"{parsed.hunks} hunks produced {len(parsed.units)} units and "
        f"{len(parsed.unresolved)} unresolved — a hunk vanished, and the coverage line would be "
        "computed over a list something fell out of"
    )


def test_the_parser_actually_resolves_things() -> None:
    """Conservation alone would pass a parser that resolved nothing at all."""
    parsed = units_in(PY_DIFF)
    assert len(parsed.units) == 2, f"both hunks name a declaration: {parsed.units}"
    assert [u.qualified_name for u in parsed.units] == ["def settle(order):", "class Ledger:"]


def test_a_hunk_git_could_not_name_is_recorded_not_dropped() -> None:
    parsed = units_in(NO_NAME_DIFF)
    assert parsed.conserved()
    assert len(parsed.units) == 0, "an import block has no enclosing declaration to name"
    assert parsed.unresolved[0].reason is Reason.UNPARSEABLE_SYNTAX
    assert parsed.unresolved[0].site.line == 1, "the record must point at the hunk"


def test_an_unsupported_language_is_recorded_against_the_file() -> None:
    """A silently skipped language is indistinguishable from one we read and found nothing in."""
    parsed = units_in(RUST_DIFF)
    assert parsed.conserved()
    assert len(parsed.units) == 0
    assert parsed.unresolved[0].reason is Reason.LANGUAGE_UNSUPPORTED
    assert parsed.unresolved[0].construct is Construct.FILE, "the fact is about the file"


def test_language_detection_is_by_suffix_and_never_returns_none() -> None:
    assert language_of("a/b/c.py") is Language.PYTHON
    assert language_of("a/b/c.PY") is Language.PYTHON, "suffixes are matched case-insensitively"
    assert language_of("Makefile") is Language.UNSUPPORTED, "absence must render, not vanish"


def test_depth_is_stated_separately_from_language() -> None:
    """We recognise Go and cannot read a function in it beyond the header git names."""
    assert depth_of(Language.GO) is Depth.HEADER
    assert depth_of(Language.UNSUPPORTED) is Depth.NONE
    assert Depth.EXACT not in {depth_of(lang) for lang in Language}, (
        "no language reaches EXACT: tree-sitter is not a dependency, and claiming otherwise "
        "would be the drift the publishing rules exist to catch"
    )


def test_the_supported_list_is_stable_for_the_coverage_line() -> None:
    assert supported() == sorted(supported()), "an unstable list makes the coverage line churn"
    assert "python" in supported()


def test_an_empty_diff_conserves_trivially_and_claims_nothing() -> None:
    parsed = units_in("")
    assert (parsed.hunks, parsed.units, parsed.unresolved) == (0, (), ())
    assert parsed.conserved()


MIXED_DIFF = (
    PY_DIFF
    + """diff --git a/docs/intro.rst b/docs/intro.rst
--- a/docs/intro.rst
+++ b/docs/intro.rst
@@ -1,3 +1,4 @@ Installation
 text
+more text
"""
)


def test_out_of_scope_files_are_not_reported_as_parse_failures() -> None:
    """Real output said "19 constructs could not be parsed", naming .rst and .toml files."""
    everything = units_in(MIXED_DIFF)
    assert everything.hunks == 3, "without a scope every hunk is parsed"
    assert any(u.reason is Reason.LANGUAGE_UNSUPPORTED for u in everything.unresolved), (
        "the .rst hunk is unsupported when it is in scope"
    )

    scoped = units_in(MIXED_DIFF, scope={"pkg/pay.py"})
    assert scoped.hunks == 2, "the .rst hunk was never going to be read; it is not a hunk we saw"
    assert scoped.unresolved == (), (
        "a file we do not review is not a parse failure — 'we do not review this' and 'we tried "
        f"and could not' are different facts: {scoped.unresolved}"
    )
    assert scoped.conserved()
