"""PostToolUse hook: format the edited file, then report structural violations.

WHAT: Reads the hook event on stdin, extracts tool_input.file_path, runs ruff on
      that one file, then runs the structural and convention guards over the tree.
      Violations are written to stderr with exit 2 so the model sees them on the
      turn that caused them.
WHY:  This replaces three shell commands in .claude/settings.json that were broken
      in two ways. They interpolated $CLAUDE_FILE_PATHS, which Claude Code does not
      set -- the hook contract passes the path as tool_input.file_path in the stdin
      event -- so `ruff format $CLAUDE_FILE_PATHS` expanded to `ruff format` and
      reformatted the entire tree on every edit. They were also chained with `&&`,
      a POSIX assumption on a project whose author develops on Windows, and
      registered as three separate hooks, which run in parallel rather than in
      order.

      ADVISORY, and the $enforcement_map says so. PostToolUse fires after the write
      has already landed, so this cannot prevent a violation -- it can only make
      the agent aware of one immediately instead of at CI time twenty minutes
      later. The blocking enforcement of these same rules is ci:guards. Claiming
      otherwise in the map would make the map the wish it exists to prevent.
IMPORTS: stdlib json, subprocess, sys, pathlib, plus discovery.project_root
      (stdlib-only, alongside).
CONSUMED BY: .claude/settings.json, PostToolUse matcher "Write|Edit".
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from discovery import project_root

TOOL_TIMEOUT_S = 60
GUARDS = ("check_structure.py", "check_conventions.py")

FEEDBACK = 2
QUIET = 0


def _read_event() -> dict[str, object]:
    try:
        return dict(json.load(sys.stdin))
    except (json.JSONDecodeError, ValueError):
        return {}


def _file_path(event: dict[str, object]) -> str:
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    value = tool_input.get("file_path")
    return str(value) if value else ""


def _run(command: list[str], root: Path) -> tuple[int, str]:
    """Run a command, returning its exit code and combined output."""
    try:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=TOOL_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, f"{command[0]}: {exc}"
    return result.returncode, (result.stdout + result.stderr).strip()


def format_one_file(path: Path, root: Path) -> None:
    """Format and autofix exactly the file that was edited. Never the whole tree."""
    if path.suffix != ".py" or not path.is_file():
        return
    target = str(path)
    _run(["uv", "run", "ruff", "format", target], root)
    _run(["uv", "run", "ruff", "check", "--fix", target], root)


def run_guards(root: Path) -> list[str]:
    """Run the structural guards; return their output if any failed."""
    failures: list[str] = []
    for guard in GUARDS:
        code, output = _run(["uv", "run", "python", f"scripts/guard/{guard}", "."], root)
        if code != 0 and output:
            failures.append(output)
    return failures


def main() -> int:
    root = project_root()
    raw = _file_path(_read_event())
    if raw:
        format_one_file(Path(raw), root)

    failures = run_guards(root)
    if not failures:
        return QUIET

    print("\n".join(failures), file=sys.stderr)
    print(
        "\nStructural guard failed on the file just written. Fix it now rather than at "
        "CI time. Do not raise a threshold to make it pass -- split the file.",
        file=sys.stderr,
    )
    return FEEDBACK


if __name__ == "__main__":
    raise SystemExit(main())
