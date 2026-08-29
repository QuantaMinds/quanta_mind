"""Clone, score and discard each pre-registered repository in turn.

WHAT: Walks the six repositories named in `blast-radius-preregistration.md`, collects rows with
      `predicts.collect`, writes them per repository, and removes the clone before the next.
WHY:  **ONE CLONE AT A TIME, BECAUSE THE DISK IS THE BINDING CONSTRAINT.** These are large
      repositories and the machine has single-digit gigabytes free; a previous experiment in this
      project was blocked outright by needing 4.5 GB against 2.8 GB free. Rows are kilobytes, so
      keeping the rows and discarding the clone is the shape that fits.

      **A REPOSITORY THAT FAILS IS RECORDED, NOT SKIPPED.** Five repositories reported as six is
      the corpus silently shrinking, which the pre-registration names as a way this run could
      mislead. Each outcome is written to the manifest whether it succeeded or not.

      **NO `--filter=blob:none`.** A blob-filtered clone fetches on demand, and this reads a whole
      tree at hundreds of historical commits — it would be slower than the disk saving is worth,
      and `AGENTS.md` records that blob-filtered clones already broke one class of read here.
IMPORTS: stdlib, and `predicts` beside it.
CONSUMED BY: an operator, by hand.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from predicts import collect

CLONE_TIMEOUT_S = 1800
REPOS = (
    "sqlalchemy/sqlalchemy",
    "numpy/numpy",
    "scipy/scipy",
    "matplotlib/matplotlib",
    "pytest-dev/pytest",
    "encode/django-rest-framework",
)


def clone(repo: str, into: Path) -> bool:
    done = subprocess.run(
        ["git", "clone", "--quiet", "--single-branch", f"https://github.com/{repo}.git", str(into)],
        capture_output=True,
        text=True,
        timeout=CLONE_TIMEOUT_S,
    )
    if done.returncode != 0:
        print(f"  clone failed: {done.stderr.strip()[:160]}", flush=True)
    return done.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=600, help="events per repository")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    args.workdir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, object] = {}
    for repo in REPOS:
        name = repo.replace("/", "_")
        into = args.workdir / name
        print(f"\n=== {repo} ===", flush=True)
        if into.exists():
            shutil.rmtree(into)
        if not clone(repo, into):
            manifest[repo] = {"status": "clone_failed", "rows": 0, "events": 0}
            continue
        try:
            rows = collect(into, args.limit)
            (args.out / f"{name}.json").write_text(json.dumps([asdict(r) for r in rows], indent=1))
            manifest[repo] = {
                "status": "ok",
                "rows": len(rows),
                "events": len({r.at for r in rows}),
            }
            print(f"  {len(rows)} rows from {len({r.at for r in rows})} events", flush=True)
        except Exception as broken:
            manifest[repo] = {"status": f"failed: {type(broken).__name__}: {broken}"[:200]}
            print(f"  FAILED: {broken}", flush=True)
        finally:
            shutil.rmtree(into, ignore_errors=True)
        (args.out / "manifest.json").write_text(json.dumps(manifest, indent=1))

    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print("\n=== manifest ===")
    for repo, got in manifest.items():
        print(f"  {repo:<34} {got}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
