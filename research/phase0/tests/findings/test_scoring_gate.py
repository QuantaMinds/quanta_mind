"""Verification that a verdict without an admissible deciding line is not scored.

WHAT: Pins the attention check that replaced the planted control arm, the refusal to score a
      partial sheet, and that both rates are printed with UNKNOWN handled explicitly.
WHY:  The control arm was passable without doing the task -- an isolated judge scored 12 of 12
      on it by checking filenames. The deciding line cannot be produced without reading the
      code, and whether it is really in that code is checkable.

      **THE TESTS ASSERT THE RATE IS ABSENT when a line is inadmissible**, not merely that a
      warning appears: a number printed beneath a caveat is a number quoted without one.
IMPORTS: pytest, phase0.findings.scoring.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0.findings.scoring import main, read_blocks, wilson

DIFF = "@@\n+    value_{n} = compute_{n}(arg)\n+    return value_{n}\n"


def _pack(n: int) -> str:
    out = ["# pack", ""]
    for i in range(1, n + 1):
        out += [f"## item {i:02d}", "", "**Code:**", "", "```diff", DIFF.format(n=i), "```", ""]
    return "\n".join(out)


def _labels(verdicts: dict[int, tuple[str, str]]) -> str:
    out = ["# Verdicts", ""]
    for i, (verdict, line) in sorted(verdicts.items()):
        out += [f"## item {i:02d}", "", f"VERDICT: {verdict}", f"LINE: {line}", ""]
    return "\n".join(out)


def _run(tmp: Path, monkeypatch, pack: str, labels: str) -> int:
    (tmp / "p.md").write_text(pack)
    (tmp / "l.md").write_text(labels)
    monkeypatch.setattr(
        "sys.argv", ["scoring", "--labels", str(tmp / "l.md"), "--pack", str(tmp / "p.md")]
    )
    return main()


def _good(n: int, true_upto: int) -> dict[int, tuple[str, str]]:
    return {
        i: (("TRUE" if i <= true_upto else "FALSE"), f"    value_{i} = compute_{i}(arg)")
        for i in range(1, n + 1)
    }


def test_a_line_not_in_the_diff_blocks_the_rate(tmp_path, monkeypatch, capsys) -> None:
    """The attention check. A verdict read off nothing must not produce a number."""
    labels = _good(6, 3)
    labels[2] = ("TRUE", "    this line is nowhere in the pack")
    code = _run(tmp_path, monkeypatch, _pack(6), _labels(labels))
    out = capsys.readouterr().out
    assert code == 2, out
    assert "item 02" in out and "not in the diff" in out, out
    assert "CORRECT" not in out, f"the rate was printed anyway: {out}"


def test_a_missing_line_on_a_decided_verdict_blocks_the_rate(tmp_path, monkeypatch, capsys) -> None:
    labels = _good(6, 3)
    labels[5] = ("FALSE", "")
    assert _run(tmp_path, monkeypatch, _pack(6), _labels(labels)) == 2
    out = capsys.readouterr().out
    assert "line missing" in out and "CORRECT" not in out, out


def test_unknown_needs_no_line_and_still_scores(tmp_path, monkeypatch, capsys) -> None:
    """UNKNOWN is the honest answer when the diff cannot settle it, so it must not be blocked."""
    labels = _good(6, 3)
    labels[6] = ("UNKNOWN", "")
    assert _run(tmp_path, monkeypatch, _pack(6), _labels(labels)) == 0
    out = capsys.readouterr().out
    assert "TRUE 3   FALSE 2   UNKNOWN 1" in out, out


def test_both_rates_are_printed_and_differ_on_unknown(tmp_path, monkeypatch, capsys) -> None:
    """Over all items UNKNOWN counts against; over decided items it is excluded."""
    labels = _good(6, 3)
    labels[6] = ("UNKNOWN", "")
    _run(tmp_path, monkeypatch, _pack(6), _labels(labels))
    out = capsys.readouterr().out
    assert "3/6 = 50.0%" in out, out
    assert "3/5 = 60.0%" in out, out


def test_a_partial_sheet_is_refused(tmp_path, monkeypatch, capsys) -> None:
    labels = _good(6, 3)
    labels[4] = ("", "")
    assert _run(tmp_path, monkeypatch, _pack(6), _labels(labels)) == 1
    assert "refusing to score" in capsys.readouterr().out


def test_a_sheet_that_does_not_cover_the_pack_is_refused(tmp_path, monkeypatch, capsys) -> None:
    assert _run(tmp_path, monkeypatch, _pack(6), _labels(_good(5, 2))) == 1
    assert "refusing to score" in capsys.readouterr().out


def test_a_junk_verdict_is_refused(tmp_path, monkeypatch, capsys) -> None:
    labels = _good(6, 3)
    labels[3] = ("PROBABLY", "    value_3 = compute_3(arg)")
    assert _run(tmp_path, monkeypatch, _pack(6), _labels(labels)) == 1
    assert "not a verdict" in capsys.readouterr().out


def test_blocks_parse_back_the_fields_they_were_written_with() -> None:
    got = read_blocks("## item 01\n\nVERDICT: TRUE\nLINE: x = 1\n", fields=("VERDICT", "LINE"))
    assert got == {"item 01": {"VERDICT": "TRUE", "LINE": "x = 1"}}, got


@pytest.mark.parametrize("hits,n", [(0, 24), (24, 24), (12, 24)])
def test_the_interval_stays_inside_zero_and_one(hits: int, n: int) -> None:
    low, high = wilson(hits, n)
    assert 0.0 <= low <= high <= 1.0, (low, high)
