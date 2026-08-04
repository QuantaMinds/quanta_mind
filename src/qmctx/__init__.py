"""The qmctx package root.

WHAT: Declares the package and its version. Nothing else.
WHY:  docs/BUILD_PLAN.md gates all product code on Phase 0 reporting a non-null
      verdict, so the layer packages (types/, discover/, ingest/, resolve/,
      probe/, label/, store/, serve/) do not exist yet -- each arrives in its own
      phase PR. This file exists because scripts/guard/check_conventions.py
      requires src/qmctx/ to be present, and because a package with no importable
      root cannot be type-checked or tested.
IMPORTS: nothing. The types layer, when it lands, will be the first thing here.
CONSUMED BY: tests/unit/test_package_metadata.py today; every layer later.
"""

from __future__ import annotations

__all__ = ["__version__"]

# Stays 0.0.0 until Phase 0 fills docs/findings/PHASE0_PREREGISTRATION.md section 8.
# A version number implies a thing that works; there is no such thing here yet.
__version__ = "0.0.0"
