"""The pilot journal's format, and the append that writes it.

WHAT: The column schema, and one markdown table row per PR attempt flushed to disk as
      each repository closes, plus a `repo-done` marker so a restart knows where to
      pick up. Reading a journal back lives in `resume.py`.
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
IMPORTS: stdlib re, pathlib; phase0.pilot.attempt.
CONSUMED BY: pilot/run.py, pipeline/resume.py; tests/pipeline/test_journal.py.
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
    # Empty on a first scan; on a re-scan it names WHY the repository was walked again,
    # e.g. `rescan: blob_none_A29`. A repository can legitimately appear twice now, and
    # a journal that recorded the second pass without its reason would leave the next
    # reader unable to tell a re-scan from a duplicated bug.
    "rescan",
    # Which arm the row is from. Appended last, so every journal written before it reads
    # "" -- NOT MEASURED. The canonical 90-repo journal is human-arm throughout and says
    # nothing about it, and "" is the honest rendering of that: the rows do not record
    # their arm, and back-filling one would be asserting what was never written down.
    "arm",
    # GitHub's own file list, appended after `arm` for the same reason it was: every
    # journal written before these existed reads "-" = NOT MEASURED, never zero. `derived`
    # above is now "-" on rejected rows for the same reason -- it used to write 0 there,
    # which read as a measurement of nothing found.
    "gh_files",
    "gh_py",
    "gh_truncated",
    # WHY the outcome was unscannable, from `Exclusion`. Appended last, so older
    # journals read "-" = NOT MEASURED. The reason was computed and typed and then
    # dropped, so three different exclusions arrived on disk as one word.
    "exclusion",
)


def _num(value: int | None) -> str:
    """A count, or `-` when it was never measured. Never `0` for the second case."""
    return "-" if value is None else str(value)


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


def append_repo(path: Path, repo: str, attempts: list[Attempt], rescan: str = "") -> None:
    """Flush one repository's rows and mark it finished. Called once per repository.

    `rescan` is stamped on every row of this flush. Nothing is rewritten and nothing is
    removed: a repository walked a second time appends a second block, and `read_attempts`
    resolves the collision by keeping the later row. Superseding rather than deleting
    means the journal still shows that eight repositories once failed to clone, which is
    the evidence A29 rests on.
    """
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
                _num(a.derived_files),
                _num(a.changed_symbols),
                str(a.stars),
                a.outcome or "-",
                a.base_on_default,
                a.merge_on_base,
                str(a.changed_lines),
                rescan or "-",
                a.arm or "-",
                _num(a.github_changed_files),
                _num(a.github_py_files),
                "yes" if a.github_files_truncated else "no",
                a.exclusion or "-",
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
