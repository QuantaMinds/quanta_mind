"""Verification that every import becomes a labelled value, and none becomes silence.

WHAT: Pins each outcome `parse/imports.edges` can produce, and that `RESOLVED` requires the
      target to be a file in the tree rather than merely a name that parses.
WHY:  Rule 2 forbids an unlabelled edge and rule 3 forbids untyped silence. An import resolver
      is where both are easiest to break: the tempting shape is a list of strings, where a name
      we could not place and a name we chose not to look at are the same absence.

      **THE TWO-RESOLVER RULE IS SABOTAGED, NOT ASSERTED.** `RESOLVED` is the only confidence
      that may be published as fact, so a test that only checks the happy path would pass on an
      implementation that marked everything RESOLVED — which is exactly the failure worth
      catching, because it publishes guesses as facts.
IMPORTS: pytest, quantamind.parse.imports, quantamind.types.verdict.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.parse.imports import Edge, edges
from quantamind.types.verdict import Confidence, Construct, Provenance, Reason

TREE = frozenset({"a/b.py", "a/__init__.py", "a/pkg/__init__.py", "a/pkg/mod.py", "app.py"})


def _only(source: str, path: str = "app.py") -> tuple[tuple[Edge, ...], tuple[object, ...]]:
    return edges(path, source, TREE)


def test_an_absolute_import_of_a_tree_file_is_resolved() -> None:
    """Both resolvers agree: the syntax names it and the file is there."""
    found, missed = _only("from a.b import thing\n")
    assert missed == (), missed
    assert [(e.module, e.target, e.confidence) for e in found] == [
        ("a.b", "a/b.py", Confidence.RESOLVED)
    ], found


def test_a_plain_import_of_a_tree_file_is_resolved() -> None:
    found, _ = _only("import a.b\n")
    assert [(e.module, e.target) for e in found] == [("a.b", "a/b.py")], found


def test_a_package_import_resolves_to_its_init() -> None:
    """`from a.pkg import x` depends on `a/pkg/__init__.py` whether or not `x` is a module."""
    found, _ = _only("from a.pkg import mod\n")
    assert ("a/pkg/mod.py", Confidence.RESOLVED) in [(e.target, e.confidence) for e in found]


def test_a_third_party_name_is_unresolved_not_absent() -> None:
    """**AN ABSENCE HERE WOULD READ AS 'THIS FILE IMPORTS NOTHING'.**"""
    found, missed = _only("import requests\n")
    assert found == (), found
    assert [(m.reason, m.construct) for m in missed] == [
        (Reason.EXTERNAL_SYMBOL, Construct.IMPORT)
    ], missed


def test_a_relative_import_we_cannot_place_is_inferred_not_resolved() -> None:
    """A relative import is internal by definition, so it is an edge — just not a named one.

    One resolver agrees (the syntax says an intra-package import exists); the other cannot name
    the file. That is precisely `INFERRED`, and calling it `RESOLVED` would publish a guess.
    """
    found, missed = edges("a/pkg/mod.py", "from .other import thing\n", TREE)
    assert missed == (), missed
    assert [(e.target, e.confidence) for e in found] == [("", Confidence.INFERRED)], found


def test_a_relative_climb_above_the_root_is_malformed_not_external() -> None:
    _, missed = edges("a/pkg/mod.py", "from ..... import thing\n", TREE)
    assert [m.reason for m in missed] == [Reason.MALFORMED_DECLARATION], missed


def test_a_dynamic_import_is_named_rather_than_missed_silently() -> None:
    """The dangerous edge is the invisible one, so `importlib` is reported as its own reason."""
    _, missed = _only("import importlib\nm = importlib.import_module('x')\n")
    assert Reason.DYNAMIC_DISPATCH in [m.reason for m in missed], missed


def test_a_file_that_will_not_parse_is_not_a_file_with_no_imports() -> None:
    found, missed = _only("def (:\n")
    assert found == (), found
    assert [(m.reason, m.construct) for m in missed] == [
        (Reason.UNPARSEABLE_SYNTAX, Construct.FILE)
    ], missed


def test_every_edge_carries_a_provenance_and_it_is_the_parser() -> None:
    """Rule 2: never an unlabelled edge. A model cannot be wrong about any of these."""
    found, _ = _only("from a.b import thing\nimport a.b\n")
    assert found, "expected edges to label"
    assert {e.provenance for e in found} == {Provenance.PARSER}, found
    assert all(e.confidence is not None for e in found)


def test_nothing_resolves_against_an_empty_tree() -> None:
    """**THE TWO-RESOLVER RULE, AS AN ASSERTION.** The syntax is identical; only the tree changed.

    An implementation that marked edges RESOLVED from the syntax alone passes every test above
    and fails this one, which is the whole point of the rule.
    """
    found, missed = edges("app.py", "from a.b import thing\n", frozenset())
    assert [e.confidence for e in found] == [], f"resolved against an empty tree: {found}"
    assert [m.reason for m in missed] == [Reason.EXTERNAL_SYMBOL], missed


def test_a_from_import_of_a_third_party_package_is_external_not_inferred() -> None:
    """**THE SHAPE THAT SLIPPED THROUGH.** `import requests` was handled; `from requests import`
    was not, and came back INFERRED — an edge asserted inside the tree to a package outside it.
    Only a dotted (relative) import is internal by definition.
    """
    found, missed = _only("from requests import get\n")
    assert found == (), f"claimed an internal edge to a third-party package: {found}"
    assert [m.reason for m in missed] == [Reason.EXTERNAL_SYMBOL], missed
