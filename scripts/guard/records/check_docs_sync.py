"""Keeps docs/engineering/CODEBASE.md honest about what is in src/.

WHAT: Two checks.
      1. Every directory under src/quantamind/ is mentioned in docs/engineering/CODEBASE.md.
      2. In CI, a diff that touches src/ must also touch docs/engineering/CODEBASE.md.
WHY:  CODEBASE.md is the onboarding map -- a new contributor, or a new agent
      session, should read one file and know which directory to open. A map that
      silently omits a directory is worse than no map, because it is trusted.

      This VERIFIES rather than regenerates. The justfile used to call a
      `regenerate_codebase_map.py` that does not exist, and CODEBASE.md's own
      header claims it is both regenerated and hand-reviewed -- which cannot both
      be true of a file whose value is its hand-written prose. Generating it would
      flatten exactly the part worth reading, so the generator is gone and this
      guard takes its place.
IMPORTS: scripts/guard/discovery.py; stdlib subprocess. No project imports.
CONSUMED BY: justfile (`just check`), .github/workflows/guards.yml.
NOTE: check 2 needs full history. The workflow sets fetch-depth: 0 -- without it
      `origin/main...HEAD` resolves to nothing and the check silently passes.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
from pathlib import Path

# Running a guard as a script puts only ITS directory on sys.path[0]. This one lives one level
# down, so the parent is added explicitly -- the same reason `citations/` does it.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from discovery import Violation, is_excluded, report

MAP_PATH = Path("docs") / "engineering" / "CODEBASE.md"
PACKAGE = Path("src") / "quantamind"
BASE_REF = "origin/main"
GIT_TIMEOUT_S = 30


def check_every_directory_is_documented(root: Path) -> list[Violation]:
    """Each package directory must appear somewhere in the map."""
    package_root = root / PACKAGE
    doc = root / MAP_PATH
    if not package_root.is_dir() or not doc.is_file():
        return []

    text = doc.read_text(encoding="utf-8")
    violations: list[Violation] = []
    for path in sorted(package_root.rglob("*")):
        if not path.is_dir() or is_excluded(path):
            continue
        name = path.relative_to(package_root).as_posix()
        if f"{name}/" not in text and f"`{name}`" not in text:
            violations.append(
                Violation(
                    doc,
                    1,
                    "undocumented-directory",
                    f"src/quantamind/{name}/ exists but is not in {MAP_PATH.as_posix()}. Add a "
                    f"row saying what it owns and what it must not do.",
                )
            )
    return violations


def _changed_files(root: Path) -> list[str] | None:
    """Files changed against the merge base, or None if history is unavailable."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{BASE_REF}...HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def check_docs_move_with_code(root: Path) -> list[Violation]:
    """A change to src/ must be reflected in the map."""
    changed = _changed_files(root)
    if changed is None:
        print(f"[docs-sync] {BASE_REF} unavailable; skipping the diff check", file=sys.stderr)
        return []
    if not changed:
        return []

    touched_src = any(f.startswith("src/") for f in changed)
    touched_map = MAP_PATH.as_posix() in changed
    if touched_src and not touched_map:
        return [
            Violation(
                root / MAP_PATH,
                1,
                "docs-not-updated",
                f"this branch changes src/ but not {MAP_PATH.as_posix()}. If the change "
                f"genuinely alters nothing a reader of the map would care about, say so "
                f"in the PR -- do not skip it silently.",
            )
        ]
    return []


def main(argv: list[str]) -> int:
    """Run both checks against the repository root."""
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    if not root.is_dir():
        print(f"[docs-sync] root {root} is not a directory", file=sys.stderr)
        return 2

    violations = check_every_directory_is_documented(root) + check_docs_move_with_code(root)
    return report(violations, root, "docs-sync")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
