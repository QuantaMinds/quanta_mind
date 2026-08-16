"""Resolve a symbol the model names to the lines where it actually occurs.

WHAT: Given a function's source and an identifier the model claims is in it, returns every line
      where that identifier occurs as a name, attribute, call, argument or assignment target --
      and an empty list when it does not occur at all.
WHY:  The reviewer's dominant failure is that 87.3% of claims quote code absent from the line they
      cite: the prose and the line numbers are generated independently and nothing forces them to
      agree. Snapping the number to a statement did not help, because the number was never coupled
      to the claim. This removes the model's ability to emit a number at all -- it names a symbol,
      the parser derives the line, and a symbol that does not exist is a REJECTION rather than a
      repair.

      An empty result is a result. A finding naming a symbol absent from the shown code is exactly
      the case where the model is reasoning about something it was not given, and counting those
      measures the decoupling directly.
IMPORTS: stdlib only (ast).
CONSUMED BY: `symbol_run.py` in this package.
"""

from __future__ import annotations

import ast
import textwrap


class Unparseable(RuntimeError):
    """The unit source did not parse. NOT the same as a symbol being absent from it."""


def occurrences(source: str, symbol: str) -> list[int]:
    """Every line where `symbol` appears as an identifier; [] when genuinely absent.

    Raises Unparseable when the source cannot be parsed, so a harness failure can never be
    counted as the model naming something that does not exist.
    """
    if not symbol or not isinstance(symbol, str):
        return []
    name = symbol.strip().split(".")[-1].split("(")[0].strip("`")
    if not name.isidentifier():
        return []
    # A method's source is indented, and ast.parse raises IndentationError on it. Without the
    # dedent this returned [] for every method -- indistinguishable from "the symbol is absent",
    # which is rule 3 violated inside a harness: a failure and a real negative had the same value.
    # It read as the model naming non-existent symbols 77.8% of the time; 79.6% of funded units
    # are methods, which is where that number actually came from.
    try:
        tree = ast.parse(textwrap.dedent(source))
    except (SyntaxError, ValueError):
        raise Unparseable(f"could not parse the unit source ({len(source)} chars)") from None

    lines: set[int] = set()
    for node in ast.walk(tree):
        ln = getattr(node, "lineno", None)
        if ln is None:
            continue
        if (isinstance(node, ast.Name) and node.id == name) or (
            isinstance(node, ast.Attribute) and node.attr == name
        ):
            lines.add(ln)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == name:
                lines.add(ln)
        elif (isinstance(node, ast.arg) and node.arg == name) or (
            isinstance(node, ast.keyword) and node.arg == name
        ):
            lines.add(ln)
    return sorted(lines)


def resolve(source: str, symbol_a: str, symbol_b: str) -> dict[str, object]:
    """Derive both anchors from the parse tree, or say precisely why they could not be derived."""
    try:
        a = occurrences(source, symbol_a)
        b = occurrences(source, symbol_b)
    except Unparseable as exc:
        return {
            "line_a": None,
            "line_b": None,
            "occurrences_a": 0,
            "occurrences_b": 0,
            "missing": [],
            "resolved": False,
            "unparseable": str(exc),
        }
    missing = [s for s, hit in ((symbol_a, a), (symbol_b, b)) if not hit]
    return {
        "line_a": a[0] if a else None,
        "line_b": b[-1] if b else None,  # consequence: the last occurrence, not the first
        "occurrences_a": len(a),
        "occurrences_b": len(b),
        "missing": missing,
        "resolved": not missing,
        "unparseable": "",
    }
