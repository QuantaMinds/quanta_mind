"""Stop hook: record what a session changed, and what it did not verify.

WHAT: At the end of a session, writes a short record to docs/plans/ naming the
      branch, the files changed against main, and whether docs/CODEBASE.md was
      updated alongside them.
WHY:  The definition of done in AGENTS.md has seven items, and the ones that get
      skipped are the ones nobody can see were skipped -- the map not updated, the
      verify never run. This makes the omission a file in the repository rather
      than something the next session has to infer.

      It never blocks. A Stop hook that fails is a session that ends in an error
      the developer did not ask for, and the record is worth less than the
      interruption costs.
IMPORTS: stdlib subprocess, sys, datetime, pathlib, plus discovery.project_root
      (stdlib-only, alongside).
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

PLANS_DIR = Path("docs") / "plans"
MAP_PATH = "docs/CODEBASE.md"
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

    touched_src = any(f.startswith("src/") for f in changed)
    touched_map = MAP_PATH in changed
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        f"# Session record — {branch}",
        "",
        f"Written by scripts/guard/hook_session_end.py at {stamp}.",
        "Informational. Nothing here was blocked or enforced.",
        "",
        f"- Branch: `{branch}`",
        f"- Files changed vs `{BASE_REF}`: {len(changed)}",
        f"- Uncommitted at session end: {len(uncommitted)}",
        f"- `{MAP_PATH}` updated: {'yes' if touched_map else 'no'}",
        "",
    ]
    if touched_src and not touched_map:
        lines += [
            f"> This session changed `src/` without touching `{MAP_PATH}`.",
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
