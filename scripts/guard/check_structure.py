"""Structural guards: file length cap and directory fanout cap.

WHAT: Fails CI when any source file exceeds 200 lines, or any directory holds more
      than 15 files (excluding __init__.py).
WHY:  Both caps are proxies for separation of concerns. A 400-line module is doing two
      jobs; a 40-file directory is a layer that was never decomposed. Enforcing the
      proxy mechanically is cheaper than arguing about the principle in review, and it
      keeps every file small enough for a new contributor — or an agent — to hold whole.
      Docs and vendored code are exempt: prose has different economics than code.
IMPORTS: scripts/guard/discovery.py (shared walker). stdlib only otherwise.
CONSUMED BY: justfile (`just check`), .github/workflows/guards.yml, and the
      PreToolUse Claude Code hook in .claude/settings.json.
"""

from __future__ import annotations

import sys
from pathlib import Path

from coverage import assert_examined, guarded
from discovery import Violation, iter_package_dirs, iter_source_files, report
from exclusions import is_excluded

MAX_FILE_LINES = 200
MAX_DIR_FILES = 15

# Hook-written session records. They are gitignored and regenerate every session, so they
# accumulate on disk without ever entering the repository -- and the fan-out cap was
# counting them, failing a directory that holds three tracked files. A cap that fires on
# files nobody committed measures the machine, not the codebase.
SESSION_RECORD_PREFIX = "session-"

# __init__.py is re-export plumbing, not a concern in its own right, so it does not
# count against the fanout budget. It is still subject to the line cap.
FANOUT_EXEMPT_NAMES: frozenset[str] = frozenset({"__init__.py"})


def check_file_lengths(root: Path) -> list[Violation]:
    """Every source file must be at most MAX_FILE_LINES lines."""
    violations: list[Violation] = []
    for path in iter_source_files(root):
        try:
            line_count = sum(1 for _ in path.open("r", encoding="utf-8", errors="strict"))
        except UnicodeDecodeError:
            violations.append(
                Violation(path, 1, "file-encoding", "not valid UTF-8; source must be UTF-8")
            )
            continue
        if line_count > MAX_FILE_LINES:
            over = line_count - MAX_FILE_LINES
            violations.append(
                Violation(
                    path,
                    MAX_FILE_LINES + 1,
                    "file-length",
                    f"{line_count} lines, {over} over the {MAX_FILE_LINES} cap. "
                    f"Split by concern, do not raise the cap.",
                )
            )
    return violations


def check_dir_fanout(root: Path) -> list[Violation]:
    """Every directory must hold at most MAX_DIR_FILES files."""
    violations: list[Violation] = []
    for directory in iter_package_dirs(root):
        entries = [
            child
            for child in directory.iterdir()
            if child.is_file()
            and not is_excluded(child)
            and child.name not in FANOUT_EXEMPT_NAMES
            and not child.name.startswith(".")
            and not child.name.startswith(SESSION_RECORD_PREFIX)
        ]
        if len(entries) > MAX_DIR_FILES:
            names = ", ".join(sorted(entry.name for entry in entries)[:5])
            violations.append(
                Violation(
                    directory,
                    1,
                    "dir-fanout",
                    f"{len(entries)} files, cap is {MAX_DIR_FILES}. "
                    f"Introduce a sub-package. First five: {names}, ...",
                )
            )
    return violations


def main(argv: list[str]) -> int:
    """Run both structural checks against the repository root."""
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    if not root.is_dir():
        print(f"[structure] root {root} is not a directory", file=sys.stderr)
        return 2

    violations = check_file_lengths(root) + check_dir_fanout(root)
    assert_examined("source files", sum(1 for _ in iter_source_files(root)), 40, root)
    return report(violations, root, "structure")


if __name__ == "__main__":
    raise SystemExit(guarded(lambda: main(sys.argv)))
