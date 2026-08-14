"""The infer layer.

WHAT: Model calls: structured output, prompt caching, refusal handling, provider adapters.
WHY:  Isolated so that everything to its left runs without a key. The free tier is not a
      configuration of this layer -- it is the absence of it.
IMPORTS: types through allocate.
CONSUMED BY: verify, render.
"""

from __future__ import annotations
