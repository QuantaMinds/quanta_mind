"""Verification that the gate refuses to certify what it did not measure.

WHAT: Pins label parsing (incomplete sheets refused), the pre-registered >=16/20
      threshold, and the single-class degeneracy that raw agreement cannot see.
WHY:  Raw agreement on an all-clean sample is 20/20 for a classifier that always
      answers "clean". `controls/analysis.py` already refuses that shape in the
      negative controls; it reappears here at a different layer, so kappa is reported
      beside the gate and a single-class sample is labelled as uninformative.
IMPORTS: pytest, phase0.handlabel.{score,select}, phase0.scan_outcome.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0.handlabel.score import GATE_MINIMUM, Agreement, read_labels, score
from phase0.handlabel.select import Candidate, Selection, select_prs
from phase0.scan_outcome import Outcome

PACKAGE = Path(__file__).resolve().parents[2] / "data" / "AIDev_BC_Analyser.zip"


def _candidate(index: int) -> Candidate:
    return Candidate(
        pr_id=1000 + index,
        repo="acme/widget",
        number=index,
        merged_at="2025-03-01T00:00:00Z",
        title=f"change {index}",
        commit_shas=("a" * 40,),
        changed_files=("acme/widget.py",),
    )


def _selection(count: int = 20) -> Selection:
    return Selection(
        candidates=tuple(_candidate(i) for i in range(1, count + 1)),
        population=count * 3,
        stride=3,
        manifest_sha256="deadbeef",
    )


def test_partial_labels_are_refused(tmp_path: Path) -> None:
    """Scoring only what was labelled would let the gate be met on the easy ones."""
    path = tmp_path / "answers.txt"
    path.write_text("1: broke\n2: clean\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing labels"):
        read_labels(path, expected=20)


def test_a_malformed_line_names_the_line(tmp_path: Path) -> None:
    path = tmp_path / "answers.txt"
    path.write_text("1: broke\n2: probably?\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"answers\.txt:2"):
        read_labels(path, expected=2)


def test_missing_answers_file_says_to_label_first(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="labels must exist before"):
        read_labels(tmp_path / "nope.txt", expected=20)


def test_comments_and_blank_lines_are_allowed(tmp_path: Path) -> None:
    path = tmp_path / "answers.txt"
    path.write_text("# my notes\n\n1: broke\n2. clean\n", encoding="utf-8")
    assert read_labels(path, expected=2) == {1: Outcome.BROKE, 2: Outcome.CLEAN}


def test_a_single_class_sample_is_flagged_rather_than_passed() -> None:
    """20/20 on an all-clean sample is what "always answer clean" scores.

    The gate still reports PASS because `PHASE0_PREREGISTRATION.md` “Timeline” threshold is not
    modified here, but the
    report must carry the warning beside it or the number reads as evidence.
    """
    selection = _selection()
    labels = dict.fromkeys(range(1, 21), Outcome.CLEAN)
    result = score(selection, labels, dict(labels))
    assert result.passed and result.agreed == 20
    assert not result.is_discriminating
    assert "always answers the same way" in result.describe()


def test_a_mixed_sample_is_discriminating_and_kappa_is_finite() -> None:
    selection = _selection()
    human = {i: (Outcome.BROKE if i <= 6 else Outcome.CLEAN) for i in range(1, 21)}
    machine = {i: (Outcome.BROKE if i <= 5 else Outcome.CLEAN) for i in range(1, 21)}
    result = score(selection, human, machine)
    assert result.is_discriminating and result.passed
    assert result.agreed == 19 and 0.0 < result.kappa < 1.0


def test_kappa_is_below_raw_agreement_when_one_class_dominates() -> None:
    """The correction that makes the degeneracy visible as a number."""
    result = Agreement(
        total=20, agreed=18, human_broke=1, machine_broke=1, both_broke=0, manifest_sha256=""
    )
    assert result.rate == 0.9
    assert result.kappa < result.rate


def test_the_gate_threshold_is_the_pre_registered_one() -> None:
    """A boundary this document forbids moving. Pinned so a refactor cannot drift it."""
    assert GATE_MINIMUM == 16


@pytest.mark.skipif(not PACKAGE.is_file(), reason="replication package not downloaded")
def test_selection_is_deterministic_and_spread_on_the_real_package() -> None:
    """Same package, same twenty, same hash — and drawn across the range, not the head."""
    first = select_prs(PACKAGE)
    second = select_prs(PACKAGE)
    assert first.manifest_sha256 == second.manifest_sha256
    assert len(first.candidates) == 20
    assert first.stride > 1, "a stride of 1 would draw one narrow slice of calendar time"
    assert len({c.repo for c in first.candidates}) > 1
    assert all(c.commit_shas and c.changed_files for c in first.candidates)
