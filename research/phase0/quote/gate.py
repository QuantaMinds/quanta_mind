"""Decide whether a finding is anchored, using string operations and no model at all.

WHAT: `added_lines()` parses a unified diff into the lines it ADDS, with new-file line numbers and
      a hunk id. `check()` runs one finding through five gates and returns EVERY gate it failed,
      plus a DERIVED line number when it passes.
WHY:  87.3% of this project's published claims quoted code absent from the line they cited, because
      the prose and the line number were generated independently. Five designs repaired the line
      number and all five failed. This one never asks for a line number: the model quotes code, and
      the line is computed from where that quote sits.

      EVERY GATE HERE IS A STRING OPERATION. A parser can decide whether a snippet occurs in a
      diff, so a model must not be asked to. The gate is deterministic, free, and reproducible
      without an API key.

      NO SHORT-CIRCUIT. Every gate is evaluated on every finding, because the gates are not
      independent -- a model that cannot quote accurately probably also names identifiers that are
      absent. Returning at the first failure would report five marginals and hide that one gate is
      doing all the work while four are decorative.

      THE PUBLISHED ANCHOR RATE IS 100% BY CONSTRUCTION AND IS NOT A RESULT. What varies, and is
      therefore reported, is the RAW rate at which findings fail G-quote.
IMPORTS: stdlib only (re).
CONSUMED BY: `run.py` in this package.
"""

from __future__ import annotations

import re

IDENT = re.compile(r"`([^`\n]{2,80})`")
# Copied from Qodo's reflection prompt, which assigns these a score of zero.
NIT = re.compile(
    r"\b(docstring|type hint|type annotation|add a comment|unused import|missing import|"
    r"unused variable|more specific exception|naming convention|typo|formatting|whitespace|"
    r"rename|readability)\b",
    re.I,
)
MIN_QUOTE_CHARS = 8


def _norm(s: str) -> str:
    """Collapse whitespace so indentation differences do not fail an otherwise exact quote."""
    return re.sub(r"\s+", " ", s).strip()


def added_lines(diff: str) -> tuple[list[tuple[str, int, str, int]], dict[int, int]]:
    """([(path, new-file line, text, hunk id)], {hunk id: added-line count}).

    Only added lines count. A finding about code the pull request did not introduce is a finding
    about the existing codebase, which is not what a diff-scoped reviewer was asked for.

    The hunk id and its size are carried because hunk size is the pre-registered PROXY for
    enclosing function length -- the corpus is not neutral on that axis and the wrong-rate is
    reported stratified by it.
    """
    out: list[tuple[str, int, str, int]] = []
    sizes: dict[int, int] = {}
    path, lineno, hunk = "", 0, -1
    for raw in diff.split("\n"):
        if raw.startswith("+++ b/"):
            path, lineno = raw[6:].strip(), 0
            continue
        if raw.startswith("@@"):
            m = re.search(r"\+(\d+)", raw)
            lineno = int(m.group(1)) if m else 0
            hunk += 1
            sizes[hunk] = 0
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            out.append((path, lineno, raw[1:], hunk))
            sizes[hunk] = sizes.get(hunk, 0) + 1
            lineno += 1
        elif raw.startswith("-") or raw.startswith("\\"):
            continue
        elif path:
            lineno += 1
    return out, sizes


def locate(quote: str, added: list[tuple[str, int, str, int]]) -> tuple[str, int, int] | None:
    """(path, line, hunk id) of the first added line containing the quote, or None.

    Multi-line quotes match on their first non-empty line: a model quoting three lines has still
    identified one anchor point, and demanding the whole block occur on one physical line would
    reject correct findings for a formatting reason.
    """
    needle = _norm(quote)
    if len(needle) < MIN_QUOTE_CHARS:
        return None
    first = next((_norm(x) for x in quote.split("\n") if _norm(x)), "")
    for path, ln, text, hunk in added:
        hay = _norm(text)
        if needle and needle in hay:
            return path, ln, hunk
        if first and len(first) >= MIN_QUOTE_CHARS and first in hay:
            return path, ln, hunk
    return None


def check(
    finding: dict[str, str],
    diff: str,
    added: list[tuple[str, int, str, int]],
    sizes: dict[int, int],
) -> dict[str, object]:
    """Run one finding through every gate. Returns {'ok', 'failed': [gate names], ...}.

    `failed` is a LIST so the joint distribution is recoverable. A finding failing only G-nit and a
    finding failing G-quote, G-outer and G-nit together are different facts about the model, and
    collapsing them to a first-failure label would lose the one that matters.
    """
    quote = str(finding.get("quote") or "")
    claim = str(finding.get("claim") or "")
    fix = str(finding.get("fix") or "")
    failed: list[str] = []

    if not quote.strip() or not claim.strip():
        return {"ok": False, "failed": ["G-empty"], "hunk_size": 0}

    hit = locate(quote, added)
    if hit is None:
        failed.append("G-quote")
        path, line, hunk = "", 0, -1
    else:
        path, line, hunk = hit

    if not fix.strip() or _norm(fix) == _norm(quote):
        failed.append("G-fix")

    # Qodo's rule: never question an entity that may be declared outside the diff.
    names = [n for n in IDENT.findall(claim) if not n.startswith("http")]
    body = _norm(diff)
    unseen = [n for n in names if _norm(n.split("(")[0].split(".")[-1]) not in body]
    if unseen:
        failed.append("G-outer")

    if NIT.search(claim):
        failed.append("G-nit")

    return {
        "ok": not failed,
        "failed": failed,
        "path": path,
        "line": line,
        "claim": claim,
        "quote": quote,
        "fix": fix,
        "unseen": unseen,
        "hunk_size": sizes.get(hunk, 0),
    }
