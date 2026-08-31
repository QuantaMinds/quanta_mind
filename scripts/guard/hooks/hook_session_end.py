"""Stop hook: record what a session changed, and what it did not verify.

WHAT: At the end of a session, writes a short record to docs/plans/ naming the
      branch, the files changed against main, and whether the CODEBASE map was
      updated alongside them. The records are gitignored -- they are a transcript,
      not repository content.
WHY:  The definition of done in AGENTS.md has seven items, and the ones that get
      skipped are the ones nobody can see were skipped -- the map not updated, the
      verify never run. This puts the omission on disk where the next session
      reads it, rather than leaving it to be inferred.

      **THE RECORDS ARE GITIGNORED AND THIS PARAGRAPH USED TO SAY OTHERWISE.** It
      claimed the omission became "a file in the repository". Twelve were committed
      once, and `a38c2d1` gitignored the pattern precisely so a stray `git add -A`
      could not do it again. They are a local transcript. 27 accumulated unread.

      It never blocks. A Stop hook that fails is a session that ends in an error
      the developer did not ask for, and the record is worth less than the
      interruption costs.
IMPORTS: stdlib subprocess, sys, datetime, pathlib; discovery.project_root and
      records.check_docs_sync.MAP_PATH alongside (both stdlib-only).
CONSUMED BY: .claude/settings.json, Stop.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

# `discovery` lives one level up: hooks are invoked by Claude Code with this file's
# own directory on sys.path, not the guard root. Explicit beats a package layout
# that only works when something else happens to have set PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from discovery import project_root

# **IMPORTED, NOT REDECLARED, AND THAT IS THE WHOLE OF THIS MODULE'S HISTORY.** This file held its
# own `MAP_PATH = "docs/CODEBASE.md"`. On 2026-08-13 the map moved to `docs/engineering/` by
# `git mv`; that commit updated the copy in `check_docs_sync.py` and missed this one. For
# eighteen days `touched_map` compared every changed path against a file that does not exist, so
# **27 of 27 session records reported `updated: no`** and every session touching `src/` printed
# the warning. A perfect zero from a comparison that could not return anything else -- the same
# class as `candidate in ours_caught`, logged as the clean-zero rule in `AGENTS.md` rule 14.
# One name for one path is what stops the next rename doing it again.
from records.check_docs_sync import MAP_PATH

PLANS_DIR = Path("docs") / "plans"
BASE_REF = "main"
GIT_TIMEOUT_S = 30


def _git(args: list[str], root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _slug(branch: str) -> str:
    return branch.replace("/", "-") or "detached"


def build_record(root: Path) -> tuple[str, str] | None:
    """Return (filename, contents), or None when there is nothing worth recording."""
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    if not branch or branch == BASE_REF:
        return None

    changed = [
        f for f in _git(["diff", "--name-only", f"{BASE_REF}...HEAD"], root).splitlines() if f
    ]
    uncommitted = [f for f in _git(["status", "--porcelain"], root).splitlines() if f]
    if not changed and not uncommitted:
        return None

    map_path = MAP_PATH.as_posix()
    touched_src = any(f.startswith("src/") for f in changed)
    touched_map = map_path in changed
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        f"# Session record — {branch}",
        "",
        f"Written by scripts/guard/hooks/hook_session_end.py at {stamp}.",
        "Informational. Nothing here was blocked or enforced.",
        "",
        f"- Branch: `{branch}`",
        f"- Files changed vs `{BASE_REF}`: {len(changed)}",
        f"- Uncommitted at session end: {len(uncommitted)}",
        f"- `{map_path}` updated: {'yes' if touched_map else 'no'}",
        "",
    ]
    # **THE RECORD SAYS SO WHEN ITS OWN SUBJECT IS MISSING.** `updated: no` is the answer both
    # when the map was not touched and when the path is wrong, and those two must not print the
    # same line -- which they did, 27 times, for eighteen days.
    if not (root / MAP_PATH).is_file():
        lines += [
            f"> **`{map_path}` does not exist, so the line above is not a measurement.**",
            "> Whatever renamed it did not update `check_docs_sync.MAP_PATH`.",
            "",
        ]
    elif touched_src and not touched_map:
        lines += [
            f"> This session changed `src/` without touching `{map_path}`.",
            "> `just check` will fail on docs-sync until it does.",
            "",
        ]
    if changed:
        lines += ["## Changed", "", *(f"- `{f}`" for f in sorted(changed)), ""]

    return f"session-{_slug(branch)}.md", "\n".join(lines)


def main() -> int:
    root = project_root()
    record = build_record(root)
    if record is None:
        return 0

    name, contents = record
    target = root / PLANS_DIR
    try:
        target.mkdir(parents=True, exist_ok=True)
        (target / name).write_text(contents, encoding="utf-8")
    except OSError as exc:
        print(f"[session-end] could not write record: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
