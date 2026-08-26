"""Live tests for the change-shape measurement and the window it is bounded by.

WHAT: A sub-package holding the tests that clone a real repository and check
      `ingest/change_shape.py` against numbers recomputed from git.
WHY:  `tests/live/` reached the 15-file directory cap. Splitting by subject rather than
      alphabetically keeps the reason a file is here legible: everything under this package
      answers "is the shape of a change measured in a window that ends at the change?"
IMPORTS: nothing at package scope.
CONSUMED BY: `just test-live`.
"""
