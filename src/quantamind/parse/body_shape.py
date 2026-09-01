"""One function body, reduced to a digest that survives renaming and nothing else.

WHAT: `shapes_in(source)` returns one `Shape` per function in a module — its name, its line, how
      many statements it holds, and a digest of its normalised body.
WHY:  **"THE SAME LOGIC IS WRITTEN IN TWO PLACES, AND A FIX TO ONE LEAVES THE OTHER WRONG" IS A
      STRUCTURAL QUESTION.** Two bodies either have the same shape or they do not, and a parser
      answers that exactly and reproducibly. `AGENTS.md`: if a parser can answer it, a model must
      not. This is D2c, and it is the cheapest honest claim in the D2 family.

      **RENAME-INSENSITIVE BY ALPHA-EQUIVALENCE, NOT BY DELETING NAMES.** Every LOCAL identifier
      becomes the position of its first appearance, so `def a(x): return x + x` and
      `def b(y): return y + y` collide while `def c(y): return y + z` does not. Deleting names
      outright would make those last two identical — a different function, reported as a copy, on
      somebody's pull request.

      **API NAMES ARE KEPT AND LOCAL NAMES ARE NOT, AND THAT ASYMMETRY IS THE DESIGN.** A copied
      block gets its variables renamed; it does not get `.commit()` renamed to `.rollback()`.
      So `Attribute.attr`, `keyword.arg` and imported names are part of the shape, and
      `Name.id`, `arg.arg` and `except ... as e` are not.

      **LITERALS ARE KEPT.** `timeout=30` and `timeout=60` are not the same logic, and saying so
      would be wrong in the direction that costs a reader their trust — the first false positive
      is the last time they read the section.

      **A LEADING DOCSTRING IS STRIPPED.** Two functions written identically and documented
      differently are exactly the duplicate this exists to find. Comments need no handling: they
      are not in the AST at all, which is half the reason this is an AST digest and not a text one.

      **THE TRAVERSAL IS `iter_fields`, NOT `ast.walk`.** `walk` is breadth-first and yields
      children without their field, so `a - b` and `b - a` reach it as the same bag of nodes.
      Field order is the structure; a digest that loses it would report reordered code as copied.
IMPORTS: stdlib ast, hashlib, dataclasses; `parse.python_names.UnparseableSource`,
      because one failure type for one failure beats two spellings of it.
CONSUMED BY: `parse/duplicate_bodies.py`.
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass

from quantamind.parse.python_names import UnparseableSource

Function = ast.FunctionDef | ast.AsyncFunctionDef

# Fields holding a LOCAL name, which a copy renames freely. Aliased by first appearance.
LOCAL_NAMES: dict[type[ast.AST], tuple[str, ...]] = {
    ast.Name: ("id",),
    ast.arg: ("arg",),
    ast.ExceptHandler: ("name",),
    ast.Global: ("names",),
    ast.Nonlocal: ("names",),
}

SEPARATOR = "\x00"


@dataclass(frozen=True, slots=True)
class Shape:
    """One function, and the digest of what it does rather than what it is called."""

    name: str
    line: int
    statements: int
    """Statements in the body, docstring excluded. The floor a caller applies is over this."""

    digest: str


class _Alias:
    """First-seen order for local names. **Stateful per function, never shared across two.**

    Sharing it would make the second function's `x` alias to `v3` because the first used three
    names, so two identical bodies in one file would stop matching — the exact case this is for.
    """

    __slots__ = ("_seen",)

    def __init__(self) -> None:
        self._seen: dict[str, str] = {}

    def of(self, name: str) -> str:
        if name not in self._seen:
            self._seen[name] = f"v{len(self._seen)}"
        return self._seen[name]


def _body_without_docstring(node: Function) -> list[ast.stmt]:
    """The body, minus a leading string expression."""
    body = node.body
    if body and isinstance(body[0], ast.Expr):
        first = body[0].value
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            return body[1:]
    return body


def _tokens(node: ast.AST, alias: _Alias) -> list[str]:
    """A deterministic token stream for one node and everything under it."""
    out = [type(node).__name__]
    local = LOCAL_NAMES.get(type(node), ())
    for field, value in ast.iter_fields(node):
        out.append(f".{field}")
        if isinstance(value, list):
            # The LENGTH is emitted, so a body of two statements cannot digest the same as one
            # body holding both concatenated into a different shape.
            out.append(f"[{len(value)}")
            for item in value:
                if isinstance(item, ast.AST):
                    out.extend(_tokens(item, alias))
                elif field in local and isinstance(item, str):
                    out.append(alias.of(item))
                else:
                    out.append(repr(item))
            out.append("]")
        elif isinstance(value, ast.AST):
            out.extend(_tokens(value, alias))
        elif field in local and isinstance(value, str):
            out.append(alias.of(value))
        else:
            # Constants, attribute names, keyword names, operators. Kept verbatim: they are what
            # the code MEANS, where a local name is only what it is called here.
            out.append(repr(value))
    return out


def shape_of(node: Function) -> Shape:
    """One function's shape. The digest covers the BODY only, never the name or the signature.

    **THE NAME IS EXCLUDED ON PURPOSE.** A copied function is usually renamed, and a check that
    required the name to match would find only the duplicates nobody bothered to rename — which
    is the subset that is easiest to spot by eye and least worth reporting.
    """
    alias = _Alias()
    body = _body_without_docstring(node)
    stream = SEPARATOR.join(token for stmt in body for token in _tokens(stmt, alias))
    return Shape(
        name=node.name,
        line=node.lineno,
        statements=len(body),
        digest=hashlib.sha256(stream.encode()).hexdigest()[:16],
    )


def shapes_in(source: str) -> tuple[Shape, ...]:
    """Every function in a module, nested ones included.

    **RAISES ON A FILE THAT WILL NOT PARSE, AND THAT IS THE SECOND ATTEMPT.** The first returned
    `()` for both "this module has no functions" and "this is not Python" — so `twins()` counted
    every dataclass-only module as unparsed and reported **51 of 390 files** in this repository as
    a coverage gap. They were read perfectly; they simply define no functions.

    A wrong denominator is worse here than anywhere: the whole value of the block is that it says
    what it could not search. `parse/python_names.py` already had the right shape — the same
    `UnparseableSource`, raised for the same reason — and this now uses it.
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError) as exc:
        raise UnparseableSource(str(exc)) from None
    return tuple(
        shape_of(node)
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    )
