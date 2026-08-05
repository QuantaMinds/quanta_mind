"""An append-only markdown journal, written after every repository, resumed on restart.

WHAT: One markdown table row per PR attempt, flushed to disk as each repository closes,
      plus a `repo-done` marker so a restart knows exactly where to pick up.
WHY:  The pilot takes about two hours and the full run takes over thirty. Holding every
      result in memory until the end means a laptop lid, a network drop or a killed shell
      costs the entire run -- and the second attempt costs the same again.

      Markdown rather than JSONL because a person reads this one. Progress that can only
      be inspected by a parser does not get inspected, and the point of writing after
      every repository is that somebody can look at it while it runs.

      The marker matters more than the rows. A repository that yielded no rows -- clone
      failed, no eligible PRs -- is indistinguishable from one never attempted if only
      rows are written, so the restart would redo it forever. `repo-done` states that the
      repository was finished, which is the same distinction between silence and failure
      that the rest of this harness turns on.
IMPORTS: stdlib re, pathlib; phase0.pilot.report.
CONSUMED BY: run_pilot.py; tests/pipeline/test_journal.py.
"""

from __future__ import annotations

import re
from pathlib import Path

from phase0.pilot.attempt import Attempt

COLUMNS = (
    "repo",
    "pr_id",
    "admitted",
    "stage",
    "category",
    "commits",
    "corpus_py",
    "derived",
    "symbols",
    "stars",
    "outcome",
    "on_default",
    # Whether the merge commit is an ancestor of its own base branch. Recorded for EVERY
    # attempt, admitted or not, because the scan only ever sees the survivors: the four
    # agentops PRs that exposed this were rejected at `no_python` before any scan ran, so
    # a count taken at scan time measures the post-filter residue rather than prevalence.
    "merge_on_base",
    # additions + deletions. A20's quartile banding reads this one.
    "changed_lines",
)
# The oldest schema this reader accepts, ending at `outcome`. Everything after it was
# appended later and reads as "not measured" when a row is short. Keeps a pre-fix journal
# comparable, which an aggregate cannot do -- and only a per-PR comparison can say whether
# failures were fixed or merely moved to a different stage.
MIN_COLUMNS = 11

DONE = re.compile(r"^<!-- repo-done: (?P<repo>\S+) -->$")
HEADER = (
    "# Pilot journal\n\n"
    "Append-only. Written after every repository, so a killed run resumes here rather\n"
    "than starting over. One row per PR attempt; `repo-done` marks a finished\n"
    "repository even when it produced no rows.\n\n"
    "| " + " | ".join(COLUMNS) + " |\n"
    "|" + "|".join("---" for _ in COLUMNS) + "|\n"
)


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
    that mean NOT MEASURED -- `merge_on_base="unknown"`, `changed_lines=-1` -- rather than
    a value that could be mistaken for a measurement. A LONGER row is refused: that is a
    journal from a future schema and guessing at it would invent data.

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
                    commit_count=int(cells[5]),
                    corpus_py_files=int(cells[6]),
                    derived_files=int(cells[7]),
                    changed_symbols=int(cells[8]),
                    stars=int(cells[9]),
                    outcome="" if cells[10] == "-" else cells[10],
                    base_is_default=cells[11] != "no",
                    # Three states -- "yes", "no", "unknown" -- kept as text rather than
                    # collapsed to a bool. "we could not check" and "it is not on the
                    # branch" are different facts, and a bool would have to pick one.
                    # An absent column reads as its NOT-MEASURED value, never as a
                    # measurement: an older journal did not record these, and "unknown"
                    # and -1 are the values the rest of the analysis already excludes.
                    merge_on_base=cells[12] or "unknown",
                    changed_lines=int(cells[13]) if cells[13] else -1,
                )
            )
        except ValueError:
            continue  # a torn final line from a kill mid-write; the repo is not marked done
    return attempts


def append_repo(path: Path, repo: str, attempts: list[Attempt]) -> None:
    """Flush one repository's rows and mark it finished. Called once per repository."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        path.write_text(HEADER, encoding="utf-8")

    lines = [
        "| "
        + " | ".join(
            (
                a.repo,
                a.pr_id,
                "yes" if a.admitted else "no",
                a.stage or "-",
                a.category or "-",
                str(a.commit_count),
                str(a.corpus_py_files),
                str(a.derived_files),
                str(a.changed_symbols),
                str(a.stars),
                a.outcome or "-",
                "yes" if a.base_is_default else "no",
                a.merge_on_base,
                str(a.changed_lines),
            )
        )
        + " |"
        for a in attempts
    ]
    # The marker goes LAST, after the rows are on disk. A kill between the two loses the
    # rows and redoes the repository, which is correct; the reverse would skip it.
    lines.append(f"<!-- repo-done: {repo} -->")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
        handle.flush()
