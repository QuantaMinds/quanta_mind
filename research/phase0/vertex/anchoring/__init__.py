"""The three attempts to make a model's claim point at the right line of code.

Split from the runners at the directory fan-out cap, and they belong together because they are one
argument in three steps:

  anchors.py   snap a model-emitted line to its enclosing statement -- FAILED, because the number
               was never coupled to the prose; it relocated an unrelated number to a tidier place
  context.py   give the model the class attributes, signatures and call sites of the file -- FAILED
               to move the wrong-rate (p = 0.53), though it did make the reviewer quieter
  symbols.py   stop the model emitting a number at all: it names an identifier, the parser derives
               the line -- the model named a real symbol 36 times out of 36, and the wrong-rate
               still did not move (82.1% -> 77.8%, p = 0.644)

Together they establish that the reviewer's failure is not in the pointing. Kept because the
negative results are the finding.
"""

from __future__ import annotations
