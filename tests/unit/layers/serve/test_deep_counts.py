"""The reviewer pass's discard counts: they conserve, and every fate is named in the output.

WHAT: Drives `types.deep.Deep` and `render.deep_report.lines()` with known fates and asserts the
      arithmetic and the text.
WHY:  **THIS IS THE TEST WHOSE ABSENCE LET THE BUG SHIP.** `unanchored` was computed as
      `len(found) - len(surviving)` — quote-not-in-diff PLUS oracle-refuted — so every refuted
      finding was counted twice. `grep unanchored tests/` returned nothing: the field was never
      asserted on anywhere in the tree, and a trailing `- refuted + refuted` made the expression
      read as deliberate.

      **THE OUTPUT IS ASSERTED, NOT JUST THE RECORD.** The counts were correct on the record for
      `refuted` and `withdrawn` before this change and still never reached the operator, who was
      shown one number for three different fates. A record that is right and a report that is
      wrong is the same failure as a wrong record.
IMPORTS: types.{deep,finding}, render.deep_report. No mocks — these are pure values.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.render.deep_report import lines
from quantamind.types.deep import Deep
from quantamind.types.finding import Finding

KEPT = Finding(path="a.py", quote="x = 1", claim="KEPT-claim", line=4)


def test_counts_that_do_not_conserve_are_refused() -> None:
    """The exact shape of the original defect: refuted counted in `unanchored` as well."""
    with pytest.raises(ValueError) as caught:
        # 4 raw, but 1 anchored + 2 unanchored + 1 refuted + 1 withdrawn accounts for 5 --
        # which is what `len(found) - len(surviving)` produced when one finding was refuted.
        Deep((KEPT,), 4, 2, 1, 1, ("a.py",))
    assert "lost count" in str(caught.value)
    assert "4 raw" in str(caught.value) and "5 accounted for" in str(caught.value)


def test_the_honest_counts_are_accepted() -> None:
    """The same pass counted correctly: one of each fate sums to the four the model returned."""
    out = Deep((KEPT,), 4, 1, 1, 1, ("a.py",))
    assert (out.raw, out.unanchored, out.refuted, out.withdrawn) == (4, 1, 1, 1)


def test_every_fate_is_named_in_the_report() -> None:
    """Three discards, three mechanisms, three lines. Not one number standing for all of them."""
    text = "\n".join(lines(Deep((KEPT,), 4, 1, 1, 1, ("a.py",))))
    assert "4 raw finding(s)" in text
    assert "1 anchored" in text
    assert "not in the diff" in text, "the unanchored count lost its mechanism"
    assert "oracle refuted" in text, "an oracle refusal vanished from the output"
    assert "withdrawn" in text, "the model's own retraction vanished from the output"
    assert "KEPT-claim" in text


def test_a_model_never_asked_does_not_read_as_a_model_that_found_nothing() -> None:
    """Rule 3. `raw=0` from an empty diff and `raw=0` from a clean review are different states."""
    never = "\n".join(lines(Deep((), 0, 0, 0, 0, ("a.py",), consulted=False)))
    clean = "\n".join(lines(Deep((), 0, 0, 0, 0, ("a.py",))))
    assert "NOT ASKED" in never and "did not run" in never
    assert "reported nothing" in clean and "a result, not a failure" in clean
    assert never != clean, "an instrument that did not run printed the same as a clean review"
