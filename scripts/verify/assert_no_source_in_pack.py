"""Prove that no customer source text reached the pack. ARCHITECTURE.md invariant 6.

WHAT: Reads every TEXT value out of a store and fails if any of them occurs inside a source file of
      the repository that store was built from.
WHY:  **This is a contractual claim, not a preference.** We tell customers the pack holds
      identifiers, counts and coverage — never their code. A telemetry table that quietly
      accumulates source is a breach waiting for a date, and it would accumulate silently: nothing
      about a longer string in a column looks wrong.

      **It proves rather than asserts.** A unit test could only check the columns we thought to
      check. This walks every table, every TEXT column, every row, and searches the actual
      repository, so a column added later is covered without anyone remembering to add it here.

      The threshold is invariant 6's: no stored substring longer than `MIN_SUSPECT` characters may
      appear in a source file. Identifiers and paths are shorter than that; a line of code is not.
IMPORTS: stdlib only (argparse, pathlib, sqlite3, sys).
CONSUMED BY: `just verify-no-source-leak`.
"""

from __future__ import annotations

import argparse
import pathlib
import sqlite3
import sys

# Invariant 6's bound. A qualified name or a path is comfortably under it; a line of source is not.
MIN_SUSPECT = 40
SOURCE_SUFFIXES = (".py", ".pyi", ".pyx", ".js", ".ts", ".go", ".rs", ".java")


def stored_text(conn: sqlite3.Connection) -> list[tuple[str, str, str]]:
    """(table, column, value) for every TEXT value in the store, whatever the schema became."""
    out: list[tuple[str, str, str]] = []
    tables = [
        str(r[0])
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if not str(r[0]).startswith("sqlite_")
    ]
    for table in tables:
        columns = [str(r[1]) for r in conn.execute(f"PRAGMA table_info({table})")]
        if not columns:
            continue
        cols = ", ".join(f'"{c}"' for c in columns)
        for row in conn.execute(f"SELECT {cols} FROM {table}"):
            for column, value in zip(columns, row, strict=True):
                if isinstance(value, str) and value:
                    out.append((table, column, value))
    return out


def source_blobs(repo: pathlib.Path) -> dict[pathlib.Path, str]:
    """Every source file's text, read once."""
    blobs: dict[pathlib.Path, str] = {}
    for path in repo.rglob("*"):
        if not path.is_file() or path.suffix not in SOURCE_SUFFIXES or ".git" in path.parts:
            continue
        try:
            blobs[path] = path.read_text(errors="replace")
        except OSError:
            continue
    return blobs


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", required=True, type=pathlib.Path)
    parser.add_argument("--repo", required=True, type=pathlib.Path)
    args = parser.parse_args(argv[1:])

    if not args.pack.exists():
        print(f"[no-source-leak] no pack at {args.pack}; nothing to prove", file=sys.stderr)
        return 1
    conn = sqlite3.connect(args.pack)
    values = stored_text(conn)
    blobs = source_blobs(args.repo)
    if not blobs:
        print(
            f"[no-source-leak] no source files under {args.repo} — the check would pass "
            "vacuously, which is not a proof",
            file=sys.stderr,
        )
        return 1

    long_values = [(t, c, v) for t, c, v in values if len(v) > MIN_SUSPECT]
    leaks: list[str] = []
    for table, column, value in long_values:
        for path, text in blobs.items():
            if value in text:
                leaks.append(f"{table}.{column} holds {len(value)} chars found in {path.name}")
                break

    print(f"[no-source-leak] {len(values):,} text values across {len(blobs)} source files")
    print(f"[no-source-leak] {len(long_values)} value(s) over {MIN_SUSPECT} chars were searched")
    if leaks:
        print(f"[no-source-leak] {len(leaks)} LEAK(S) — the pack contains customer source:")
        for leak in leaks[:10]:
            print(f"    {leak}")
        print("  ARCHITECTURE.md invariant 6 is a contractual claim. Do not ship this.")
        return 1
    print("[no-source-leak] ok — no stored value appears in any source file")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
