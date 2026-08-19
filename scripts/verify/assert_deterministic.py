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
import shutil
import sqlite3
import subprocess
import sys
import tempfile

# Columns written from the clock rather than from the repository. Named, not pattern-matched, so
# the list cannot grow without a human adding a line here.
VOLATILE: dict[str, set[str]] = {"repo": {"first_seen"}}


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    """Every column of `table` except the wall-clock ones, in declaration order.

    Raises when a VOLATILE entry names a column the table does not have. A stale exclusion is
    worse than none: it reads as protection and hashes the clock anyway, which is the exact
    defect this whole file documents and then shipped for as long as `VOLATILE` was unused.
    """
    present = [str(r[1]) for r in conn.execute(f"PRAGMA table_info({table})")]
    drop = VOLATILE.get(table, set())
    missing = drop - set(present)
    if missing:
        raise SystemExit(
            f"[determinism] VOLATILE names {sorted(missing)} on table {table!r}, which has "
            f"{present}. The exclusion list is stale and would silence nothing."
        )
    return [c for c in present if c not in drop]


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
        columns = _columns(conn, table)
        hasher.update(f"\x00TABLE {table}({','.join(columns)})".encode())
        if not columns:
            continue
        selected = ", ".join(f'"{c}"' for c in columns)
        for row in conn.execute(f"SELECT {selected} FROM {table}"):
            hasher.update(repr(row).encode())
            rows += 1
    conn.close()
    return hasher.hexdigest()[:16], rows


def self_test(pack: pathlib.Path) -> None:
    """Prove the exclusion is LIVE against this pack, before trusting a matching digest.

    Writes a new value into a wall-clock column and requires the digest NOT to move, then into a
    real column and requires it to move. `VOLATILE` sat defined-and-unreferenced in this file
    while the docstring above claimed the exclusion existed; three fast runs inside one second
    agreed anyway and the check reported success. A digest that cannot be shown to ignore the
    clock is a digest nobody should read.
    """
    before, _ = content_digest(pack)
    conn = sqlite3.connect(pack)
    for table, columns in VOLATILE.items():
        for column in columns:
            conn.execute(f'UPDATE "{table}" SET "{column}" = "{column}" + 1')
    conn.commit()
    conn.close()
    after, _ = content_digest(pack)
    if before != after:
        raise SystemExit(
            f"[determinism] SELF-TEST FAILED: moving a wall-clock column changed the digest "
            f"({before} -> {after}), so the exclusion is not being applied."
        )
    conn = sqlite3.connect(pack)
    conn.execute("UPDATE touch SET path = path || '.x'")
    conn.commit()
    conn.close()
    if content_digest(pack)[0] == before:
        raise SystemExit(
            "[determinism] SELF-TEST FAILED: changing `touch.path` did NOT change the digest, "
            "so the hash is not reading the data it claims to compare."
        )


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
    # On a COPY: the self-test deliberately corrupts what it inspects, and the real pack is an
    # output other steps read.
    with tempfile.TemporaryDirectory() as scratch:
        probe = pathlib.Path(scratch) / "probe.db"
        shutil.copy(args.out, probe)
        self_test(probe)

    if len(digests) != 1:
        print(
            f"[determinism] {len(digests)} DIFFERENT packs over {args.runs} runs of identical "
            f"input: {sorted(digests)}",
            file=sys.stderr,
        )
        print("  A ranking that changes between runs is one nobody can audit.", file=sys.stderr)
        return 1
    excluded = ", ".join(f"{t_}.{c}" for t_, cs in VOLATILE.items() for c in sorted(cs))
    print(f"[determinism] wall-clock columns excluded by name: {excluded or '(none)'}")
    print(f"[determinism] ok — {args.runs} runs, {rows:,} rows, one digest {seen[0][0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
