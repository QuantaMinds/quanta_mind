"""The quantamind package root.

WHAT: Declares the package and its version. Nothing else.
WHY:  docs/plans/roadmap/product-skeleton.md builds the layers in dependency order, so the layer
      packages (types/, store/, ingest/, parse/, rank/, allocate/, infer/, verify/,
      render/, serve/) arrive one PR at a time and none exists yet. This file exists
      because scripts/guard/check_conventions.py requires src/quantamind/ to be present,
      and because a package with no importable root cannot be type-checked or tested.
IMPORTS: nothing. The types layer, when it lands, will be the first thing here.
CONSUMED BY: tests/unit/test_package_metadata.py today; every layer later.
"""

from __future__ import annotations

__all__ = ["__version__"]

# Stays 0.0.0 until the ranker reproduces its research number inside this package -- the
# gate named in docs/plans/roadmap/product-skeleton.md "Order of work". A version number implies a
# thing that works, and what works today lives in research/, not here.
__version__ = "0.0.0"
