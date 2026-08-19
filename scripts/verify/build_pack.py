"""Clone a real repository and build a real pack from it, for the verifiers to work on.

WHAT: Clones `--repo` (default a small, active project), reads its history through `ingest`, and
      writes a store at `--out`.
WHY:  The verifiers prove things about a PACK, and for years there was no pack, so they were never
      written and `just verify` refused to run at all. There is a pack now, and it is produced by
      the same code path the product uses rather than by a fixture — a verifier that runs against
      hand-made data proves something about the fixture.
      **THE CORPUS IS PINNED.** It used to clone `pallets/flask` at HEAD into a gitignored
      directory, so the pack differed between machines and between weeks -- `main` moved on
      2026-08-16 -- and `just verify-data` could never have had a golden to diff against. The
      commit is named in `scripts/verify/pinned_clone.json` and verified after cloning; an
      unreachable pin stops the build rather than falling back to whatever the branch points at.
IMPORTS: quantamind.ingest.history, quantamind.store; scripts/fixtures/clone_pinned.
      stdlib otherwise.
CONSUMED BY: `just verify-no-source-leak` and `just verify-determinism`.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
# The pinning mechanism is shared with `just fixtures` rather than written twice: two
# implementations of "clone at a commit and verify it landed" drift, and only one of them keeps
# the verification. No intermediate variable: an assignment before the imports is CODE, and ruff
# then flags every import after it as E402.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts" / "fixtures"))

from clone_pinned import FixtureCloneFailed, pin

from quantamind.ingest.history import read_touches
from quantamind.store import schema
from quantamind.store import touches as touch_store

MANIFEST = pathlib.Path(__file__).resolve().parent / "pinned_clone.json"
DEFAULT_REPO = "pallets/flask"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--clone", required=True, type=pathlib.Path)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    args = parser.parse_args(argv[1:])

    spec = json.loads(MANIFEST.read_text())
    if args.repo != spec["repo"]:
        print(
            f"[build-pack] --repo {args.repo} but the manifest pins {spec['repo']}. A pack built "
            f"from a different corpus cannot be diffed against the golden.",
            file=sys.stderr,
        )
        return 1
    try:
        # checkout=True: the source-leak check searches this clone's files.
        _name, sha, fresh = pin(spec["repo"], spec["sha"], spec["url"], args.clone, checkout=True)
    except FixtureCloneFailed as exc:
        print(f"[build-pack] {exc}", file=sys.stderr)
        return 1
    print(
        f"[build-pack] corpus {spec['repo']} @ {spec['ref']} ({sha[:12]}), "
        f"{'cloned' if fresh else 'already pinned'}"
    )

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
