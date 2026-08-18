"""Clone a real repository and build a real pack from it, for the verifiers to work on.

WHAT: Clones `--repo` (default a small, active project), reads its history through `ingest`, and
      writes a store at `--out`.
WHY:  The verifiers prove things about a PACK, and for years there was no pack, so they were never
      written and `just verify` refused to run at all. There is a pack now, and it is produced by
      the same code path the product uses rather than by a fixture — a verifier that runs against
      hand-made data proves something about the fixture.
IMPORTS: quantamind.ingest.history, quantamind.store. stdlib otherwise.
CONSUMED BY: `just verify-no-source-leak` and `just verify-determinism`.
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from quantamind.ingest.history import read_touches
from quantamind.store import schema
from quantamind.store import touches as touch_store

DEFAULT_REPO = "pallets/flask"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--clone", required=True, type=pathlib.Path)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    args = parser.parse_args(argv[1:])

    if not (args.clone / ".git").is_dir():
        done = subprocess.run(
            ["git", "clone", "-q", f"https://github.com/{args.repo}.git", str(args.clone)],
            capture_output=True,
            text=True,
            timeout=900,
        )
        if done.returncode != 0:
            print(f"[build-pack] clone of {args.repo} failed: {done.stderr[:200]}", file=sys.stderr)
            return 1

    if args.out.exists():
        args.out.unlink()
    conn = schema.open_store(args.out)
    repo_id = touch_store.ensure_repo(conn, "github.com", args.repo)
    written = touch_store.index(conn, repo_id, read_touches(args.clone, pathspec="*.py"))
    conn.close()
    if written == 0:
        print(
            f"[build-pack] {args.repo} produced an EMPTY pack; every verifier over it would "
            "pass vacuously",
            file=sys.stderr,
        )
        return 1
    print(f"[build-pack] {written:,} touches from {args.repo} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
