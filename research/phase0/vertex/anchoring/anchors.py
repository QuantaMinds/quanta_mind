"""Snap a model's cited line number onto the statement that encloses it.

WHAT: Given a file's source and a line the model cited, returns the first line of the smallest
      `ast` statement containing it. A blank line, a comment, a closing bracket or a continuation
      line resolves to the statement it belongs to.
WHY:  36.4% of the first run's findings were wrong for this reason alone -- the reasoning was
      often sound and the pointer landed one or two lines off, on a blank line or a `)`. That is
      the single largest failure bucket and it is not a model problem: the information needed to
      fix it is in the parse tree, which this project already builds. Fixing it in code rather
      than by asking the model more nicely is the deterministic-beats-clever rule applied.

      IT DOES NOT REPAIR A CLAIM THAT POINTS AT THE WRONG PLACE ENTIRELY. Snapping line 3251 to
      its enclosing statement still leaves it citing `organization_id=` when the claim is about
      `workflow_yaml=`. This fixes precision of the pointer, never its intent.
IMPORTS: stdlib only (ast).
CONSUMED BY: `enriched.py` in this package.
"""

from __future__ import annotations

import ast


def statement_spans(source: str) -> list[tuple[int, int]]:
    """(start, end) of every statement, innermost last so the smallest match wins."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    spans: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.stmt):
            continue
        end = getattr(node, "end_lineno", None)
        if end is None:
            continue
        spans.append((node.lineno, end))
    # widest first, so scanning forward lets the narrowest enclosing span win
    spans.sort(key=lambda s: s[1] - s[0], reverse=True)
    return spans


def snap(source: str, line: int, spans: list[tuple[int, int]] | None = None) -> int:
    """The first line of the smallest statement containing `line`.

    Returns `line` unchanged when the file does not parse or nothing encloses it -- an unsnapped
    anchor is a result, not a failure, and the caller counts them.
    """
    if not isinstance(line, int) or line < 1:
        return line
    spans = statement_spans(source) if spans is None else spans
    best: tuple[int, int] | None = None
    for lo, hi in spans:
        if lo <= line <= hi and (best is None or (hi - lo) <= (best[1] - best[0])):
            best = (lo, hi)
    return best[0] if best else line


def snap_pair(source: str, a: int, b: int) -> tuple[int, int, bool]:
    """Snap both anchors. The flag says whether either moved, so the effect is countable."""
    spans = statement_spans(source)
    sa, sb = snap(source, a, spans), snap(source, b, spans)
    return sa, sb, (sa != a or sb != b)
