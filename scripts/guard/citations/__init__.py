"""Guards over citations: that they resolve, and that dated ones are still current.

WHAT: Two checks. `resolve` fails when a cited path does not exist; `freshness` fails when a
      figure's stated re-check date has passed.
WHY:  Split out of scripts/guard/ when it reached its fifteen-file cap, and split here rather
      than anywhere else because these two guard the same failure: a citation that reads as
      authority while pointing at nothing. One catches a path that was never written, the
      other catches a source that has since moved.
IMPORTS: scripts/guard/discovery.py; stdlib only.
CONSUMED BY: justfile (`just check`), .github/workflows/guards.yml.
"""

from __future__ import annotations
