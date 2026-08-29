"""Reject any `subprocess` call that does not declare a timeout.

WHAT: Walks every `subprocess.run`, `.Popen`, `.call`, `.check_call` and `.check_output` in the
      source trees and requires an explicit `timeout=` keyword. Reports the file and line of each
      one that lacks it.
WHY:  AGENTS.md has said "Timeouts on every subprocess and every I/O call. Default 30s, declared
      explicitly" since it was written, and NOTHING CHECKED IT. All thirteen call sites complied
      when this guard was added, which is exactly the moment to add it: a rule that is obeyed by
      habit is one refactor away from being obeyed nowhere, and the enforcement map's own comment
      says a rule with no mechanism is advisory.

      A MISSING TIMEOUT IS THE LOUDEST SILENT FAILURE THERE IS. Every other failure in this
      pipeline produces a message: an exit code, a raised `HistoryReadFailed`, a typed
      `Unresolved`. A subprocess with no timeout produces NOTHING -- no output, no error, no
      completion. `git log` on a corrupt object store, a `gh api` call against a hung endpoint,
      and the run stops forever with the last thing printed being whatever came before it. There
      is no failure mode a reader is worse equipped to diagnose.

      A LITERAL IS NOT REQUIRED, only an explicit keyword. `timeout=HISTORY_TIMEOUT_S` is better
      than `timeout=1800` because the constant carries a name and a docstring, and demanding a
      literal would push call sites toward magic numbers to satisfy a guard.
IMPORTS: scripts/guard/discovery.py; stdlib ast. No project imports.
CONSUMED BY: `just guards`; CI.
"""

from __future__ import annotations

import ast
import sys

from coverage import assert_examined, guarded
from discovery import Violation, iter_python_files, project_root, report

# **A FLOOR, NOT A TARGET.** Set well below today's 35 so it fires when discovery
# collapses -- a moved directory, a narrowed glob -- rather than when the count drifts.
SUBPROCESS_FLOOR = 10

SCANNED_ROOTS = ("src", "research/phase0/src", "scripts")
# Every subprocess entry point that starts a child process and can therefore wait forever.
# `subprocess.PIPE` and friends are attributes, not calls, and never match.
BLOCKING_CALLS = frozenset(
    {"run", "call", "check_call", "check_output", "Popen", "getoutput", "getstatusoutput"}
)


def _is_subprocess_call(node: ast.Call) -> str | None:
    """The subprocess function this call names, or None when it is not one.

    Matches both `subprocess.run(...)` and a bare `run(...)` imported via
    `from subprocess import run`, because the second form is just as capable of hanging.
    """
    func = node.func
    if (
        isinstance(func, ast.Attribute)
        and func.attr in BLOCKING_CALLS
        and isinstance(func.value, ast.Name)
        and func.value.id == "subprocess"
    ):
        return f"subprocess.{func.attr}"
    return None


def _imported_bare(tree: ast.Module) -> set[str]:
    """Names pulled in by `from subprocess import run, Popen`, which lose the module prefix."""
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            out.update(alias.asname or alias.name for alias in node.names)
    return out & BLOCKING_CALLS


def main() -> int:
    root = project_root()
    violations: list[Violation] = []
    checked = 0

    for scanned in SCANNED_ROOTS:
        base = root / scanned
        if not base.is_dir():
            continue
        for path in iter_python_files(base):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError):
                continue
            bare = _imported_bare(tree)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                named = _is_subprocess_call(node)
                if named is None and isinstance(node.func, ast.Name) and node.func.id in bare:
                    named = node.func.id
                if named is None:
                    continue
                checked += 1
                if not any(keyword.arg == "timeout" for keyword in node.keywords):
                    violations.append(
                        Violation(
                            path,
                            node.lineno,
                            "subprocess-timeout",
                            f"`{named}` has no explicit timeout — it can hang forever, printing "
                            f"nothing and raising nothing",
                        )
                    )

    # Printed on every run. The count is the evidence the guard is looking at anything at all:
    # a scan that silently matched zero call sites reports exactly what a clean run reports.
    assert_examined("subprocess call sites", checked, SUBPROCESS_FLOOR, root)
    print(f"[subprocess-timeouts] {checked} subprocess call site(s) checked", flush=True)
    return report(violations, root, "subprocess-timeouts")


if __name__ == "__main__":
    sys.exit(guarded(lambda: main()))
