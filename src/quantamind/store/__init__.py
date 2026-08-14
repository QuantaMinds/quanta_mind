"""The store layer.

WHAT: Persistence of the types: schema, migrations, and one repository module per aggregate.
WHY:  The outcome of a review is knowable only weeks later, so the store is append-only and
      carries late-arriving labels. It is the asset, which is why there is no
      delete-and-reindex path.
IMPORTS: types.
CONSUMED BY: ingest and everything right of it.
"""

from __future__ import annotations
