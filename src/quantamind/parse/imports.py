"""Every import one file declares, each labelled with how well we resolved it.

WHAT: `edges(path, source, in_tree)` returns the import edges a file declares and an `Unresolved`
      record for every import it declares that we could not turn into an edge.
WHY:  **THIS IS A DETECTOR, NOT A REVIEWER.** "This module is imported by fourteen others" is a
      question a parser answers exactly. `verify/pin_mismatch.py` is the same shape and fires 24
      of 24 with precision 100% by construction, while model findings on the same corpus are
      66.7-82.1% wrong and no gate removes any of them. Nothing here consults a model, so no
      model can be wrong about it.

      **`RESOLVED` NEEDS TWO INDEPENDENT RESOLVERS AND HAS THEM HERE:** the syntax says the import
      exists, AND the named target is a file in the tree. Either alone is `INFERRED`. That is rule
      2, and it is the difference between "this file imports that file" and "this file mentions a
      name that looks like that file".

      **NO BRANCH RETURNS NOTHING.** An import we cannot place comes back as `Unresolved` with the
      reason and the construct, never as an absence -- rule 3. An empty edge list therefore means
      "no static Python import resolved to a file in this tree", never "nothing depends on this",
      and a caller rendering it as the latter is stating something this module did not check.

      **PURE: NO GIT, NO I/O, NO NETWORK.** The caller supplies the source and the set of paths in
      the tree. `parse/importers.py` does the git reading and answers the reverse question per
      file; this answers the forward one and is testable without a repository.
IMPORTS: stdlib `ast`, plus `types.verdict`. Leftward only.
CONSUMED BY: tests/unit/layers/parse/test_import_edges.py; `store/` once D2b lands.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from quantamind.types.verdict import Confidence, Construct, Provenance, Reason, Site, Unresolved

# The module through which a dynamic import is made. An argument to it is not a name we can read.
DYNAMIC = "importlib"


@dataclass(frozen=True, slots=True)
class Edge:
    """One file importing another, with how sure we are and what produced the claim."""

    importer: str
    """The path declaring the import."""

    module: str
    """The module as written in the source, before resolution."""

    target: str
    """The path in the tree this resolves to. Empty only when `confidence` is INFERRED."""

    line: int
    confidence: Confidence
    provenance: Provenance = Provenance.PARSER
    """Always PARSER here, and stated rather than defaulted at the call site: rule 2 forbids an
    unlabelled edge, and a field a caller may omit is a field a caller will omit."""


def _candidates(module: str) -> tuple[str, ...]:
    """The paths a dotted module name could name, most specific first.

    A name resolves to a module file or to a package's `__init__`, and both are real. Returning
    both rather than guessing is what lets the caller's tree membership decide.
    """
    stem = module.replace(".", "/")
    return (f"{stem}.py", f"{stem}/__init__.py")


def _resolve(module: str, in_tree: frozenset[str]) -> str:
    """The path in the tree this module names, or empty. The SECOND resolver."""
    for candidate in _candidates(module):
        if candidate in in_tree:
            return candidate
    return ""


def _absolute(node: ast.ImportFrom, path: str) -> str:
    """A relative import resolved against the importing file's own package.

    `from . import x` inside `a/b.py` means `a.x`; `from ..c import y` means the package above.
    Returns empty when the climb goes above the tree root, which is a malformed declaration
    rather than an external one.
    """
    parts = path.split("/")[:-1]
    climb = (node.level or 0) - 1
    if climb > len(parts):
        return ""
    base = parts[: len(parts) - climb] if climb else parts
    tail = node.module.split(".") if node.module else []
    return ".".join([*base, *tail])


def _dynamic(tree: ast.Module, path: str) -> list[Unresolved]:
    """Every `importlib` call. **Named, because an invisible edge is the dangerous kind.**"""
    out: list[Unresolved] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        named = getattr(func, "attr", None) or getattr(func, "id", None)
        root = getattr(getattr(func, "value", None), "id", None)
        if root == DYNAMIC or (named == "import_module" and root is None):
            out.append(
                Unresolved(
                    site=Site(path=path, line=node.lineno),
                    reason=Reason.DYNAMIC_DISPATCH,
                    construct=Construct.IMPORT,
                )
            )
    return out


def edges(
    path: str, source: str, in_tree: frozenset[str]
) -> tuple[tuple[Edge, ...], tuple[Unresolved, ...]]:
    """The import edges `source` declares, and every import that did not become one."""
    try:
        tree = ast.parse(source)
    except SyntaxError as broken:
        # A file that will not parse is not a file with no dependencies.
        return (), (
            Unresolved(
                site=Site(path=path, line=broken.lineno or 1),
                reason=Reason.UNPARSEABLE_SYNTAX,
                construct=Construct.FILE,
            ),
        )

    found: list[Edge] = []
    missed: list[Unresolved] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            named = [(alias.name, node.lineno) for alias in node.names]
            relative = False  # a plain `import x` has no package to resolve against
        elif isinstance(node, ast.ImportFrom):
            absolute = _absolute(node, path) if node.level else (node.module or "")
            if not absolute:
                missed.append(
                    Unresolved(
                        site=Site(path=path, line=node.lineno),
                        reason=Reason.MALFORMED_DECLARATION,
                        construct=Construct.IMPORT,
                    )
                )
                continue
            # `from a.b import c` may name a module `a.b.c` OR a symbol `c` inside `a.b`.
            named = [(f"{absolute}.{a.name}", node.lineno) for a in node.names]
            named.append((absolute, node.lineno))
            # **ONLY A DOTTED IMPORT IS INTERNAL BY DEFINITION.** This read `True` for every
            # `ImportFrom`, so `from requests import get` came back INFERRED -- an edge claimed
            # inside the tree to a third-party package. `import requests` was unaffected, so the
            # obvious test passed.
            relative = bool(node.level)
        else:
            continue

        placed = False
        for module, line in named:
            target = _resolve(module, in_tree)
            if target:
                found.append(Edge(path, module, target, line, Confidence.RESOLVED))
                placed = True
        if placed:
            continue
        module, line = named[-1]
        if relative:
            # The package resolved but the imported name did not: one resolver agrees, the other
            # cannot tell a submodule from a re-exported symbol. That is INFERRED, not absent.
            found.append(Edge(path, module, "", line, Confidence.INFERRED))
        else:
            missed.append(
                Unresolved(
                    site=Site(path=path, line=line),
                    reason=Reason.EXTERNAL_SYMBOL,
                    construct=Construct.IMPORT,
                )
            )

    missed.extend(_dynamic(tree, path))
    return tuple(found), tuple(missed)
