"""Reading a Python parse tree: names, scopes, and where the calls are.

WHAT: The tree-sitter layer. Owns the parser, extracts a call's callee name, the
      qualified name of the enclosing function, and the set of call nodes in a file.
WHY:  Split out of census.py, which owns a different concern: census.py decides
      what *counts* toward the denominator and what is excluded as a builtin. This
      module only answers "what does this tree say", and it is the only place that
      knows tree-sitter's node types. When the grammar version moves, exactly one
      file changes.

      `qualified_name` matters more than it looks. PyCG reports
      {caller_fqn: [callee_fqn]} with no line numbers, so the only way to match a
      call site to an edge is through the name of the function containing it. If
      this disagrees with PyCG's naming, the join in classify_exposure.py matches
      nothing and every site reads as unresolved.
IMPORTS: tree_sitter 0.26 -- Language() takes a capsule as of 0.23, and query
      execution moved to QueryCursor in 0.26. tree_sitter_python. Nothing else.
CONSUMED BY: census.py; tests/test_census.py.
"""

from __future__ import annotations

from functools import lru_cache

import tree_sitter_python as tspython
from tree_sitter import Language, Node, Parser

SCOPE_NODES = ("function_definition", "class_definition")


@lru_cache(maxsize=1)
def parser() -> Parser:
    """One parser per process. Language() takes a capsule, not an int."""
    return Parser(Language(tspython.language()))


def parse(source: str) -> tuple[Node, bytes]:
    """Parse to a root node plus the raw bytes the node offsets index into."""
    raw = source.encode("utf-8")
    return parser().parse(raw).root_node, raw


def text(node: Node, source: bytes) -> str:
    """Verbatim source for a node."""
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def callee_name(function_node: Node, source: bytes) -> str:
    """The trailing identifier of a call's function expression.

    `foo()` -> foo · `a.b.validate()` -> validate · `super().validate()` -> validate
    · `getattr(m, n)()` -> '' — no static name, which is precisely the case this
    study exists to count.
    """
    if function_node.type == "identifier":
        return text(function_node, source)
    if function_node.type == "attribute":
        attribute = function_node.child_by_field_name("attribute")
        return text(attribute, source) if attribute else ""
    return ""


def qualified_name(node: Node, source: bytes) -> str:
    """Dotted name of the function or class enclosing this node.

    Matches PyCG's convention: module-relative dotted paths, so a method inside a
    class body is `Class.method`. The module prefix is added by census.py, which
    knows the file path.
    """
    parts: list[str] = []
    current = node.parent
    while current is not None:
        if current.type in SCOPE_NODES:
            name = current.child_by_field_name("name")
            if name is not None:
                parts.append(text(name, source))
        current = current.parent
    return ".".join(reversed(parts))


def call_nodes(root: Node) -> list[Node]:
    """Every `call` node, in source order."""
    found = [n for n in _walk(root) if n.type == "call"]
    return sorted(found, key=lambda n: (n.start_point[0], n.start_point[1]))


def bare_decorators(root: Node) -> list[tuple[Node, Node]]:
    """`@dec` without parentheses, as (decorator_node, callee_node) pairs.

    Applying a decorator invokes it, so it is a call site — RUNBOOK section 1.1
    requires it counted. tree-sitter models a parenthesised `@dec()` as a normal
    `call` node, but a bare `@dec` as a plain identifier, so it needs its own pass
    or it is silently missing from the denominator.
    """
    pairs: list[tuple[Node, Node]] = []
    for node in _walk(root):
        if node.type != "decorator":
            continue
        inner = next((c for c in node.children if c.type != "@"), None)
        if inner is not None and inner.type in ("identifier", "attribute"):
            pairs.append((node, inner))
    return pairs


def receiver_type(function_node: Node) -> str:
    """Node type of an attribute call's receiver, or '' when there is none.

    `"abc".strip()` -> string. Used to recognise calls on literals, which are
    unambiguously builtin however the method is named.
    """
    if function_node.type != "attribute":
        return ""
    receiver = function_node.child_by_field_name("object")
    return receiver.type if receiver is not None else ""


def _walk(root: Node) -> list[Node]:
    """Every node in the tree."""
    found: list[Node] = []
    stack = [root]
    while stack:
        current = stack.pop()
        found.append(current)
        stack.extend(reversed(current.children))
    return found
