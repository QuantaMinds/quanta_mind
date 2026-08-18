"""Expand each hunk back to the function it sits in, using the signature git already computed.

WHAT: `expand(diff, fetch)` rewrites a unified diff so every hunk begins at its enclosing function
      or class, and reports what it managed to expand.
WHY:  Git writes the enclosing declaration into every hunk header -- `@@ -266,17 +269,12 @@ def
      get_dumper(self, obj: Any, format: PyFormat) -> abc.Dumper:` -- and we throw it away. The
      model sees `+ if order.refunded:` with three lines of context and does not know what function
      it is in.

      QODO DOES THIS AND LEADS THE BENCHMARK AT 67.9% PRECISION. Their `allow_dynamic_context`
      walks back up to ten lines looking for the line matching that header and starts the hunk
      there. It costs one file read and no model call.

      THE INVARIANT THAT MATTERS: expansion must not move the ADDED lines. `gate.py` derives every
      finding's location from where an added line sits, so a rewrite that shifts those numbers
      would silently corrupt every anchor. `tests` assert the added-line positions are identical
      before and after.
IMPORTS: stdlib only (re).
CONSUMED BY: `run13.py` in this package.
"""

from __future__ import annotations

import re
from collections.abc import Callable

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")
# Fixed at 20 BEFORE any correctness run. Qodo ships 10; a sweep over 211 hunks of six ALREADY-
# BURNED repositories put coverage at 40.3/55.5/62.1/73.9% for 5/10/20/60, with zero anchor shifts
# at every setting. 20 buys 6.6 points over Qodo's 10 for ~1.1k extra characters per pull request;
# 60 buys 11.8 more for 4.8x that. The sweep measured COVERAGE on burned repositories -- never a
# wrong-rate, and never on the repositories the effect is measured on.
MAX_BACK = 20


def section(header: str) -> str:
    """The declaration git names after the second @@, or '' when it named none."""
    m = HUNK.match(header)
    return m.group(5).strip() if m else ""


def expand(diff: str, fetch: Callable[[str], list[str] | None]) -> tuple[str, dict[str, int]]:
    """Rewrite the diff with hunks starting at their enclosing declaration.

    `fetch(path)` returns the ORIGINAL file's lines, or None when unavailable -- in which case the
    hunk is emitted unchanged rather than guessed at.
    """
    stats = {"hunks": 0, "expanded": 0, "no_header": 0, "no_file": 0, "not_found": 0}
    out: list[str] = []
    path = ""
    lines = diff.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("--- a/"):
            path = ln[6:].strip()
            out.append(ln)
            i += 1
            continue
        m = HUNK.match(ln)
        if not m:
            out.append(ln)
            i += 1
            continue

        stats["hunks"] += 1
        start1, size1 = int(m.group(1)), int(m.group(2) or 1)
        start2, size2 = int(m.group(3)), int(m.group(4) or 1)
        header = m.group(5).strip()

        if not header:
            stats["no_header"] += 1
            out.append(ln)
            i += 1
            continue
        original = fetch(path)
        if not original:
            stats["no_file"] += 1
            out.append(ln)
            i += 1
            continue

        # Walk back from the hunk looking for the line git named. Indices are 1-based in the diff.
        lo = max(1, start1 - MAX_BACK)
        window = original[lo - 1 : start1 - 1]
        found = -1
        for k, cand in enumerate(window):
            if header in cand:
                found = k
                break
        if found < 0:
            stats["not_found"] += 1
            out.append(ln)
            i += 1
            continue

        extra = window[found:]
        stats["expanded"] += 1
        n = len(extra)
        head = f"@@ -{lo + found},{size1 + n} +{start2 - n},{size2 + n} @@ {header}"
        out.append(head)
        out += [" " + x for x in extra]
        i += 1
    return "\n".join(out), stats
