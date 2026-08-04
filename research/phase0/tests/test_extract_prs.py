"""Contract test for corpus extraction.

WHAT: Asserts extract() is unimplemented and that PRRecord carries parent_sha.
WHY:  parent_sha is the field the study's validity rests on. Exposure is computed
      at the commit the agent branched from; classifying against merged state leaks
      the outcome into the exposure. If this field is ever dropped from the record,
      every downstream stage silently loses the ability to honour that, so its
      presence is asserted here rather than assumed.
IMPORTS: phase0.extract_prs, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pytest

from phase0.extract_prs import PRRecord, extract


def test_extract_is_unimplemented() -> None:
    with pytest.raises(NotImplementedError):
        extract(Path("aidev"), "python")


def test_record_carries_the_parent_commit() -> None:
    """Without parent_sha the leakage guarantee in classify_exposure is unenforceable."""
    assert "parent_sha" in {f.name for f in fields(PRRecord)}


def test_record_is_immutable() -> None:
    """Frozen: a corpus record must not be edited after the outcome scan runs."""
    record = PRRecord("1", "o/r", "python", "abc", "def", "2026-01-01T00:00:00Z", (), ())
    with pytest.raises(AttributeError):
        record.parent_sha = "tampered"  # type: ignore[misc]
