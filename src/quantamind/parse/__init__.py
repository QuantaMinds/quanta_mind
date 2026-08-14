"""The parse layer.

WHAT: Turns a diff into changed units, signatures and references. Tree-sitter lives here.
WHY:  Anything the parser cannot resolve becomes an Unresolved record rather than nothing. This
      layer is where the coverage line gets its content, so silence must be typed here or it can
      never be reported downstream.
IMPORTS: types, store, ingest.
CONSUMED BY: rank, verify, render.
"""

from __future__ import annotations
