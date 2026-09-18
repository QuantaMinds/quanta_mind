"""What a forge told us, independent of which forge told us.

WHAT: `delivery.py` holds the four outcomes an authenticated delivery can carry — `Review`,
      `Installed`, `Withdrawn`, `Ignore`.
WHY:  **THE PRODUCT IS ABOUT TO SPEAK TO A SECOND FORGE AND THE REVIEWER MUST NOT LEARN WHICH.**
      These values were GitHub's by accident of where they were defined. Bitbucket reaches us
      through a Forge app rather than a signed webhook, and its payload shares no field names with
      GitHub's — but it means one of the same four things. Naming them once, here, is what lets
      `serve/review/review_delivery.deliver()` stay a single function instead of two that drift.
IMPORTS: stdlib only. Leftmost layer.
CONSUMED BY: `serve/`.
"""
