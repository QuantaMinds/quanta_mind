"""Map a unified diff's changed lines onto the enclosing Python functions, exactly.

WHAT: Parses each changed file with `ast` and returns the functions whose line range contains a
      line the patch added or modified, together with that function's full source text.
WHY:  The cost measurement needs the real prompt, and the product's prompt is "the ranked
      function and its immediate context, not the whole diff". Estimating from patch size
      understates it; estimating from whole files overstates it badly -- one file here is 969k
      characters. It also avoids the defect that voided an earlier measurement: git's default
      funcname heuristic attributes a hunk to the nearest line starting in column 0, which in
      Python is `class`, not `def`. `ast` has no such ambiguity.
IMPORTS: stdlib only (ast, re).
CONSUMED BY: `cost.py` in this package. Nothing in `src/`.
"""

from __future__ import annotations

import ast
import re

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.MULTILINE)


def touched_lines(patch: str) -> set[int]:
    """Post-image line numbers the patch adds or modifies."""
    out: set[int] = set()
    for m in HUNK.finditer(patch):
        start = int(m.group(1))
        body = patch[m.end() :]
        nxt = HUNK.search(body)
        if nxt:
            body = body[: nxt.start()]
        line = start
        for raw in body.split("\n"):
            if raw.startswith("+"):
                out.add(line)
                line += 1
            elif raw.startswith("-"):
                continue
            else:
                line += 1
    return out


def changed_units(source: str, patch: str) -> list[dict[str, object]]:
    """Functions and methods containing a touched line, innermost first.

    Returns [] when the file does not parse -- a syntax error is a result, not a crash, and the
    caller counts them so a silent drop cannot be mistaken for a file with no changed units.
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    lines = source.split("\n")
    hit = touched_lines(patch)
    if not hit:
        return []

    found: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        lo = node.lineno
        hi = getattr(node, "end_lineno", None)
        if hi is None:
            continue
        if not any(lo <= h <= hi for h in hit):
            continue
        # the decorator list starts above node.lineno; include it, it is part of the unit
        for dec in node.decorator_list:
            lo = min(lo, dec.lineno)
        text = "\n".join(lines[lo - 1 : hi])
        found.append(
            {
                "name": node.name,
                "lineno": lo,
                "end_lineno": hi,
                "n_lines": hi - lo + 1,
                "touched": sum(1 for h in hit if lo <= h <= hi),
                "source": text,
            }
        )
    # innermost wins: a nested def is a more precise unit than the function enclosing it
    found.sort(key=lambda u: (int(u["n_lines"]),))
    seen: set[str] = set()
    out: list[dict[str, object]] = []
    for u in found:
        if u["name"] in seen:
            continue
        seen.add(str(u["name"]))
        out.append(u)
    return out
