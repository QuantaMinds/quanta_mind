"""Keeps research dependencies out of the product.

WHAT: Fails if anything under src/ or scripts/ imports a package that belongs to
      research/ only -- pandas, scipy, statsmodels, git, yaml, pycg, tree_sitter.
WHY:  research/phase0/ is a standalone uv project with its own lockfile and its own
      interpreter, which is the structural reason those packages cannot reach the
      product today. This guard is the backstop for the day someone converts the
      projects into a uv workspace to simplify CI. uv's documentation is explicit
      that workspace members share one environment and that it "can't ensure that
      packages don't import dependencies declared by another workspace member" --
      so at that moment the structural guarantee silently disappears and only this
      check remains.

      It also enforces a design rule in its own right: scripts/guard/ is stdlib-only
      because guards must run before the package is installable. Any third-party
      import there breaks that, whatever the package is.
IMPORTS: scripts/guard/discovery.py; stdlib ast. No project imports.
CONSUMED BY: justfile (`just check`), .github/workflows/guards.yml.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from discovery import Violation, iter_python_files, report

# Top-level module names owned by research/. `git` is GitPython.
RESEARCH_ONLY: frozenset[str] = frozenset(
    {
        "pandas",
        "numpy",
        "scipy",
        "statsmodels",
        "git",
        "yaml",
        "pycg",
        "tree_sitter",
        "tree_sitter_python",
        "tree_sitter_typescript",
    }
)

# Directories the product occupies. research/ is exempt by definition.
PRODUCT_DIRS: tuple[str, ...] = ("src", "scripts")


def _top_level(module: str) -> str:
    return module.split(".")[0]


def _imported_modules(tree: ast.Module) -> list[tuple[str, int]]:
    """Every top-level module name imported, with its line number."""
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((_top_level(alias.name), node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.append((_top_level(node.module), node.lineno))
    return found


def check_product_is_clean(root: Path) -> list[Violation]:
    """No product file may import a research-only package."""
    violations: list[Violation] = []
    for directory in PRODUCT_DIRS:
        base = root / directory
        if not base.is_dir():
            continue
        for path in iter_python_files(base):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError:
                continue  # ruff's job, not ours
            for module, lineno in _imported_modules(tree):
                if module in RESEARCH_ONLY:
                    violations.append(
                        Violation(
                            path,
                            lineno,
                            "research-import-in-product",
                            f"imports '{module}', which belongs to research/ only. The "
                            f"product ships inside the customer's network and carries no "
                            f"analysis stack. If this is genuinely needed, it needs a "
                            f"dependency entry and an argument, not an import.",
                        )
                    )
    return violations


def main(argv: list[str]) -> int:
    """Scan the product directories beneath the repository root."""
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    if not root.is_dir():
        print(f"[research-imports] root {root} is not a directory", file=sys.stderr)
        return 2

    return report(check_product_is_clean(root), root, "research-imports")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
