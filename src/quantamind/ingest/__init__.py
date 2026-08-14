"""The ingest layer.

WHAT: Reads from the outside world: git history, diffs, pull-request metadata, comments.
WHY:  Every read that can fail is here, in one layer, so the failure handling is in one place.
      A history read that ignores its exit code is the defect that voided four measurements.
IMPORTS: types, store.
CONSUMED BY: parse, rank, serve.
"""

from __future__ import annotations
