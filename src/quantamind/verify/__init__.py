"""The verify layer.

WHAT: Adjudicates the model's structural claims against the parse before publication.
WHY:  It cannot import infer. That is the point of the layer order: the code judging the
      model's claims must not be able to start trusting them. Its scope is structural claims
      only, and it says so where a claim is undecidable.
IMPORTS: types through allocate, and parse. NEVER infer.
CONSUMED BY: render.
"""

from __future__ import annotations
