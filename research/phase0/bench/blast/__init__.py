"""Does blast radius predict which file a later fix returns to?

WHAT: `predicts.py` scores every admissible event on a clone twice — by prior fix count, the
      signal the product already ships, and by import in-degree, the signal D2a makes possible —
      and reports whether the second separates the outcome at all.
WHY:  D2a measured that ~44% of import statements resolve in-tree, which says the graph is
      buildable and NOTHING about whether it predicts anything. Building D2b and D2d on that
      would be shipping a signal whose value nobody measured, which is the mistake this project
      keeps finding in other people's work.
IMPORTS: stdlib, quantamind.{ingest,rank,parse}. Run with the ROOT interpreter.
CONSUMED BY: an operator, by hand.
"""
