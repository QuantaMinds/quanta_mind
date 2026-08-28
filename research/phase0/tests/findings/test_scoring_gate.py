"""Verification that the findings scorer withholds a number it cannot justify.

WHAT: Pins the control gate, the refusal to score a partial sheet, and that UNSURE costs a
      point rather than being quietly dropped.
WHY:  The gate's whole value is that it fires on the one input where a result would be most
      tempting: a sheet where everything was marked TRUE, which yields a 100% correctness
      rate. **The test therefore asserts the rate is ABSENT from the output**, not merely
      that a warning is present -- an earlier version printed both, and a number printed
      beneath a caveat is a number that gets quoted without one.
IMPORTS: pytest, phase0.findings.scoring.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0.findings.scoring import main, wilson


def _files(tmp: Path, verdicts: dict[str, str], arms: dict[str, str]) -> tuple[Path, Path]:
    key = tmp / "key.csv"
    key.write_text("\n".join(f"{i},{a}" for i, a in arms.items()) + "\n")
    labels = tmp / "labels.csv"
    labels.write_text(
        "label_id,verdict\n" + "\n".join(f"{i},{v}" for i, v in verdicts.items()) + "\n"
    )
    return labels, key


def _arms(real: int, planted: int) -> dict[str, str]:
    ids = {f"item {i:02d}": "REAL" for i in range(1, real + 1)}
    ids.update({f"item {i:02d}": "PLANTED" for i in range(real + 1, real + planted + 1)})
    return ids


def _run(monkeypatch, labels: Path, key: Path) -> int:
    monkeypatch.setattr("sys.argv", ["score_findings", "--labels", str(labels), "--key", str(key)])
    return main()


def test_marking_everything_true_yields_no_number_at_all(tmp_path, monkeypatch, capsys) -> None:
    """The failure the controls exist for. 100% must not appear anywhere in the output."""
    arms = _arms(6, 6)
    labels, key = _files(tmp_path, dict.fromkeys(arms, "TRUE"), arms)
    code = _run(monkeypatch, labels, key)
    out = capsys.readouterr().out
    assert code == 2, out
    assert "WITHHELD" in out, out
    assert "100" not in out and "FINDINGS CORRECT" not in out, f"the rate leaked anyway: {out}"


def test_catching_the_controls_produces_the_rate(tmp_path, monkeypatch, capsys) -> None:
    arms = _arms(6, 6)
    verdicts = {i: ("FALSE" if a == "PLANTED" else "TRUE") for i, a in arms.items()}
    verdicts["item 01"] = "FALSE"
    labels, key = _files(tmp_path, verdicts, arms)
    code = _run(monkeypatch, labels, key)
    out = capsys.readouterr().out
    assert code == 0, out
    assert "FINDINGS CORRECT  5 of 6" in out, out


def test_unsure_costs_a_point_rather_than_being_dropped(tmp_path, monkeypatch, capsys) -> None:
    arms = _arms(6, 6)
    verdicts = {i: ("FALSE" if a == "PLANTED" else "TRUE") for i, a in arms.items()}
    verdicts["item 02"] = "UNSURE"
    labels, key = _files(tmp_path, verdicts, arms)
    _run(monkeypatch, labels, key)
    out = capsys.readouterr().out
    assert "FINDINGS CORRECT  5 of 6" in out, out
    assert "UNSURE            1 of 12" in out, out


def test_a_partial_sheet_is_refused(tmp_path, monkeypatch, capsys) -> None:
    """Committing to every answer is what stops a labeller peeking after half."""
    arms = _arms(6, 6)
    verdicts = {i: ("TRUE" if n else "") for n, i in enumerate(arms)}
    labels, key = _files(tmp_path, verdicts, arms)
    assert _run(monkeypatch, labels, key) == 1
    assert "refusing to score" in capsys.readouterr().out


def test_a_key_and_sheet_that_disagree_are_refused(tmp_path, monkeypatch, capsys) -> None:
    arms = _arms(6, 6)
    labels, key = _files(tmp_path, dict.fromkeys(list(arms)[:-1], "TRUE"), arms)
    assert _run(monkeypatch, labels, key) == 1
    assert "refusing to score" in capsys.readouterr().out


def test_a_junk_verdict_is_refused(tmp_path, monkeypatch, capsys) -> None:
    arms = _arms(6, 6)
    verdicts = dict.fromkeys(arms, "TRUE")
    verdicts["item 03"] = "PROBABLY"
    labels, key = _files(tmp_path, verdicts, arms)
    assert _run(monkeypatch, labels, key) == 1
    assert "not a verdict" in capsys.readouterr().out


@pytest.mark.parametrize("hits,n", [(0, 12), (12, 12), (6, 12)])
def test_the_interval_stays_inside_zero_and_one(hits: int, n: int) -> None:
    """A normal approximation goes outside the unit interval exactly at the ends we hit."""
    low, high = wilson(hits, n)
    assert 0.0 <= low <= high <= 1.0, (low, high)
