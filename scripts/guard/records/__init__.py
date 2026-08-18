"""Guards over the project's documents, evidence and provenance, rather than its code.

WHAT: The checks that a record still says what its subject does — plan state, documented commands,
      corpus reuse, withdrawn amendments, docs-code sync, and references that name rather than
      number.
WHY:  `scripts/guard/` crossed the fifteen-file cap, and the split that fell out of the contents was
      code-and-structure versus record-and-evidence. On a project whose thesis is provenance, the
      second group is not a lesser kind of guard: a stale record reads exactly like a current one,
      which is the failure mode none of the code guards can see.
IMPORTS: stdlib only, per guard.
CONSUMED BY: the `guards` recipe in the justfile, and .github/workflows/guards.yml.
"""

from __future__ import annotations
