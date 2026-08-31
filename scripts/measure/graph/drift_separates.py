"""Does architectural drift separate the fix-return outcome, or is it churn wearing drift's name?

WHAT: `score(clone)` walks a clone's history and returns one `Scored` per library file: how many
      commits touched it, how many of those moved its import set, and how many were fix-shaped.
      `graph/drift_report.py` is the command that reads these and prints the registered bars.
WHY:  **D2e ASSERTS THAT DIVERGENCE IS MEASURABLE FROM THE IMPORT GRAPH, AND THE CATEGORY ASSERTS
      IT LOUDLY.** "Deep context beats diff-level review" names architectural drift as one of its
      four legs. A consensus is not a measurement, and the same graph this reads has already lost
      once: blast radius was pre-registered, came back INCONCLUSIVE, and prior-fix history beat it
      65-13 where they disagreed.

      **B3 IS THE BAR THAT MATTERS AND IT IS WHY `drift` IS A RATE.** A raw count of import changes
      is a proxy for "this file was edited a lot", and an edited file attracts later fixes for
      reasons that have nothing to do with architecture. Dividing by churn is the cheapest control
      available; the stratified comparison is the one that decides. **A cause that does not
      separate outcomes inside a matched stratum is a story** — `AGENTS.md` says so, and three
      fixes that moved nothing at p = 0.53 are why.

      **THE OUTCOME IS THE SHIPPED ONE, NOT A NEW ONE.** Fix-return is what the ranker is measured
      against. A new signal judged against a new outcome can be made to win by choosing the outcome.
IMPORTS: quantamind.parse.{imports,suite_reach}, quantamind.rank.events for the fix words.
      Product code only; nothing from `research/`, which rule 11 keeps out of `scripts/`.
CONSUMED BY: `scripts/measure/graph/drift_report.py`.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# `parents[3]`, not `[2]` — this moved into `graph/` when `scripts/measure/` hit its
# fifteen-file cap, and a depth index is exactly the reference AGENTS.md rule 12 warns
# about: still valid after a move, silently pointing somewhere else.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from quantamind.parse.suite_reach import is_library
from quantamind.rank.events import FIXWORDS

MIN_CHURN = 10
"""Commits a file needs before `drift` means anything. Below ten it is a ratio of small integers."""

GIT_TIMEOUT_S = 300
# **A PRINTABLE MARKER, NOT A NUL.** `subprocess` refuses an argv element containing a
# null byte outright — `ValueError: embedded null byte` — so the record separator has to
# survive being passed to git as text. This one cannot occur in a commit subject.
SEPARATOR = "@@QM-REC@@"
FIELD = "@@QM-FLD@@"


@dataclass(frozen=True, slots=True)
class Scored:
    """One file: how much it moved, how much of that was structural, how often a fix came back."""

    path: str
    churn: int
    shifts: int
    fixes: int

    @property
    def drift(self) -> float:
        return self.shifts / self.churn

    @property
    def fix_rate(self) -> float:
        return self.fixes / self.churn


def _git(clone: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(clone), *args], capture_output=True, text=True, timeout=GIT_TIMEOUT_S
    )
    # **THE EXIT CODE IS ASSERTED.** `AGENTS.md` operational notes: a truncated stream read as data
    # voided four measurements here already.
    if done.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed in {clone}: {done.stderr.strip()[:200]}")
    return done.stdout


def _imports_at(clone: Path, sha: str, path: str) -> frozenset[str] | None:
    """The module names this file imports at `sha`, or None when it will not parse.

    **NONE IS NOT AN EMPTY SET.** A file that does not parse has an UNKNOWN import set, and
    treating it as empty would score the next commit as a shift the author never made.
    """
    try:
        source = _git(clone, "show", f"{sha}:{path}")
    except RuntimeError:
        return None
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return frozenset(names)


def _history(clone: Path) -> list[tuple[str, str, list[str]]]:
    """`(sha, subject, paths)`, oldest first.

    `--full-history` for the reason `ingest/commits.read_commits` gives: a pathspec turns on
    history simplification and drops commits that really did touch the path.
    """
    raw = _git(
        clone,
        "log",
        "--reverse",
        "--no-merges",
        "--full-history",
        "--name-only",
        f"--format={SEPARATOR}%H{FIELD}%s",
    )
    out: list[tuple[str, str, list[str]]] = []
    for record in raw.split(SEPARATOR):
        if not record.strip():
            continue
        head, _, body = record.partition("\n")
        sha, _, subject = head.partition(FIELD)
        paths = [line for line in body.splitlines() if line.strip()]
        out.append((sha, subject, paths))
    return out


def score(clone: Path) -> list[Scored]:
    """Every library file with enough history to score, and its three numbers."""
    commits = _history(clone)
    touching: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for sha, subject, paths in commits:
        for path in paths:
            if is_library(path):
                touching[path].append((sha, subject))

    scored: list[Scored] = []
    for path, seen in touching.items():
        if len(seen) < MIN_CHURN:
            continue
        shifts = 0
        previous: frozenset[str] | None = None
        for sha, _ in seen:
            now = _imports_at(clone, sha, path)
            if now is None:
                continue  # unknown, not empty — see `_imports_at`
            if previous is not None and now != previous:
                shifts += 1
            previous = now
        if previous is None:
            continue  # never resolved: EXCLUDED and counted by the caller, never scored zero
        fixes = sum(1 for _, subject in seen if any(w in subject.lower() for w in FIXWORDS))
        scored.append(Scored(path, len(seen), shifts, fixes))
    return scored
