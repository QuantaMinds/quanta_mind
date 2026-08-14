"""The types layer.

WHAT: Value objects, enums and protocols. Frozen, immutable, no behaviour that touches I/O.
WHY:  Every other layer speaks in these types, so they are the vocabulary of the system. Putting
      them first and forbidding them from importing anything means a type can never drag a
      database or an HTTP client behind it.
IMPORTS: nothing. This layer is the floor.
CONSUMED BY: every layer.
"""

from __future__ import annotations
