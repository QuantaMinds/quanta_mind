"""What the first scan may say about a repository, and the two things it must never say.

WHAT: Renders `render.scan_report.report()` over real `Hotspots` values and asserts the window, the
      share arithmetic, the labelling of a model's narration, and the refusal to conflate an empty
      history with a failed walk.
WHY:  **THE SCAN IS THE FIRST THING A PROSPECT RUNS, AND IT IS A COUNT WEARING A REPORT'S CLOTHES.**
      A table of touch counts invites a reader to hear "these files are bad". `AGENTS.md` rule 14
      is the reason the renderer says what it counted rather than what it thinks, and the risk-word
      assertion below is what keeps that true after the next edit.

      **THE NARRATION IS THE PART THAT CAN DRIFT.** It is a model's paragraph, printed inside a
      report whose other half is reproducible, and the label is the only thing separating them. A
      test that only checked the paragraph appeared would pass with the label deleted.

      **AN EMPTY SCAN AND A FAILED WALK BOTH PRODUCE ZERO ROWS.** The renderer must refuse to claim
      either, and `test_empty_claims_neither` is the assertion that it does -- the same
      "no edge here" versus "we failed here" distinction the resolver layer is built on.
IMPORTS: quantamind.render.scan_report, quantamind.store.touches for `Hotspots`.
"""

from __future__ import annotations

from quantamind.render.scan_report import as_of, report
from quantamind.store.touches import Hotspots

# Shaped like the real Flask scan: a long window, a concentrated head, a mixed set of paths.
REAL = Hotspots(
    files=(("src/flask/app.py", 354), ("CHANGES.rst", 328), ("src/flask/helpers.py", 204)),
    tracked=642,
    touches=9093,
    first=1_200_000_000,
    last=1_700_000_000,
)


def test_window_is_printed_so_the_table_can_be_read() -> None:
    """Three weeks and seven years give the same table; only the window says which you have."""
    out = report("pallets/flask", REAL)
    assert "9,093 file-touches" in out
    assert "642 file(s)" in out
    assert "5,787 day(s)" in out, "the span must be stated, or the counts mean nothing"


def test_the_share_is_arithmetic_a_reader_can_redo() -> None:
    """(354 + 328 + 204) / 9,093 = 9.7%, which must round to 10 and be attributed to 3 files."""
    out = report("pallets/flask", REAL)
    assert "top 3 file(s) carry 10%" in out


def test_no_risk_word_reaches_the_reader() -> None:
    """**A COUNT IS NOT A VERDICT.** The renderer may not call a file risky, buggy or a problem."""
    out = report("pallets/flask", REAL).lower()
    for word in ("risk", "risky", "problem", "dangerous", "buggy", "defect", "unsafe"):
        assert word not in out, f"the scan called something {word!r}; it counted commits"


def test_empty_claims_neither_no_history_nor_a_failure() -> None:
    """Zero rows means a fresh repository OR a broken walk, and the report must not pick one."""
    out = report("acme/new", Hotspots(files=(), tracked=0, touches=0, first=0, last=0))
    assert "different" in out, "the two causes must be named as distinguishable"
    assert "claims neither" in out
    assert "carry" not in out, "an empty scan must not print a share of nothing"


def test_a_model_paragraph_is_labelled_and_comes_last() -> None:
    """The counts are reproducible and the paragraph is 25.0% correct. The label is the seam."""
    out = report("pallets/flask", REAL, narration="The distribution is concentrated.")
    assert out.index("354 touch(es)") < out.index("The distribution is concentrated.")
    assert "a model's reading" in out
    assert "25.0% correct" in out, "the reader must be told what the paragraph is worth"
    assert "not shown your code" in out


def test_silence_from_the_model_prints_no_label_at_all() -> None:
    """An empty narration must not render an empty labelled block, which reads as a model result."""
    assert "a model's reading" not in report("pallets/flask", REAL, narration="   ")


def test_as_of_names_a_never_rather_than_an_epoch() -> None:
    """`0` formatted as a date is 1970, which reads as a real and very old commit."""
    assert (
        as_of(Hotspots(files=(), tracked=0, touches=0, first=0, last=0))
        == "never -- no commit was read"
    )
    assert as_of(REAL).startswith("20")
