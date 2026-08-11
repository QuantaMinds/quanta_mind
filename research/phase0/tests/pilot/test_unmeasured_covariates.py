"""NOT MEASURED must never be recorded as a measurement of zero.

WHAT: Pins `derived_files`/`changed_symbols` as None on rows where derivation did not
      run, the one stage where zero IS the measurement, the journal's round trip of
      both, and that a band drops an unmeasured row instead of banding it.
WHY:  `covariates.attempt_for` initialised these to 0 and overwrote them only on the
      admitted branch, so EVERY rejected row recorded 0. The count of rows reading
      `derived_files == 0` was then arithmetically identical to the count of rejected
      rows -- the same objects, not merely the same total -- and the field could not
      answer "did derivation work", which is the question it looks like it answers.

      `no_python` is the sole exception and is asserted separately: `assemble.py`'s
      `if not derived` IS that rejection, so zero there is a fact. A `no_symbols` row
      cannot have derived zero, because that branch runs only when `derived` is
      non-empty -- yet it recorded 0 like the rest, which is how a `no_symbols`
      rejection came to be cited as evidence of a derivation defect that did not exist.

      `test_a_zero_would_be_indistinguishable_from_rejection` is the guard on the guard:
      it recomputes the identity that made the original bug invisible, so if these fields
      ever go back to 0 the suite says so rather than passing quietly.
IMPORTS: phase0.pilot.covariates, phase0.pilot.attempt, phase0.pipeline.journal,
      phase0.pipeline.resume, phase0.pipeline.rejection, phase0.handlabel.select,
      phase0.extract_prs, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

from phase0.extract_prs import PRRecord
from phase0.handlabel.select import Candidate
from phase0.pilot.covariates import attempt_for
from phase0.pilot.report import FILE_BANDS, _cross
from phase0.pipeline import journal, resume
from phase0.pipeline.rejection import Rejection

CORPUS_FILES = ("a/b.py", "a/c.py", "README.md")


def _candidate(pr_id: int = 1) -> Candidate:
    return Candidate(
        pr_id=pr_id,
        repo="o/r",
        number=pr_id,
        merged_at="2026-03-01T12:00:00Z",
        title="t",
        commit_shas=("s",),
        changed_files=CORPUS_FILES,
    )


def _record() -> PRRecord:
    return PRRecord(
        pr_id="1",
        repo="o/r",
        language="python",
        parent_sha="0" * 40,
        merged_sha="1" * 40,
        merged_at="2026-03-01T12:00:00Z",
        changed_files=("a/b.py",),
        changed_symbols=("a.b.f",),
    )


def test_a_rejected_row_records_none_not_zero() -> None:
    """`no_symbols` derived files; it cannot have derived zero, and must not say so."""
    row = attempt_for(_candidate(), Rejection("1", "no_symbols", "no bodies"), 3, stars=1)
    assert (row.derived_files, row.changed_symbols, row.stage) == (None, None, "no_symbols")


def test_no_python_records_a_real_zero() -> None:
    """The one stage where zero is a measurement: `if not derived` IS the rejection."""
    row = attempt_for(_candidate(), Rejection("1", "no_python", "no .py"), 3, stars=1)
    assert row.derived_files == 0
    assert row.changed_symbols is None, "symbols were never counted; that is not zero"


def test_an_admitted_row_records_what_was_measured() -> None:
    row = attempt_for(_candidate(), _record(), 3, stars=1)
    assert row.derived_files == 1
    assert row.changed_symbols == 1


def test_github_file_list_is_recorded_and_never_flagged_truncated() -> None:
    """The list was used by `verify_files` and dropped; the row now keeps it.

    This test previously asserted a 100-entry list was `truncated=True`, which was right
    while `github_pulls` fetched one page deep. `fetch_all` now walks every page and
    RAISES rather than returning a short list, so a full-page list is complete and the
    flag is False. The old assertion was pinning the truncation, not the recording.
    """
    row = attempt_for(_candidate(), _record(), 3, stars=1, api_files=("x.py", "y.md", "z.py"))
    assert (row.github_changed_files, row.github_py_files) == (3, 2)
    assert row.github_files_truncated is False

    full_page = attempt_for(
        _candidate(), _record(), 3, stars=1, api_files=tuple(f"f{i}.py" for i in range(100))
    )
    assert (full_page.github_changed_files, full_page.github_files_truncated) == (100, False)


def test_absent_github_list_is_none_not_zero() -> None:
    """`()` would claim GitHub reported zero files. It reported nothing."""
    row = attempt_for(_candidate(), _record(), 3, stars=1, api_files=None)
    assert (row.github_changed_files, row.github_py_files, row.github_files_truncated) == (
        None,
        None,
        False,
    )


def test_journal_round_trips_unmeasured_as_unmeasured(tmp_path: Path) -> None:
    """A `-` written must read back None, never 0."""
    path = tmp_path / "j.md"
    rejected = attempt_for(_candidate(1), Rejection("1", "no_symbols", "x"), 3, stars=1)
    admitted = attempt_for(_candidate(2), _record(), 3, stars=1, api_files=("x.py", "y.md"))
    journal.append_repo(path, "o/r", [rejected, admitted])

    back = {a.pr_id: a for a in resume.read_attempts(path)}
    assert back["1"].derived_files is None
    assert back["1"].changed_symbols is None
    assert back["2"].derived_files == 1
    assert back["2"].github_changed_files == 2
    assert back["2"].github_py_files == 1


def test_a_band_drops_an_unmeasured_row_rather_than_banding_it() -> None:
    """None must not land in a band. It is not a small PR; it is an unknown one."""
    measured = attempt_for(_candidate(1), _record(), 3, stars=1, api_files=("x.py",))
    unmeasured = attempt_for(_candidate(2), _record(), 3, stars=1, api_files=None)
    banded = _cross([measured, unmeasured], FILE_BANDS, "github_py_files")
    assert sum(int(b["n"]) for b in banded.values()) == 1


def test_a_zero_would_be_indistinguishable_from_rejection() -> None:
    """The identity that hid the original bug, asserted so it cannot return.

    With the old behaviour every rejected row read 0, so "rows reading zero" and "rows
    rejected" were the same set. If that identity ever holds again, the field has stopped
    measuring derivation and this test is the thing that notices.
    """
    rows = [
        attempt_for(_candidate(1), _record(), 3, stars=1),
        attempt_for(_candidate(2), Rejection("2", "no_symbols", "x"), 3, stars=1),
        attempt_for(_candidate(3), Rejection("3", "parent_commit", "x"), 3, stars=1),
    ]
    rejected = {r.pr_id for r in rows if not r.admitted}
    reading_zero = {r.pr_id for r in rows if r.derived_files == 0}
    assert reading_zero != rejected
    assert reading_zero == set()
