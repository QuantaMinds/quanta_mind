"""Call-site census: the coverage denominator.

WHAT: Counts every call site in a source file, including the ones no resolver can
      handle, and decides which are builtins and therefore excluded.
WHY:  This is the number everything else divides by, and no upstream graph tool
      emits it -- they emit edges. Get it wrong and every downstream result is
      wrong by a constant nobody can see, which is why RUNBOOK section 1.1 gates
      on an *exact* match against a hand-counted 200-line file, not an approximate
      one.

      Builtins are excluded because DyPyBench found `"abc".strip()`-class calls
      are ~59% of the apparent static-vs-dynamic gap. Counting them makes coverage
      look catastrophic and tells a developer nothing.

      Counting must never mix with resolving. If it does, the denominator quietly
      shrinks and coverage inflates -- the one bug that would make this look solved
      while being exactly wrong. Resolution lives in run_graph.py and nothing here
      imports it.
IMPORTS: phase0.syntax for the tree-sitter layer. No graph tool, ever.
CONSUMED BY: run_pipeline.py, classify_exposure.py; tests/test_census.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from phase0 import syntax

# Names PyCG structurally never emits edges for, and which a developer asking
# "who calls this?" never means. Exception constructors are included: `raise
# KeyError(k)` is a builtin call, and leaving it out inflates the denominator.
_BUILTIN_FUNCTIONS = """
abs all any bool bytes callable chr dict dir enumerate filter float format
frozenset getattr hasattr hash id input int isinstance issubclass iter len list
map max min next object open ord print range repr reversed round set setattr
sorted str sum super tuple type vars zip
"""
_BUILTIN_EXCEPTIONS = """
Exception ValueError TypeError KeyError IndexError AttributeError RuntimeError
NotImplementedError StopIteration OSError IOError ImportError ZeroDivisionError
AssertionError
"""
PYTHON_BUILTINS: frozenset[str] = frozenset((_BUILTIN_FUNCTIONS + _BUILTIN_EXCEPTIONS).split())

# str/list/dict/set methods. DyPyBench's "abc".strip() case.
_BUILTIN_METHOD_NAMES = """
append extend insert remove pop clear copy count index sort reverse keys values
items get update setdefault join split rsplit strip lstrip rstrip replace
startswith endswith lower upper title encode decode find rfind format add
discard union
"""
BUILTIN_METHODS: frozenset[str] = frozenset(_BUILTIN_METHOD_NAMES.split())

# A call on one of these receivers is builtin whatever the method is named.
LITERAL_RECEIVERS: frozenset[str] = frozenset({"string", "list", "dictionary", "set", "integer"})


@dataclass(frozen=True, slots=True)
class CallSite:
    """One syntactic call, resolved or not."""

    path: str
    line: int
    column: int
    callee_text: str  # verbatim source, e.g. 'getattr(mod, cfg["handler"])'
    callee_name: str  # trailing identifier, e.g. 'validate'; '' when computed
    enclosing: str  # dotted FQN of the containing function; module name at top level
    is_builtin: bool


def is_builtin(function_node: object, name: str) -> bool:
    """True for calls excluded from both numerator and denominator.

    A literal receiver settles it regardless of the method name -- `"a".format()`
    is builtin, `self.format()` is not, and the name alone cannot tell them apart.
    """
    node_type = getattr(function_node, "type", "")
    if node_type == "identifier":
        return name in PYTHON_BUILTINS
    if node_type == "attribute":
        if syntax.receiver_type(function_node) in LITERAL_RECEIVERS:  # type: ignore[arg-type]
            return True
        return name in BUILTIN_METHODS
    return False


def _qualify(module: str, enclosing: str) -> str:
    """PyCG-style FQN: module, or module.Class.method."""
    if module and enclosing:
        return f"{module}.{enclosing}"
    return module or enclosing


def count_call_sites(source: str, path: str = "<memory>", module: str = "") -> list[CallSite]:
    """Enumerate every call site in one file, in source order.

    Counts, and only counts. Both parenthesised calls and bare decorators are
    included: applying `@dec` invokes `dec`, and tree-sitter models the bare form
    as a plain identifier rather than a call, so it needs its own pass or it goes
    silently missing from the denominator.
    """
    root, raw = syntax.parse(source)
    sites: list[CallSite] = []

    for node in syntax.call_nodes(root):
        function_node = node.child_by_field_name("function")
        if function_node is None:
            continue
        name = syntax.callee_name(function_node, raw)
        sites.append(
            CallSite(
                path=path,
                line=node.start_point[0] + 1,
                column=node.start_point[1],
                callee_text=syntax.text(function_node, raw),
                callee_name=name,
                enclosing=_qualify(module, syntax.qualified_name(node, raw)),
                is_builtin=is_builtin(function_node, name),
            )
        )

    for decorator, inner in syntax.bare_decorators(root):
        name = syntax.callee_name(inner, raw)
        sites.append(
            CallSite(
                path=path,
                line=decorator.start_point[0] + 1,
                column=decorator.start_point[1],
                callee_text=syntax.text(inner, raw),
                callee_name=name,
                enclosing=_qualify(module, syntax.qualified_name(decorator, raw)),
                is_builtin=is_builtin(inner, name),
            )
        )

    return sorted(sites, key=lambda s: (s.line, s.column))


def non_builtin(sites: list[CallSite]) -> list[CallSite]:
    """The denominator: every call site that is not a builtin."""
    return [s for s in sites if not s.is_builtin]
