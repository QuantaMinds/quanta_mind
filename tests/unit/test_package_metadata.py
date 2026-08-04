"""Unit tier: the package imports and declares the version it claims to.

WHAT: Asserts the package root is importable and pinned at the pre-Phase-0 version.
WHY:  Two jobs. It stops `pytest tests/unit` exiting 5 (no tests collected), which
      `just check` reads as failure on a fresh clone -- the exact bug
      CONTRIBUTING.md calls the highest-priority issue in the repository. And it
      asserts on a value rather than truthiness, so it survives
      scripts/guard/check_assert_quality.py, which is the standard every test here
      is held to.
IMPORTS: qmctx (the package root). Tier 1, so mocks would be permitted; none needed.
CONSUMED BY: justfile (`just test-unit`), .github/workflows/ci.yml.
"""

from __future__ import annotations

import qmctx


def test_version_is_pre_phase_zero() -> None:
    """0.0.0 is a claim: nothing here is validated until the correlation test reports."""
    assert qmctx.__version__ == "0.0.0"


def test_package_exports_only_version() -> None:
    """The root stays empty by design -- layer packages arrive in phase PRs."""
    assert qmctx.__all__ == ["__version__"]
