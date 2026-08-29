"""Verification that the scorer WITHHOLDS a rate it cannot justify.

WHAT: Pins the four ways a sheet is refused — a deciding line that is not a line of code, one
      pointing the wrong way, an absent DIRECTION, and a sheet so one-sided it cannot be told
      from a constant responder.
WHY:  Split from `test_scoring_gate.py`, which pins what the rate IS. This pins when there is
      no rate, and that is the half with a history: **two of these four gates were written and
      demonstrated by hand, and both could be disabled without a single test failing.**

      Each case here is a sheet that reached a real result it should not have. A second rater
      returned 23 TRUE of 24 and scored 95.8% — the same score a responder answering TRUE
      unconditionally gets — and nothing in the output said so.
IMPORTS: pytest, phase0.findings.scoring.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

from phase0.findings.scoring import main

DIFF = "@@\n+    value_{n} = compute_{n}(arg)\n+    return value_{n}\n"


def _pack(n: int) -> str:
    out = ["# pack", ""]
    for i in range(1, n + 1):
        out += [f"## item {i:02d}", "", "**Code:**", "", "```diff", DIFF.format(n=i), "```", ""]
    return "\n".join(out)


def _labels(verdicts: dict[int, tuple[str, str]]) -> str:
    out = ["# Verdicts", ""]
    for i, (verdict, line) in sorted(verdicts.items()):
        way = "REMOVED" if line.strip().startswith("-") else "ADDED" if line.strip() else ""
        out += [
            f"## item {i:02d}",
            "",
            f"VERDICT: {verdict}",
            f"LINE: {line}",
            f"DIRECTION: {way}",
            "",
        ]
    return "\n".join(out)


def _good(n: int, true_upto: int) -> dict[int, tuple[str, str]]:
    return {
        i: (("TRUE" if i <= true_upto else "FALSE"), f"+    value_{i} = compute_{i}(arg)")
        for i in range(1, n + 1)
    }


def _run(tmp: Path, monkeypatch, pack: str, labels: str) -> int:
    (tmp / "p.md").write_text(pack)
    (tmp / "l.md").write_text(labels)
    monkeypatch.setattr(
        "sys.argv", ["scoring", "--labels", str(tmp / "l.md"), "--pack", str(tmp / "p.md")]
    )
    return main()


def test_a_sheet_that_is_one_verdict_throughout_is_withheld(tmp_path, monkeypatch, capsys) -> None:
    """**THE FAILURE A REAL SECOND RATER PRODUCED.** 23 TRUE of 24 scores 95.8%, and so does a
    responder answering TRUE unconditionally. Nothing in the output said so, so the number read
    as a measurement. The rate must be ABSENT, not printed under a caveat.
    """
    labels = {i: ("TRUE", f"+    value_{i} = compute_{i}(arg)") for i in range(1, 7)}
    code = _run(tmp_path, monkeypatch, _pack(6), _labels(labels))
    out = capsys.readouterr().out
    assert code == 3, out
    assert "ONE VERDICT ON" in out and "WITHHELD" in out, out
    assert "CORRECT" not in out, f"the rate was printed anyway: {out}"


def test_a_sheet_just_under_the_threshold_still_scores(tmp_path, monkeypatch, capsys) -> None:
    """The gate must not swallow an ordinary lopsided-but-real sheet, or it eats every result."""
    labels = {i: ("TRUE", f"+    value_{i} = compute_{i}(arg)") for i in range(1, 7)}
    labels[6] = ("FALSE", "+    value_6 = compute_6(arg)")
    labels[5] = ("UNKNOWN", "")
    assert _run(tmp_path, monkeypatch, _pack(6), _labels(labels)) == 0
    assert "CORRECT" in capsys.readouterr().out


def test_a_direction_contradicting_the_diff_is_withheld(tmp_path, monkeypatch, capsys) -> None:
    """The line is real and present; only its direction is wrong. The rate must not compute."""
    labels = _good(6, 3)
    sheet = _labels(labels).replace("DIRECTION: ADDED", "DIRECTION: REMOVED", 1)
    (tmp_path / "p.md").write_text(_pack(6))
    (tmp_path / "l.md").write_text(sheet)
    monkeypatch.setattr(
        "sys.argv",
        ["scoring", "--labels", str(tmp_path / "l.md"), "--pack", str(tmp_path / "p.md")],
    )

    code = main()
    out = capsys.readouterr().out
    assert code == 4, out
    assert "POINTING THE WRONG WAY" in out and "CORRECT" not in out, out


def test_a_missing_direction_is_withheld_not_skipped(tmp_path, monkeypatch, capsys) -> None:
    """**AN ABSENT FIELD USED TO MEAN THE CHECK PASSED OVER THE ITEM IN SILENCE.**"""
    labels = _good(6, 3)
    sheet = _labels(labels).replace("DIRECTION: ADDED", "DIRECTION:", 1)
    (tmp_path / "p.md").write_text(_pack(6))
    (tmp_path / "l.md").write_text(sheet)
    monkeypatch.setattr(
        "sys.argv",
        ["scoring", "--labels", str(tmp_path / "l.md"), "--pack", str(tmp_path / "p.md")],
    )

    code = main()
    out = capsys.readouterr().out
    assert code == 4, out
    assert "no DIRECTION given" in out and "CORRECT" not in out, out


def test_a_diff_header_cited_as_the_deciding_line_is_withheld(
    tmp_path, monkeypatch, capsys
) -> None:
    """The sheet that slipped every gate: a header is in the diff text, so a substring test
    accepts it, and it then failed to place — which the old code passed over in silence."""
    labels = dict.fromkeys(range(1, 7), ("TRUE", "+++ b/pkg/mod.py"))
    labels[6] = ("FALSE", "+++ b/pkg/mod.py")
    code = _run(tmp_path, monkeypatch, _pack(6), _labels(labels))
    out = capsys.readouterr().out
    assert code == 2, out
    assert "diff header" in out and "CORRECT" not in out, out
