"""What a Python file calls, imports and defines, with the line each was on.

WHAT: `names_in(source)` returns `Names(calls, imports, defined)`, every entry a `Mention` carrying
      the dotted name and its line. `UnparseableSource` when the file will not parse.
WHY:  **THIS IS THE HALF OF A RULE CHECK A PARSER CAN ANSWER EXACTLY.** Every example violation the
      competition demonstrates -- a forbidden call, a banned import, a naming convention -- is a
      question about names in a syntax tree, not a judgement about intent. Answering them with a
      model would make each one 66.7-82.1% wrong and, worse, unrepeatable: an audit row is worth
      reading only if re-running the check on the same commit gives the same answer.

      **A SYNTAX ERROR RAISES RATHER THAN RETURNING EMPTY NAMES.** A file that will not parse has
      no calls we can see, and an empty `Names` is indistinguishable from a file that genuinely
      calls nothing -- which would report a violating file as compliant. That is the failure this
      product exists to refuse, so the caller is forced to decide what an unreadable file means.

      **DOTTED NAMES ARE RECONSTRUCTED, NOT MATCHED ON THE LAST SEGMENT.** A rule forbidding
      `subprocess.run` must not fire on `runner.run`, and one forbidding `os.system` must not miss
      `os.system(...)` because the check only looked at `system`. Attribute chains are walked to
      their root.
IMPORTS: stdlib `ast` only. Nothing from the product.
CONSUMED BY: `verify/rule_check.py`.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass


class UnparseableSource(SyntaxError):
    """The file is not valid Python. A RESULT for the caller to classify, never an empty answer."""


@dataclass(frozen=True, slots=True)
class Mention:
    """One name and where it appeared. The line is what a violation points a developer at."""

    name: str
    line: int


@dataclass(frozen=True, slots=True)
class Names:
    """Everything a rule can be checked against, in one pass over the tree."""

    calls: tuple[Mention, ...] = ()
    imports: tuple[Mention, ...] = ()
    defined: tuple[Mention, ...] = ()


def _dotted(node: ast.expr) -> str:
    """`a.b.c` from an attribute chain, or `""` for anything that is not a plain name.

    A call on a subscript or a call result -- `handlers[0]()`, `factory()()` -- has no static
    dotted name. Empty is the honest answer and matches no rule, rather than a partial name that
    would match the wrong one.
    """
    parts: list[str] = []
    current: ast.expr = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return ""
    parts.append(current.id)
    return ".".join(reversed(parts))


def names_in(source: str) -> Names:
    """Parse `source` and collect its calls, imports and definitions."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError) as exc:
        raise UnparseableSource(str(exc)) from None

    calls: list[Mention] = []
    imports: list[Mention] = []
    defined: list[Mention] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _dotted(node.func)
            if name:
                calls.append(Mention(name, node.lineno))
        elif isinstance(node, ast.Import):
            imports.extend(Mention(alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            # `from a.b import c` is recorded as `a.b.c`, so a rule may forbid either the module
            # or the symbol without needing two ways to say it. A relative import has no module.
            root = node.module or ""
            for alias in node.names:
                imports.append(Mention(f"{root}.{alias.name}" if root else alias.name, node.lineno))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            defined.append(Mention(node.name, node.lineno))
    return Names(tuple(calls), tuple(imports), tuple(defined))
