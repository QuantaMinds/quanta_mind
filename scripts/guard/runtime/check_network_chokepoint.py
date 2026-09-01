"""Every outbound call in the product asks permission first.

WHAT: finds every module in `src/` that opens a socket or runs a networked git subcommand, and
      fails unless it calls `types.deployment.permit` before doing so.
WHY:  **D7f. AIR-GAPPED MUST REFUSE, NOT MERELY ABSTAIN**, and a refusal spread across seven call
      sites is seven chances to forget one. A new module added next month that calls `urlopen`
      without asking would reintroduce the exact failure the row names — an outbound attempt that
      a bank sees in its egress logs and we do not see at all.

      **THIS GUARD EXISTS BECAUSE RULE 7 DID NOT.** `AGENTS.md` claimed the layer order stopped
      `verify` importing `infer` and nothing enforced it, for months, with a `→ guard` pointer
      beside it that stopped anyone checking. A deployment promise with no mechanism is the same
      shape, and it is worth more to a customer than a layering rule.

      **IT MATCHES ON PRIMITIVES, NOT ON NAMES.** Looking for a module called something like
      `http.py` would miss `verify/releases.py`; looking for `urlopen` and for git's own networked
      subcommands finds what actually reaches out, whatever the file is called.
IMPORTS: scripts/guard/discovery.py; stdlib ast, re.
CONSUMED BY: justfile (`just check`), .github/workflows/guards.yml.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# Running a guard as a script puts only ITS directory on sys.path[0]. This one lives one level
# down, so the shared modules beside its parent are added explicitly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coverage import assert_examined, guarded
from discovery import Violation, iter_python_files, report

OPENS_A_SOCKET = ("urlopen", "socket", "HTTPSConnection", "HTTPConnection")
"""Calls that reach the network. `Request` alone builds an object and sends nothing."""

NETWORKED_GIT = ("clone", "fetch", "ls-remote", "push", "pull")
"""git subcommands that talk to a remote. `log`, `show`, `rev-parse` and friends do not."""

RUNS_A_PROCESS = "subprocess"
"""**A GIT WORD ONLY COUNTS IF THE MODULE IMPORTS `subprocess`.** `serve/cli.py` names an argument
`"clone"` and calls a local function `run(...)`, and two successive versions of this guard flagged
it — first on the word, then on the name `run`. A guard that fires on deliberate code teaches a
reader to scroll past the section, which `.quantamind/rules.toml`'s own header calls worse than no
rule at all. Importing `subprocess` is what actually distinguishes a module that can shell out."""

ASKS_PERMISSION = "permit"
"""`types.deployment.permit`. Imported under its own name at every call site, never aliased."""


def _calls(tree: ast.AST) -> set[str]:
    """Every attribute or name invoked anywhere in the module."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if isinstance(target, ast.Attribute):
            found.add(target.attr)
        elif isinstance(target, ast.Name):
            found.add(target.id)
    return found


def _imports_subprocess(tree: ast.AST) -> bool:
    """Whether this module can shell out at all."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(a.name == RUNS_A_PROCESS for a in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module == RUNS_A_PROCESS:
            return True
    return False


def _git_remote_words(tree: ast.AST) -> set[str]:
    """Networked git subcommands appearing as string literals in this module."""
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value in NETWORKED_GIT
    }


def check_chokepoint(root: Path) -> list[Violation]:
    """Every module that reaches out must call `permit` somewhere in the same module."""
    violations: list[Violation] = []
    for path in iter_python_files(root):
        if "src/quantamind" not in path.as_posix():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue  # ruff's job, not ours
        called = _calls(tree)
        sockets = sorted(set(OPENS_A_SOCKET) & called)
        git_words = sorted(_git_remote_words(tree)) if _imports_subprocess(tree) else []
        if not sockets and not git_words:
            continue
        if ASKS_PERMISSION in called:
            continue
        wanted = ", ".join(sockets + [f"git {w}" for w in git_words])
        violations.append(
            Violation(
                path,
                1,
                "network-without-permission",
                f"reaches the network ({wanted}) without calling "
                f"`types.deployment.permit(...)` first. An air-gapped deployment must REFUSE, "
                f"not merely fail to connect — see D7f.",
            )
        )
    return violations


def main(root: Path) -> int:
    violations = check_chokepoint(root)
    # **A GUARD THAT EXAMINED NOTHING MUST NOT REPORT "ok".** A clean zero and a broken walk print
    # the same line otherwise, which this project has recorded three times.
    assert_examined("python modules", sum(1 for _ in iter_python_files(root)), 40, root)
    return report(violations, root, "network-chokepoint")


if __name__ == "__main__":
    sys.exit(guarded(lambda: main(Path(sys.argv[1] if len(sys.argv) > 1 else "."))))
