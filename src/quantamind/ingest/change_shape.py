"""What this change looks like against what this repository normally does.

WHAT: `shape(clone, sha, changed)` returns the facts a reviewer wants before reading anything — how
      many files and lines, how that compares to the repository's own median, how many people have
      touched these files lately, how often they have changed, and when the change landed.
WHY:  **EVERY ONE OF THESE IS A FACT ABOUT HISTORY, NOT A JUDGEMENT ABOUT THE CODE.** That is the
      property that let the deterministic half of this product survive when the reviewing half did
      not: *"this pull request touches 14 files where your median is 3"* cannot be false the way
      *"this is a null dereference"* can be. Two git commands settle any line of it.

      **AND IT IS COMPARED TO THE REPOSITORY'S OWN NORMS, NEVER TO AN ABSOLUTE.** "14 files" means
      nothing on its own; "14 where your median is 3" is the whole content. The firing gate learned
      this the expensive way — an absolute threshold fired on 198 of 200 real changes, and the
      percentile version fires on 8-15%.

      **NO MODEL IS INVOLVED AND NONE CAN BE.** A model asked how unusual a change is would be
      guessing at a number git can count.

      **WHAT THIS DOES NOT DO IS PREDICT.** It describes. Whether any of these facts predicts that a
      change will need repair is a separate question with its own measurement, and until that is
      run these are context for a human rather than a signal.
IMPORTS: stdlib only. Left of rank.
CONSUMED BY: `render/shape_line.py`.
"""

from __future__ import annotations

import collections
import datetime as dt
import statistics
import subprocess
from dataclasses import dataclass
from pathlib import Path

GIT_TIMEOUT_S = 120
RECENT_DAYS = 30
SAMPLE = 300  # changes to draw the repository's own norms from


@dataclass(frozen=True, slots=True)
class Shape:
    """The change measured against its repository. Every field is countable."""

    files: int
    median_files: int
    lines: int
    median_lines: int
    hands: int
    """Distinct people who touched these same files in the last 30 days, excluding this author."""

    churn: int
    """How many times these files changed in the last 30 days."""

    when: str
    """Local weekday and hour the change landed, from the commit's own timestamp."""

    unusual: tuple[str, ...]
    """The facts that sit outside the repository's normal range. Empty is the common case."""


def _run(clone: Path, args: list[str]) -> str:
    done = subprocess.run(
        ["git", "-C", str(clone), *args], capture_output=True, text=True, timeout=GIT_TIMEOUT_S
    )
    return done.stdout if done.returncode == 0 else ""


def _norms(clone: Path) -> tuple[int, int]:
    """(median files, median lines) over the repository's recent changes."""
    text = _run(clone, ["log", f"-{SAMPLE}", "--no-merges", "--format=%x00", "--numstat"])
    files: list[int] = []
    lines: list[int] = []
    for chunk in text.split("\x00"):
        rows = [r for r in chunk.splitlines() if r.strip() and "\t" in r]
        if not rows:
            continue
        files.append(len(rows))
        total = 0
        for row in rows:
            parts = row.split("\t")
            total += sum(int(x) for x in parts[:2] if x.isdigit())
        lines.append(total)
    return (
        int(statistics.median(files)) if files else 0,
        int(statistics.median(lines)) if lines else 0,
    )


def shape(clone: Path, sha: str, changed: list[str]) -> Shape:
    """The change's own shape, and the repository's, so the first can be read against the second."""
    stat = _run(clone, ["show", "--numstat", "--format=", sha])
    lines = sum(
        int(x)
        for row in stat.splitlines()
        if "\t" in row
        for x in row.split("\t")[:2]
        if x.isdigit()
    )
    median_files, median_lines = _norms(clone)

    since = f"--since={RECENT_DAYS}.days.ago"
    author = _run(clone, ["show", "-s", "--format=%ae", sha]).strip()
    others: collections.Counter[str] = collections.Counter()
    churn = 0
    if changed:
        log = _run(
            clone,
            ["log", since, "--no-merges", "--format=%x00%ae", "--name-only", "--", *changed[:40]],
        )
        for chunk in log.split("\x00"):
            head, _, _body = chunk.partition("\n")
            if not head.strip():
                continue
            churn += 1
            if head.strip() != author:
                others[head.strip()] += 1

    # **CHURN AND HANDS ARE READ AS SHARES OF THE REPOSITORY'S OWN ACTIVITY, NOT AS COUNTS.**
    # The first version flagged "these files changed 25 times in 30 days" as unusual on three of
    # four consecutive werkzeug commits — because 25 is a large number and werkzeug is a busy
    # repository. That is an absolute threshold, which this module's own docstring warns against
    # two paragraphs above: the firing gate learned it the expensive way at 198 of 200.
    all_recent = _run(clone, ["log", since, "--no-merges", "--format=%ae"]).splitlines()
    repo_commits = len(all_recent)
    repo_hands = len({x.strip() for x in all_recent if x.strip()})

    stamp = _run(clone, ["show", "-s", "--format=%cI", sha]).strip()
    when = ""
    if stamp:
        # **`fromisoformat` REJECTS THE `Z` SUFFIX BEFORE PYTHON 3.11**, and git's `%cI` emits it
        # for UTC commits. It raised on a real repository the first time this ran on live data —
        # not in any unit test, because the fixtures all carried numeric offsets.
        try:
            moment = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError:
            moment = None
        when = f"{moment:%A} {moment:%H:%M}" if moment else ""

    odd: list[str] = []
    if median_files and len(changed) >= 3 * median_files:
        odd.append(f"{len(changed)} files against a median of {median_files}")
    if median_lines and lines >= 3 * median_lines:
        odd.append(f"{lines} lines changed against a median of {median_lines}")
    if repo_hands and len(others) >= max(2, repo_hands // 3):
        odd.append(
            f"{len(others)} of the {repo_hands} people active this month touched these files"
        )
    if repo_commits and churn >= max(5, repo_commits // 3):
        odd.append(f"these files carry {churn} of the repository's {repo_commits} recent commits")

    return Shape(
        files=len(changed),
        median_files=median_files,
        lines=lines,
        median_lines=median_lines,
        hands=len(others),
        churn=churn,
        when=when,
        unusual=tuple(odd),
    )
