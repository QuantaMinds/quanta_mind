"""Blast radius against the fix-return outcome, on the definition that carries the p-value.

WHAT: For every admissible event, records each changed file's prior fix count, its import
      in-degree at that commit, and whether a later fix returned to it.
WHY:  **THE EVENT DEFINITION IS IMPORTED, NEVER RESTATED.** `rank/events.admissible` carries the
      published claim — 1.21% against 3.12%, n = 2,400 — and its own docstring records that the
      definition was written out twice before and the two copies drifted. A third copy here would
      report a number that resembles the published one and is not it.

      **THE GRAPH IS BUILT AT THE EVENT'S OWN COMMIT, NOT AT HEAD.** In-degree today includes
      importers added after the fix we are trying to predict, which is the future leaking into a
      feature — the defect `change_shape`'s window had, wrong in both directions on real clones.
IMPORTS: stdlib, quantamind.{ingest,rank,parse}.
CONSUMED BY: an operator, by hand.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from quantamind.ingest.commits import read_commits
from quantamind.parse.imports import edges
from quantamind.rank.events import admissible

GIT_TIMEOUT_S = 120


@dataclass(frozen=True, slots=True)
class Row:
    """One changed file in one event: two predictors and the outcome."""

    at: int
    path: str
    prior_fixes: int
    importers: int
    returned: bool


def _shas_by_time(clone: Path) -> dict[int, str]:
    out = subprocess.run(
        ["git", "-C", str(clone), "log", "--no-merges", "--format=%ct %H"],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_S,
        check=True,
    )
    found: dict[int, str] = {}
    for line in out.stdout.splitlines():
        when, _, sha = line.partition(" ")
        found.setdefault(int(when), sha)
    return found


def _tree(clone: Path, sha: str) -> list[tuple[str, str]]:
    """`(oid, path)` for every `.py` file in the tree at `sha`."""
    out = subprocess.run(
        ["git", "-C", str(clone), "ls-tree", "-r", sha],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_S,
        check=True,
    )
    found: list[tuple[str, str]] = []
    for line in out.stdout.splitlines():
        meta, _, path = line.partition("\t")
        if path.endswith(".py"):
            found.append((meta.split()[2], path))
    return found


def _sources(clone: Path, blobs: list[tuple[str, str]]) -> dict[str, str]:
    """Every blob's text in ONE `git cat-file --batch`.

    **A `git show` PER FILE IS WHAT MAKES THIS UNRUNNABLE AT SCALE.** A repository with 600 Python
    files costs 600 processes per event, and this walks hundreds of events across six repositories.

    **THE STREAM IS PARSED AS BYTES, BECAUSE GIT'S SIZE IS IN BYTES.** The first version decoded
    first and sliced a `str` by those counts, so a single non-ASCII character shifted every
    following offset and the parser read blob contents as headers. It happened to crash on
    sqlalchemy; had it not, the import graph would have been quietly wrong from that byte on.
    """
    if not blobs:
        return {}
    done = subprocess.run(
        ["git", "-C", str(clone), "cat-file", "--batch"],
        input="\n".join(oid for oid, _ in blobs).encode(),
        capture_output=True,
        timeout=GIT_TIMEOUT_S * 5,
    )
    out: dict[str, str] = {}
    body: bytes = done.stdout
    at = 0
    for _oid, path in blobs:
        head, sep, _rest = body[at:].partition(b"\n")
        if not sep:
            break
        parts = head.split()
        if len(parts) != 3 or not parts[2].isdigit():
            break
        size = int(parts[2])
        start_at = at + len(head) + 1
        out[path] = body[start_at : start_at + size].decode("utf-8", "replace")
        at = start_at + size + 1
    return out


def in_degree(clone: Path, sha: str) -> Counter[str]:
    """How many files in the tree import each file, AT `sha`. Empty when the tree cannot be read."""
    blobs = _tree(clone, sha)
    tree = frozenset(path for _oid, path in blobs)
    text = _sources(clone, blobs)
    degree: Counter[str] = Counter()
    for _oid, path in blobs:
        found, _ = edges(path, text.get(path, ""), tree)
        for edge in found:
            if edge.target and edge.target != path:
                degree[edge.target] += 1
    return degree


def collect(clone: Path, limit: int) -> list[Row]:
    commits = read_commits(clone, "*.py")
    when = _shas_by_time(clone)
    fixes: Counter[str] = Counter()
    rows: list[Row] = []
    seen = 0
    for event in admissible(commits):
        sha = when.get(event.at, "")
        if not sha:
            continue
        degree = in_degree(clone, sha)
        for path in sorted(event.paths):
            rows.append(Row(event.at, path, fixes[path], degree.get(path, 0), path in event.target))
        for path in event.target:
            fixes[path] += 1
        seen += 1
        print(f"  event {seen}/{limit} at {event.at} — {len(event.paths)} file(s)", flush=True)
        if seen >= limit:
            break
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clone", type=Path, required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = collect(args.clone, args.limit)
    args.out.write_text(json.dumps([asdict(r) for r in rows], indent=1))
    print(f"\n{len(rows)} file-rows from {len({r.at for r in rows})} events -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
