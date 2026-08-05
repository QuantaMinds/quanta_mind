"""Verification that the exposure entry point refuses to run over nothing.

WHAT: Asserts the exit codes and the absence of an output file when there are no usable
      records, and that the argument surface exists at all.
WHY:  This module exists because `run_pipeline` had none. `python -m` on a module without
      a `__main__` block runs the body, ignores every flag, writes nothing and exits 0 --
      so the runbook's Days 3-5 command reported success and did nothing, and no test
      could notice because no test invoked the docs.

      The empty-records case is the one that matters. A pass over zero PRs would otherwise
      write an empty audit log, print a tidy summary of zeroes and exit 0, which is the
      same failure wearing the entry point's clothes: an absence formatted as a result. It
      must exit non-zero and name the command that produces records.

      Asserted on the real `main`, with real paths in a tmp directory, and no network:
      the refusal happens before any clone, which is precisely why it is cheap to test and
      why there is no excuse for it being untested.
IMPORTS: phase0.exposure_run.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0 import exposure_run


def test_no_records_file_exits_non_zero_and_writes_nothing(tmp_path: Path) -> None:
    """ "Nothing to do" and "done" must not be the same exit code."""
    out = tmp_path / "exposure.jsonl"

    code = exposure_run.main(
        [
            "--records",
            str(tmp_path / "absent.jsonl"),
            "--out",
            str(out),
            "--workspace",
            str(tmp_path / "ws"),
        ]
    )

    assert code == 2
    assert not out.exists(), "an empty audit log is indistinguishable from a completed run"


def test_a_records_file_of_only_unusable_lines_is_also_refused(tmp_path: Path) -> None:
    """A file that exists but yields no complete record is empty for our purposes.

    `records_file.read` drops records missing a field the later stages depend on, so a
    non-empty file can still produce zero usable PRs -- and that must reach the same
    refusal as a missing file rather than starting a pass over nothing.
    """
    records = tmp_path / "records.jsonl"
    records.write_text('{"pr_id": "1", "repo": "o/r"}\nnot json at all\n', encoding="utf-8")
    out = tmp_path / "exposure.jsonl"

    code = exposure_run.main(
        ["--records", str(records), "--out", str(out), "--workspace", str(tmp_path / "ws")]
    )

    assert code == 2
    assert not out.exists()


def test_the_argument_surface_exists(tmp_path: Path) -> None:
    """The whole defect was a module with no arguments that accepted every flag."""
    args = exposure_run.parse(
        ["--records", "r.jsonl", "--out", "o.jsonl", "--workspace", "w", "--timeout", "42"]
    )

    assert (args.records, args.out, args.timeout) == (Path("r.jsonl"), Path("o.jsonl"), 42)
    assert args.pilot is False


def test_an_unknown_flag_is_rejected_rather_than_ignored(tmp_path: Path) -> None:
    """`python -m` on a module without argparse swallowed every flag silently."""
    with pytest.raises(SystemExit):
        exposure_run.parse(["--not-a-real-flag"])


def test_from_journal_is_offered_when_no_records_exist(tmp_path: Path) -> None:
    """The corpus was measured before `--records` existed, so this path is not optional.

    Re-running the pilot cannot recover them: it resumes from the journal, finds every
    repository done, and writes nothing. The message must name the way out, because the
    alternative a reader would reach for does not work.
    """
    args = exposure_run.parse(["--from-journal", "j.md"])

    assert args.from_journal == Path("j.md")


def test_the_refusal_names_both_ways_out(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    """A refusal that does not say what to do next gets worked around, not obeyed."""
    exposure_run.main(
        [
            "--records",
            str(tmp_path / "absent.jsonl"),
            "--out",
            str(tmp_path / "o.jsonl"),
            "--workspace",
            str(tmp_path / "ws"),
        ]
    )

    message = capsys.readouterr().err
    assert "--from-journal" in message
    assert "pilot.run --records" in message
