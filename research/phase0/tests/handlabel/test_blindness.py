"""Verification that the sheet cannot carry an answer to the labeller.

WHAT: Pins the two-column blind export, the URL shape it accepts, and the balance that
      makes an always-CLEAN labeller fail.
WHY:  The contamination risk in this gate is one careless column, and no test catches
      "somebody read the wrong file". So the guarantee is structural: `write_blind`
      accepts only `(int, str)` pairs, and rejects any URL richer than a plain pull
      request link -- the one route by which an answer could still be encoded.

      The balance test is the point of the stratified design. At the corpus base rate a
      random twenty holds about two broken PRs, so always-CLEAN scores ~18/20 and passes
      a gate that proved nothing. Ten of each makes it score 10/20 and fail.
IMPORTS: pytest, phase0.handlabel.{files,draw,score,labels}.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from phase0.handlabel.draw import KeyRow
from phase0.handlabel.files import BLIND_COLUMNS, read_key, write_blind, write_key
from phase0.handlabel.labels import HumanLabel
from phase0.handlabel.score import score
from phase0.handlabel.sheet import Drawn
from phase0.outcome.window import Exclusion


def _key(n_broke: int, n_clean: int) -> list[KeyRow]:
    rows = []
    for index in range(1, n_broke + n_clean + 1):
        verdict = "BROKE" if index <= n_broke else "CLEAN"
        rows.append(
            KeyRow(
                label_id=index,
                pr_id=1000 + index,
                repo="acme/widget",
                number=index,
                verdict=verdict,
                criterion="fix_touching_same_file" if verdict == "BROKE" else "none",
                evidence_sha="a" * 40 if verdict == "BROKE" else "",
            )
        )
    return rows


def _labels(verdicts: dict[int, str]) -> dict[int, HumanLabel]:
    return {
        label_id: HumanLabel(
            label_id=label_id,
            verdict=verdict,
            confidence="high",
            evidence="none found",
            reasoning="test",
            minutes=6.0,
        )
        for label_id, verdict in verdicts.items()
    }


def test_the_blind_sheet_has_exactly_two_columns(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    write_blind(path, [(1, "https://github.com/acme/widget/pull/7")])
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == list(BLIND_COLUMNS)
    assert rows[1] == ["1", "https://github.com/acme/widget/pull/7"]


def test_a_url_that_could_encode_the_answer_is_refused(tmp_path: Path) -> None:
    """A compare view or commit link would hand over the evidence the rule used."""
    for leaky in (
        "https://github.com/acme/widget/compare/aaa...bbb",
        "https://github.com/acme/widget/commit/deadbeef",
        "https://github.com/acme/widget/pull/7/files#diff-1",
    ):
        with pytest.raises(ValueError, match="plain pull-request URL"):
            write_blind(tmp_path / "s.csv", [(1, leaky)])


def test_always_clean_fails_a_balanced_sample() -> None:
    """The whole reason for stratifying. Ten of each, so a constant answer scores 10/20."""
    key = _key(n_broke=10, n_clean=10)
    result = score(key, _labels(dict.fromkeys(range(1, 21), "CLEAN")))
    assert result.agreed == 10
    assert not result.passed


def test_always_clean_would_have_passed_an_unbalanced_sample() -> None:
    """Documents the degeneracy the design removes, at the base rate it would occur at."""
    key = _key(n_broke=2, n_clean=18)
    result = score(key, _labels(dict.fromkeys(range(1, 21), "CLEAN")))
    assert result.agreed == 18 and result.passed


def test_unsure_counts_as_disagreement_and_is_reported(tmp_path: Path) -> None:
    """A forced guess is worse than an honest gap, but it is not agreement either."""
    key = _key(n_broke=10, n_clean=10)
    verdicts = {i: ("BROKE" if i <= 10 else "CLEAN") for i in range(1, 21)}
    verdicts[3] = "UNSURE"
    verdicts[15] = "UNSURE"
    result = score(key, _labels(verdicts))
    assert result.unsure == 2
    assert result.agreed == 18
    assert [d.direction for d in result.disagreements] == ["undetermined", "undetermined"]


def test_the_key_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "_key.csv"
    original = _key(n_broke=2, n_clean=2)
    write_key(path, original)
    assert read_key(path) == original


def test_disagreement_direction_names_the_fix() -> None:
    """Which way the rule erred is what decides how to change it."""
    key = _key(n_broke=10, n_clean=10)
    verdicts = {i: ("BROKE" if i <= 10 else "CLEAN") for i in range(1, 21)}
    verdicts[1] = "CLEAN"  # machine BROKE, human CLEAN -> too loose
    verdicts[20] = "BROKE"  # machine CLEAN, human BROKE -> too tight
    result = score(key, _labels(verdicts))
    assert {d.direction for d in result.disagreements} == {"rule too loose", "rule too tight"}
    assert result.machine_broke_human_clean == 1
    assert result.machine_clean_human_broke == 1


def test_a_skipped_pr_is_counted_by_reason_and_reaches_the_caller() -> None:
    """The draw must report what it passed over, not merely avoid crashing on it.

    `draw` skips PRs whose outcome could not be scanned -- they cannot enter either
    bucket, since a labeller cannot check a verdict the instrument never reached. The
    count was collected into `Drawn` and then never read by `sample_for_labelling`, which
    is the same silence as never counting it: the reason `UNSCANNABLE` exists at all is
    that a skipped unit used to be indistinguishable from a clean one.

    Kept at the accounting layer on purpose. `draw` itself clones from GitHub, and a mock
    would only prove our stub returns what we told it to; that the scan produces the right
    `Exclusion` for each case is asserted against real git in tests/outcome/test_branch.py.
    """
    drawn = Drawn(
        blind=(),
        key=(),
        seed=0,
        considered=12,
        repos_visited=3,
        unscannable={Exclusion.BASE_REF_MISSING: 2, Exclusion.MERGE_UNREACHABLE: 1},
    )

    assert drawn.skipped_total() == 3
    # Reasons stay separate: a deleted branch and a rewritten history are different facts
    # about the repository, and one number for both would report neither.
    assert drawn.unscannable[Exclusion.BASE_REF_MISSING] == 2
    assert drawn.unscannable[Exclusion.MERGE_UNREACHABLE] == 1


def test_a_draw_that_skipped_nothing_reports_zero_not_absence() -> None:
    """An empty skip set is a measurement, and must not read as "never checked"."""
    drawn = Drawn(blind=(), key=(), seed=0, considered=5, repos_visited=1)

    assert drawn.skipped_total() == 0
    assert drawn.unscannable == {}
