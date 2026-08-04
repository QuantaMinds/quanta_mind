"""PreToolUse hook: blocks writes that must never happen silently.

WHAT: Reads the hook event on stdin and decides on three cases.
      - vendor/                  -> deny. Pinned third-party source is never edited.
      - on branch main           -> deny. CONTRIBUTING.md: one change, one branch.
      - tests/fixtures/golden/   -> ask, unless a one-shot sentinel is present.
WHY:  PreToolUse is the only hook that can actually prevent something -- it runs
      before the tool call, and exit 2 cancels it. PostToolUse fires after the write
      has landed and can only comment.

      The golden case is deliberately "ask" rather than "deny". VALIDATION.md
      section 2.4 turns on golden files being reviewed rather than regenerated, but
      blocking the update outright would just push people to disable the hook.
      Asking puts a human in the loop, which is the actual requirement.

      A sentinel FILE rather than an environment variable: `export
      QMCTX_UPDATE_GOLDEN=1` survives in a shell profile and quietly disables the
      check forever. A file the hook deletes after one use cannot.
IMPORTS: stdlib json, subprocess, sys, pathlib, plus discovery.project_root.
      discovery.py is stdlib-only and sits alongside, so hooks still run before the
      package is installable.
CONSUMED BY: .claude/settings.json, PreToolUse matcher "Write|Edit".
CONTRACT: event JSON on stdin with tool_input.file_path. Exit 2 denies and feeds
      stderr back to the model. Exit 0 with hookSpecificOutput on stdout can ask.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from discovery import project_root

SENTINEL = ".qmctx-allow-golden"
GOLDEN_DIR = "tests/fixtures/golden"
VENDOR_DIR = "vendor/"
PROTECTED_BRANCH = "main"
GIT_TIMEOUT_S = 30

DENY = 2
ALLOW = 0


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


def _relative(path_text: str, root: Path) -> str:
    """Repo-relative posix path, or the raw text if it is outside the repo."""
    if not path_text:
        return ""
    try:
        return Path(path_text).resolve().relative_to(root).as_posix()
    except ValueError:
        return Path(path_text).as_posix()


def _current_branch(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _ask(reason: str) -> int:
    """Escalate to the human instead of deciding."""
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return ALLOW


def decide(rel: str, root: Path) -> int:
    """Apply the three rules to one repo-relative path."""
    if not rel:
        return ALLOW

    if rel.startswith(VENDOR_DIR):
        print(
            f"{rel} is vendored third-party source and is never edited. Versions are "
            f"pinned because a grammar or analyzer change silently alters output. "
            f"Patch upstream, or record a fork in docs/PROJECT_CONTEXT.md.",
            file=sys.stderr,
        )
        return DENY

    if _current_branch(root) == PROTECTED_BRANCH:
        print(
            f"refusing to write {rel} on '{PROTECTED_BRANCH}'. One change, one branch: "
            f"`git switch -c feat/<area>-<description>` first. See CONTRIBUTING.md.",
            file=sys.stderr,
        )
        return DENY

    if rel.startswith(GOLDEN_DIR):
        sentinel = root / SENTINEL
        if sentinel.is_file():
            sentinel.unlink()  # one-shot: consumed here so it cannot be left set
            return ALLOW
        return _ask(
            f"{rel} is a reviewed golden file. VALIDATION.md requires a human to state "
            f"why the output changed and why the new output is more correct -- "
            f"'regenerated' is not an explanation. Approve only if you are that human."
        )

    return ALLOW


def main() -> int:
    root = project_root()
    return decide(_relative(_file_path(_read_event()), root), root)


if __name__ == "__main__":
    raise SystemExit(main())
