"""Locate a finding's quote in the diff, mechanically, and drop it when the quote is not there.

WHAT: `added_lines(diff)` parses a unified diff into the lines it ADDS with their new-file numbers.
      `locate(finding, diff)` returns the finding with its line derived, or `None` when the quoted
      code does not appear in the diff at all.
WHY:  **THIS IS A PARSER AND IT RUNS BEFORE ANY MODEL JUDGE.** A string search decides whether a
      snippet occurs in a diff, so a model must not be asked to — the project's rule, applied where
      it actually pays. It is free, deterministic, and reproducible without a key.

      **IT CATCHES THE `ABSENT` CLASS BY CONSTRUCTION.** In design thirteen's blind adjudication all
      ten planted sabotage findings — a real quote paired with a claim about entirely different
      code — were caught, and every one of them is a finding whose quote does not sit where the
      claim says. A model judge shares the reviewer's blind spots; a string comparison does not have
      any.

      **THE PUBLISHED ANCHOR RATE IS 100% BY CONSTRUCTION AND IS NOT A RESULT.** Everything that
      survives here is anchored because unanchored findings were removed. What varies, and is
      therefore worth reporting, is the RAW rate at which findings fail this gate.

      **WHITESPACE IS COLLAPSED BEFORE COMPARING.** A quote that differs from the diff only in
      indentation is the same line, and failing it would discard true findings for a reason that
      has nothing to do with truth.
IMPORTS: types.finding only. Never `infer/` — rule 7.
CONSUMED BY: `serve/commands/run_review.py`, before any model judge runs.
"""

from __future__ import annotations

import re
from dataclasses import replace

from quantamind.types.finding import Finding

MIN_QUOTE_CHARS = 8
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def _norm(text: str) -> str:
    """Collapse whitespace so indentation differences do not fail an otherwise exact quote."""
    return re.sub(r"\s+", " ", text).strip()


def added_lines(diff: str) -> list[tuple[str, int, str]]:
    """(path, new-file line number, text) for every line the diff ADDS.

    Only added lines. A finding about a line the change did not introduce is a finding about
    pre-existing code, which this product does not comment on.
    """
    out: list[tuple[str, int, str]] = []
    path = ""
    line = 0
    for raw in diff.splitlines():
        if raw.startswith("+++ b/"):
            path = raw[6:].strip()
            continue
        if raw.startswith("diff --git "):
            path = ""
            continue
        hunk = _HUNK.match(raw)
        if hunk:
            line = int(hunk.group(1))
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            if path:
                out.append((path, line, raw[1:]))
            line += 1
        elif not raw.startswith("-"):
            line += 1
    return out


def locate(finding: Finding, diff: str) -> Finding | None:
    """The finding with `line` derived from where its quote sits, or None if it is not there.

    **None is a REFUSAL, not an absence.** The caller counts it; a finding whose quoted code is not
    in the diff cannot have been read off the diff, whatever the claim says.
    """
    quote = _norm(finding.quote)
    if len(quote) < MIN_QUOTE_CHARS:
        # Too short to identify anything. `}` occurs in every file and would anchor anywhere.
        return None
    for path, number, text in added_lines(diff):
        if path != finding.path:
            continue
        if quote in _norm(text):
            return replace(finding, line=number)
    return None
