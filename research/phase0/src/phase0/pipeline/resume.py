"""Reading a pilot journal back: what a restart already knows.

WHAT: `completed_repos` and `read_attempts` -- the journal as an input, plus the
      last-wins rule that resolves a repository walked twice.
WHY:  Split from `journal.py`, which owns the format and the append. Writing a row and
      reconstructing a half-finished run from rows are different jobs: the writer only
      has to render the current schema, while this side has to read journals written by
      every schema that came before it and decide what an absent column means.

      That asymmetry is the whole reason the split is worth making. Every rule here is
      about interpreting silence -- a short row is an older schema, an absent column is
      NOT MEASURED and never a value, a torn final line is a kill mid-write and not a
      data point, a repeated (repo, pr_id) is a re-scan superseding rather than a
      duplicate to count twice. None of that belongs next to a `"\\n".join`.
IMPORTS: stdlib pathlib; phase0.pilot.attempt, phase0.pipeline.journal (its schema).
CONSUMED BY: pilot/run.py, pilot/targets.py, pilot/compare.py, pipeline/rebuild.py;
      tests/pipeline/test_journal.py, tests/pilot/test_targets.py.
"""

from __future__ import annotations

from pathlib import Path

from phase0.pilot.attempt import Attempt
from phase0.pipeline.journal import COLUMNS, DONE, MIN_COLUMNS


def completed_repos(path: Path) -> set[str]:
    """Repositories already finished. A restart skips these."""
    if not path.is_file():
        return set()
    found: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        marker = DONE.match(line.strip())
        if marker:
            found.add(marker.group("repo"))
    return found


def read_attempts(path: Path) -> list[Attempt]:
    """Every attempt recorded so far, so the report covers the whole run.

    Reads journals written before the newer columns existed. Columns are only ever
    appended, so a shorter row is an older schema and the absent fields take the values
    that mean NOT MEASURED -- `merge_on_base="unknown"`, `changed_lines=-1`, `arm=""` --
    rather than a value that could be mistaken for a measurement. A LONGER row is
    refused: that is a journal from a future schema and guessing at it would invent data.

    This exists so a pre-fix journal remains comparable. Without it the only baseline is
    an aggregate, and an aggregate cannot say whether failures were fixed or merely moved
    to another stage -- which is the question a large drop in one stage always raises.
    """
    if not path.is_file():
        return []
    attempts: list[Attempt] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| repo "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not MIN_COLUMNS <= len(cells) <= len(COLUMNS) or cells[0] == "---":
            continue
        cells += [""] * (len(COLUMNS) - len(cells))
        try:
            attempts.append(
                Attempt(
                    repo=cells[0],
                    pr_id=cells[1],
                    admitted=cells[2] == "yes",
                    # An admitted row has no stage; the writer renders that as `-` so the
                    # table stays readable, so the reader has to invert it. Without this
                    # a resumed run reads its own admitted rows back as stage="-", and
                    # the final report grows a rejection category that never happened.
                    stage="" if cells[3] == "-" else cells[3],
                    category="" if cells[4] == "-" else cells[4],
                    # POSITIONAL, AND THAT MAKES THIS FILE A SCHEMA LOCK ON A LIVE WALK.
                    # Every field below is read by INDEX, and the journal is the resume
                    # checkpoint: a walk killed at hour four re-enters here and continues
                    # appending. So inserting or reordering a column mid-walk writes two
                    # different shapes into one file, and the rows written under the old
                    # shape then parse into the wrong fields rather than failing -- the
                    # `except ValueError: continue` at the bottom only catches a torn
                    # line, not a well-formed line of the wrong width read one column off.
                    #
                    # Append at the END, never in the middle, and never while a walk is
                    # running. This is the same reason `run_pipeline.run` documents its
                    # serial-over-repositories loop: a property nothing enforces, that
                    # costs a re-run when broken. There is no guard for it.
                    commit_count=int(cells[5]),
                    corpus_py_files=int(cells[6]),
                    # `-` is NOT MEASURED and must not read back as 0. Older journals wrote
                    # a literal 0 on every rejected row, so those still read 0 -- that is
                    # what they recorded, and inventing None for them would assert a
                    # distinction the file never made.
                    derived_files=_count(cells[7]),
                    changed_symbols=_count(cells[8]),
                    stars=int(cells[9]),
                    outcome="" if cells[10] == "-" else cells[10],
                    # Three states, not a bool. An older journal wrote only yes/no and both
                    # are measurements; an EMPTY cell is a journal that did not record it,
                    # and "unknown" is what the report excludes rather than counts.
                    base_on_default=cells[11] or "unknown",
                    # Three states -- "yes", "no", "unknown" -- kept as text rather than
                    # collapsed to a bool. "we could not check" and "it is not on the
                    # branch" are different facts, and a bool would have to pick one.
                    # An absent column reads as its NOT-MEASURED value, never as a
                    # measurement: an older journal did not record these, and "unknown"
                    # and -1 are the values the rest of the analysis already excludes.
                    merge_on_base=cells[12] or "unknown",
                    changed_lines=int(cells[13]) if cells[13] else -1,
                    # "" for every journal written before the column existed, which is
                    # all of them including the canonical 90-repo one. That journal is
                    # human-arm throughout and records nothing about it; back-filling
                    # "Human" here would assert what was never written down.
                    arm="" if cells[15] == "-" else cells[15],
                    github_changed_files=_count(cells[16]),
                    github_py_files=_count(cells[17]),
                    github_files_truncated=cells[18] == "yes",
                    exclusion="" if cells[19] == "-" else cells[19],
                )
            )
        except ValueError:
            continue  # a torn final line from a kill mid-write; the repo is not marked done
    return _last_wins(attempts)


def _count(cell: str) -> int | None:
    """A recorded count, or None when the journal did not record one.

    `-` and an absent column are both NOT MEASURED. Returning 0 for either is the bug this
    exists to prevent: it makes "derivation found nothing" and "derivation never ran" the
    same value, and the second is what every rejected row actually was.
    """
    return int(cell) if cell and cell != "-" else None


def _last_wins(attempts: list[Attempt]) -> list[Attempt]:
    """One row per (repo, pr_id) -- the LAST, because a re-scan supersedes.

    A `--only-repo` pass appends a second block for a repository that is already in the
    journal. Returning both would double-count it, and the eight repositories a re-scan
    exists for are precisely the ones whose first block says `clone_failed` -- so the
    duplicate would reinstate the attrition the re-scan removed, in the arm that decides
    A16's confounder. Insertion order is preserved so the report still reads as a walk.
    """
    latest: dict[tuple[str, str], Attempt] = {}
    for attempt in attempts:
        latest[(attempt.repo, attempt.pr_id)] = attempt
    return list(latest.values())
