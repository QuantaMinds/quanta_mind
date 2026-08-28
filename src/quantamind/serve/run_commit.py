"""`quantamind review` — rank one commit from a local clone and print what we would say.

WHAT: `review_commit(clone, repo, sha)` resolves the commit's changed files and timestamp, runs the
      ranking against history strictly before it, and writes the comment to stdout.
WHY:  **THIS IS THE COMMAND A SCEPTIC RUNS BEFORE GRANTING ANY ACCESS.** It reads a clone they
      already have and writes to stdout. No token, no webhook, no network, and nothing posted.

      **IT IS SPLIT FROM `run_review.py` BECAUSE THEY ARE DIFFERENT CONCERNS**, and because that
      file crossed the 200-line cap when reviews began being recorded. `review()` is a library
      function returning a value; this is an entry point that prints and returns an exit code.
      Rule 6: if you need "and" to describe what a file does, split it.
IMPORTS: rank.firing, serve.{deep_review,run_review}, types.change. Rightmost layer.
CONSUMED BY: `serve/cli.py`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from quantamind.rank import firing
from quantamind.serve.deep_review import report
from quantamind.serve.run_review import review
from quantamind.types.change import REVIEWABLE_SUFFIXES
from quantamind.types.settings import load


def review_commit(clone: Path, repo: str, sha: str, *, deep_project: str = "") -> int:
    """`quantamind review` — rank one commit's files against history strictly before it.

    Prints the comment body, or says plainly that the change is not worth speaking on. **It posts
    nothing**: this is the command a sceptic runs before granting any access, so it reads a clone
    and writes to stdout.
    """
    if not (clone / ".git").exists():
        print(f"{clone} is not a git clone; a review reads history and nothing else")
        return 1
    stamp = _timestamp(clone, sha)
    if stamp is None:
        print(f"{sha[:12]} is not in {clone}, or has no reviewable files")
        return 1
    changed, as_of = stamp
    with TemporaryDirectory() as scratch:
        out = review(clone, repo, changed, Path(scratch) / "review.db", as_of=as_of)
    print(
        f"[review] {len(out.considered)} file(s) ranked, {len(out.skipped)} skipped as unsupported"
    )
    if out.forecast is not None:
        print(f"[review] {out.forecast.sentence()}")
        if out.forecast.selectivity is not firing.Selectivity.SELECTIVE:
            print(f"[review] SELECTIVITY: {out.forecast.selectivity.value.upper()}")
    if out.body is None:
        print("[review] not worth speaking on — no comment would be posted")
        return 0
    print(out.body)
    if deep_project:
        report(clone, sha, out, deep_project, load().gcloud_path)
    return 0


def _timestamp(clone: Path, sha: str) -> tuple[list[str], int] | None:
    """The reviewable files a commit changed, and its time. None when the commit is unknown."""
    done = subprocess.run(
        ["git", "-C", str(clone), "show", "--name-only", "--format=%ct", sha],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if done.returncode != 0:
        return None
    lines = [x for x in done.stdout.splitlines() if x.strip()]
    if not lines:
        return None
    changed = [p for p in lines[1:] if p.endswith(REVIEWABLE_SUFFIXES)]
    return changed, int(lines[0])
