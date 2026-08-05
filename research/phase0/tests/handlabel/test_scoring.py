"""Verification that the gate refuses to certify what it did not measure.

WHAT: Pins label parsing (incomplete and malformed sheets refused), the pre-registered
      threshold, kappa's treatment of `UNSURE`, and the repository cap on the draw.
WHY:  Every refusal here exists because the alternative is a number that looks like a
      result. A partial sheet scored against what is present lets the gate be met on the
      easy ones; a mistyped verdict silently coerced to CLEAN is a fabricated judgement.
IMPORTS: pytest, phase0.handlabel.{labels,score,draw,select}.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from phase0.handlabel.draw import MAX_PER_REPO, KeyRow, _shuffled_by_repo
from phase0.handlabel.labels import read_labels
from phase0.handlabel.score import GATE_MINIMUM, Agreement, score
from phase0.handlabel.select import Candidate

HEADER = "label_id,verdict,confidence,evidence,reasoning,minutes\n"


def _sheet(tmp_path: Path, body: str, header: str = HEADER) -> Path:
    path = tmp_path / "human_labels.csv"
    path.write_text(header + body, encoding="utf-8")
    return path


def _key(n: int) -> list[KeyRow]:
    return [
        KeyRow(
            label_id=i,
            pr_id=i,
            repo="acme/widget",
            number=i,
            verdict="BROKE" if i % 2 else "CLEAN",
            criterion="revert",
            evidence_sha="b" * 40,
        )
        for i in range(1, n + 1)
    ]


def test_the_threshold_is_the_pre_registered_one() -> None:
    """A boundary the pre-registration forbids moving. Pinned against refactors."""
    assert GATE_MINIMUM == 16


def test_a_partial_sheet_is_refused(tmp_path: Path) -> None:
    path = _sheet(tmp_path, "1,BROKE,high,abc,because,5\n2,CLEAN,low,none found,unrelated,4\n")
    with pytest.raises(ValueError, match="missing labels"):
        read_labels(path, expected=20)


def test_an_unrecognised_verdict_names_the_line(tmp_path: Path) -> None:
    path = _sheet(tmp_path, "1,BROKE,high,abc,because,5\n2,probably,low,x,y,4\n")
    with pytest.raises(ValueError, match=r"human_labels\.csv:3: verdict must be"):
        read_labels(path, expected=2)


def test_an_unrecognised_confidence_is_refused(tmp_path: Path) -> None:
    path = _sheet(tmp_path, "1,BROKE,certain,abc,because,5\n")
    with pytest.raises(ValueError, match="confidence must be"):
        read_labels(path, expected=1)


def test_a_missing_column_is_refused(tmp_path: Path) -> None:
    path = _sheet(
        tmp_path,
        "1,BROKE,high,abc,because\n",
        header="label_id,verdict,confidence,evidence,reasoning\n",
    )
    with pytest.raises(ValueError, match=r"missing column\(s\) \['minutes'\]"):
        read_labels(path, expected=1)


def test_a_missing_sheet_says_to_label_first(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="before the key is opened"):
        read_labels(tmp_path / "nope.csv", expected=20)


def test_verdicts_and_minutes_are_parsed(tmp_path: Path) -> None:
    path = _sheet(tmp_path, "1,broke,HIGH,sha123,it reverted,~7 min\n")
    parsed = read_labels(path, expected=1)
    assert parsed[1].verdict == "BROKE" and parsed[1].confidence == "high"
    assert parsed[1].minutes == 7.0 and parsed[1].evidence == "sha123"


def test_kappa_excludes_unsure_but_the_rate_does_not() -> None:
    """Coding UNSURE as a class would invent a judgement the labeller declined to make."""
    perfect = Agreement(
        total=20,
        agreed=18,
        both_broke=9,
        both_clean=9,
        machine_broke_human_clean=0,
        machine_clean_human_broke=0,
        unsure=2,
        minutes_median=6.0,
    )
    assert perfect.rate == 0.9  # UNSURE counted against
    assert perfect.kappa == pytest.approx(1.0)  # but excluded from kappa's 18


def test_kappa_is_below_the_rate_when_one_class_dominates() -> None:
    lopsided = Agreement(
        total=20,
        agreed=18,
        both_broke=1,
        both_clean=17,
        machine_broke_human_clean=1,
        machine_clean_human_broke=1,
        unsure=0,
        minutes_median=6.0,
    )
    assert lopsided.kappa < lopsided.rate


def test_the_confusion_matrix_totals_the_sample(tmp_path: Path) -> None:
    key = _key(20)
    labels = read_labels(
        _sheet(
            tmp_path,
            "".join(f"{i},{'BROKE' if i % 2 else 'CLEAN'},high,x,y,5\n" for i in range(1, 21)),
        ),
        expected=20,
    )
    result = score(key, labels)
    cells = (
        result.both_broke
        + result.both_clean
        + result.machine_broke_human_clean
        + result.machine_clean_human_broke
    )
    assert cells + result.unsure == result.total == 20
    assert result.agreed == 20 and result.passed


def test_no_repository_can_supply_the_whole_sample() -> None:
    """Without the cap, one project with 40 eligible PRs would be the entire gate."""
    population = [
        Candidate(
            pr_id=i,
            repo="acme/big" if i < 40 else "acme/small",
            number=i,
            merged_at="2025-03-01T00:00:00Z",
            title="t",
            commit_shas=("a" * 40,),
            changed_files=("m.py",),
        )
        for i in range(50)
    ]
    grouped = dict(_shuffled_by_repo(population, random.Random(20260804)))
    assert len(grouped["acme/big"]) == MAX_PER_REPO
    assert max(len(v) for v in grouped.values()) <= MAX_PER_REPO
