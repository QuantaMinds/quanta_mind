"""The rank layer.

WHAT: The prior-touch index, the percentile threshold, and the ranking itself.
WHY:  This decides where inference is spent, so it is the layer a wrong turn makes expensive.
      It is deliberately model-free: it must run with no key, on every change, for free.
IMPORTS: types, store, ingest, parse.
CONSUMED BY: allocate, render.
"""

from __future__ import annotations
