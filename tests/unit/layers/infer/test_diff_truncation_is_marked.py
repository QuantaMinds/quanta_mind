"""Verification that a diff cut to fit the prompt says it was cut.

WHAT: Pins `infer/change_summary._capped` — the diff passes through untouched when it fits, and
      carries an explicit marker when it does not.
WHY:  **THE COMMENT BESIDE `MAX_DIFF_CHARS` CLAIMED THE TRUNCATION WAS "VISIBLE IN THE OUTPUT"
      AND NOTHING MADE IT SO.** The diff was sliced with `diff[:MAX_DIFF_CHARS]` and handed to
      the model, which then read a change that stopped mid-hunk with no way to know it had, and
      summarised it as though it were the whole thing. That is rule 14 exactly: a comment may
      explain why, never assert whether.

      **THE PATTERN WAS ALREADY IN THE CODEBASE.** `ingest/standards/conventions.py` marks its
      own truncation with the same kind of sentinel; the diff path simply never did.

      **AND THE CONSTANT WAS NEVER SWEPT.** `30_000` is written with a separator, and the
      mutation tool sliced by `len(repr(value))` — five characters against six — so it refused
      rather than mutating. Three constants were skipped that way and reported as neither caught
      nor surviving. Fixed in `scripts/measure/mutate.py`, and all four mutations survive.
IMPORTS: pytest, quantamind.infer.change_summary.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.infer.change_summary import MAX_DIFF_CHARS, TRUNCATED, _capped

CAP = 30_000
"""The shipped cap, written out. `MAX_DIFF_CHARS + 1` would read the value under test."""


def test_the_cap_is_thirty_thousand_characters() -> None:
    """Cut from 60,000 when a real 27-file delivery hit MAX_TOKENS."""
    assert MAX_DIFF_CHARS == CAP


def test_a_diff_that_fits_is_passed_through_untouched() -> None:
    """No marker on an intact diff: a reader must not think something was hidden."""
    diff = "+ added a line\n" * 10

    assert _capped(diff) == diff
    assert TRUNCATED not in _capped(diff)


def test_a_diff_at_exactly_the_cap_is_not_marked() -> None:
    """The boundary. Marking an intact diff would be a false warning."""
    assert _capped("x" * CAP) == "x" * CAP


def test_a_longer_diff_is_cut_and_says_so() -> None:
    """The failure being fixed: the model must be able to tell it was not shown everything."""
    capped = _capped("x" * (CAP + 5_000))

    assert capped.startswith("x" * CAP)
    assert capped.endswith(TRUNCATED)
    assert "truncated" in TRUNCATED, "the marker no longer says what happened"


def test_the_kept_portion_is_the_beginning_of_the_diff() -> None:
    """Keeping the tail would drop the files a reviewer reads first."""
    diff = "FIRST-HUNK\n" + "y" * (CAP * 2)

    capped = _capped(diff)

    assert capped[: len("FIRST-HUNK")] == "FIRST-HUNK"
    assert len(capped) == CAP + len(TRUNCATED)
