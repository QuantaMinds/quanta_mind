"""Convention guards: layering, module docstrings, and banned name tokens.

WHAT: Three checks that protect separation of concerns and readability.
      1. Layering  — a module may import only from layers to its left in the declared
                     order (types < discover < ingest < resolve < probe < label < store
                     < serve). Sideways imports into a sibling's internals are banned.
                     The order lives in discovery.LAYER_ORDER and is authoritative;
                     `parse` was removed when we decided to consume an upstream graph
                     rather than build one (docs/plans/implementation.md).
      2. Docstring — every module opens with a docstring containing WHAT, WHY and
                     IMPORTS, so a new contributor can read any single file cold.
      3. Naming    — bans placeholder tokens (util, helper, manager, ...) that mark a
                     missing abstraction.
WHY:  Layering is what lets us change one resolver without breaking another; it is the
      mechanical form of "any change should be independently testable". Docstrings are
      the onboarding contract. Banned tokens are how vague modules start.
IMPORTS: scripts/guard/discovery.py; stdlib ast.
CONSUMED BY: justfile (`just check`), .github/workflows/guards.yml.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from coverage import assert_examined
from discovery import LAYER_ORDER, Violation, iter_python_files, layer_of, report

PACKAGE = "quantamind"

# The union of what this guard banned and what AGENTS.md's style section listed --
# the two had drifted apart, each holding tokens the other did not.
BANNED_TOKENS: frozenset[str] = frozenset(
    {
        "util",
        "utils",
        "helper",
        "helpers",
        "manager",
        "common",
        "misc",
        "shared",
        "stuff",
        "base",
        "core",
        "data",
    }
)

REQUIRED_DOCSTRING_SECTIONS: tuple[str, ...] = ("WHAT:", "WHY:", "IMPORTS:")


def _layer_index(layer: str) -> int:
    return LAYER_ORDER.index(layer)


def check_layering(root: Path, package_root: Path) -> list[Violation]:
    """A layer may import only from layers strictly to its left."""
    violations: list[Violation] = []
    for path in iter_python_files(root):
        own_layer = layer_of(path, package_root)
        if own_layer is None:
            continue
        own_index = _layer_index(own_layer)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue  # syntax errors are ruff's job, not ours
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            parts = node.module.split(".")
            if len(parts) < 2 or parts[0] != PACKAGE:
                continue
            target_layer = parts[1]
            if target_layer not in LAYER_ORDER or target_layer == own_layer:
                continue
            if _layer_index(target_layer) >= own_index:
                violations.append(
                    Violation(
                        path,
                        node.lineno,
                        "layer-violation",
                        f"'{own_layer}' imports from '{target_layer}', which is at or to "
                        f"its right. Dependencies flow left only. Move the shared type "
                        f"into quantamind.types, or invert the dependency.",
                    )
                )
    return violations


def check_module_docstrings(root: Path) -> list[Violation]:
    """Every module must open with a docstring covering WHAT, WHY and IMPORTS."""
    violations: list[Violation] = []
    for path in iter_python_files(root):
        if path.name == "__init__.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        doc = ast.get_docstring(tree)
        if not doc:
            violations.append(
                Violation(
                    path,
                    1,
                    "missing-docstring",
                    "no module docstring. State WHAT it does, WHY it exists, what it "
                    "IMPORTS and from which layer, and who consumes it.",
                )
            )
            continue
        missing = [s for s in REQUIRED_DOCSTRING_SECTIONS if s not in doc]
        if missing:
            violations.append(
                Violation(
                    path,
                    1,
                    "incomplete-docstring",
                    f"module docstring missing section(s): {', '.join(missing)}",
                )
            )
    return violations


def check_naming(root: Path) -> list[Violation]:
    """File and directory names must not contain placeholder tokens."""
    violations: list[Violation] = []
    for path in iter_python_files(root):
        stem_tokens = set(path.stem.lower().split("_"))
        offending = stem_tokens & BANNED_TOKENS
        if offending:
            token = sorted(offending)[0]
            violations.append(
                Violation(
                    path,
                    1,
                    "banned-name",
                    f"filename contains '{token}'. That word marks a missing abstraction. "
                    f"Name the file after the single concern it owns.",
                )
            )
    return violations


def main(argv: list[str]) -> int:
    """Run all three convention checks."""
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    package_root = root / "src" / PACKAGE
    if not package_root.is_dir():
        print(f"[conventions] no package at {package_root}", file=sys.stderr)
        return 2

    violations = (
        check_layering(root, package_root) + check_module_docstrings(root) + check_naming(root)
    )
    assert_examined("python files", sum(1 for _ in iter_python_files(root)), 40, root)
    return report(violations, root, "conventions")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
