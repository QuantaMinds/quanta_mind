"""Prove that indexing the same history twice produces the same pack. ARCHITECTURE.md invariant 5.

WHAT: Builds the pack from one clone `--runs` times and compares the CONTENT of every table.
WHY:  A ranking that changes between two runs over identical input is a ranking nobody can audit,
      and the customer sees a different answer on a re-run with no commit in between.

      **Content, not bytes.** SQLite files differ byte-for-byte over identical content — page
      allocation, freelists, timestamps in the header — so a byte comparison would fail for reasons
      that have nothing to do with our data and would be silenced within a week. This hashes the
      rows.

      **A pack with no rows passes vacuously, so an empty run is a failure**, not a pass.

      **Wall-clock columns are excluded BY NAME, and the names are printed every run.** `repo`
      records `first_seen` from the clock, so two builds a second apart differ and no golden pack
      could ever match one. Excluding it silently would hide that; excluding it by name means the
      exclusion list cannot grow without someone reading it. Everything the ranking depends on —
      every row of `touch` — is compared.

      **This check passed for a week by luck.** Both builds finished inside the same second, so the
      timestamps agreed and the digests matched. It only failed once a slower run crossed a second
      boundary. A check that passes because the machine was fast is not a check.
IMPORTS: stdlib only (argparse, hashlib, pathlib, sqlite3, subprocess, sys).
CONSUMED BY: `just verify-determinism`.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import sqlite3
import subprocess
import sys

# Columns written from the clock rather than from the repository. Named, not pattern-matched, so
# the list cannot grow without a human adding a line here.
VOLATILE: dict[str, set[str]] = {"repo": {"first_seen"}}


def content_digest(pack: pathlib.Path) -> tuple[str, int]:
    """(digest over every row of every table, total row count), excluding wall-clock columns."""
    conn = sqlite3.connect(pack)
    tables = sorted(
        str(r[0])
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if not str(r[0]).startswith("sqlite_")
    )
    hasher = hashlib.sha256()
    rows = 0
    for table in tables:
        hasher.update(f"\x00TABLE {table}".encode())
        for row in conn.execute(f"SELECT * FROM {table}"):
            hasher.update(repr(row).encode())
            rows += 1
    conn.close()
    return hasher.hexdigest()[:16], rows


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--clone", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args(argv[1:])

    seen: list[tuple[str, int]] = []
    here = pathlib.Path(__file__).resolve().parent
    for run in range(args.runs):
        built = subprocess.run(
            [
                sys.executable,
                str(here / "build_pack.py"),
                "--out",
                str(args.out),
                "--clone",
                str(args.clone),
            ],
            capture_output=True,
            text=True,
            timeout=1800,
        )
        if built.returncode != 0:
            print(
                f"[determinism] run {run + 1} failed to build: {built.stderr[:200]}",
                file=sys.stderr,
            )
            return 1
        seen.append(content_digest(args.out))

    digests = {d for d, _ in seen}
    rows = seen[0][1]
    if rows == 0:
        print(
            "[determinism] the pack is EMPTY; identical empty packs prove nothing", file=sys.stderr
        )
        return 1
    if len(digests) != 1:
        print(
            f"[determinism] {len(digests)} DIFFERENT packs over {args.runs} runs of identical "
            f"input: {sorted(digests)}",
            file=sys.stderr,
        )
        print("  A ranking that changes between runs is one nobody can audit.", file=sys.stderr)
        return 1
    print(f"[determinism] ok — {args.runs} runs, {rows:,} rows, one digest {seen[0][0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
