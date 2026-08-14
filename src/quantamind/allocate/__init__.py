"""The allocate layer.

WHAT: Turns a ranking into a budget: what gets a deep read, what gets none, and the ceiling.
WHY:  The request ceiling is enforced here rather than hoped for. Above the ceiling the review
      still runs and still reports coverage; only inference is withheld.
IMPORTS: types through rank.
CONSUMED BY: infer, serve.
"""

from __future__ import annotations
