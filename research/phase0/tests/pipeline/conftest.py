"""A real git repository with a real two-commit history, for the diff-reading tests.

WHAT: Builds a throwaway repo whose child commit edits one line inside one method and
      adds a new file, then hands back the two SHAs.
WHY:  These tests assert on `git diff` output and tree-sitter parses. Faking either
      would test the fake. AGENTS.md rule 1 is explicit that a green test on mocked data
      is not a verified test, and the whole point of this fixture is that the diff is
      produced by git.
IMPORTS: stdlib subprocess, pytest.
CONSUMED BY: tests/pipeline/test_changed.py, tests/pipeline/test_assemble.py.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

SOURCE = """
import os


def untouched(a, b):
    return a + b


class Handler:
    def validate(self, request):
        checked = request.strip()
        return checked


def also_untouched():
    return 1
"""


@pytest.fixture
def parent_source() -> str:
    """The file's contents at the parent commit, for symbol-attribution assertions."""
    return SOURCE


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, str, str]:
    """(repository, parent sha, child sha)."""
    root = tmp_path / "repo"
    (root / "pkg").mkdir(parents=True)

    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, timeout=60)

    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True, timeout=60)
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "T")
    (root / "pkg" / "mod.py").write_text(SOURCE, encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "parent")

    changed = SOURCE.replace("checked = request.strip()", "checked = request.strip().lower()")
    (root / "pkg" / "mod.py").write_text(changed, encoding="utf-8")
    (root / "pkg" / "added.py").write_text("def brand_new():\n    return 2\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "child")

    out = subprocess.run(
        ["git", "-C", str(root), "log", "--format=%H", "--reverse"],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    parent, child = out.stdout.split()
    return root, parent, child
