"""Every `python -m` command the docs prescribe must actually be runnable.

WHAT: Finds `python -m <module>` invocations in the documentation and fails when the
      named module has no command-line entry point.
WHY:  `PHASE0_RUNBOOK.md` "Days 3-5 - The run" documents the three commands that ARE the
      study. None of the three modules had a `main`, a `__main__` guard, or any argparse:

          uv run python -m phase0.extract_prs  ... --out data/prs.jsonl
          uv run python -m phase0.run_pipeline ... --out data/exposure.jsonl
          uv run python -m phase0.scan_outcome ... --out data/outcome.jsonl

      `python -m pkg.mod` on a module with no `__main__` block executes the top-level
      body -- imports and class definitions -- and exits 0. The `--out` flags are
      ignored, no file is written, nothing is printed, and the shell reports success.
      Running the study exactly as documented produces nothing and looks like it worked.

      That is the eighth instance of one pattern here: an absence that is not typed, so
      it reads as a result. The others corrupted a number. This one would let a
      thirty-hour run appear to have completed. The functions themselves are real and
      tested -- `run_pipeline.run()` has coverage -- they were simply never wired to a
      command line, and no test could notice because no test invokes the docs.

      Deliberately syntactic, like `check_module_identity`. Guards run before the package
      is installable, so the module cannot be imported to ask whether it would do
      anything; the presence of an `if __name__ == "__main__"` block is the property that
      makes `python -m` more than a no-op, and it is visible in the AST.
IMPORTS: scripts.guard.discovery, stdlib ast + re.
CONSUMED BY: `just guards`; CI.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys
from pathlib import Path

# Running a guard as a script puts only ITS directory on sys.path[0]. This one lives one level
# down, so the parent is added explicitly -- the same reason `citations/` does it.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from coverage import assert_examined, refuse_path_argument
from discovery import Violation, project_root, report

# `python -m package.module`, however it is invoked -- bare, via uv, or inside a longer
# pipeline. The module name is what matters; the flags after it are not our business.
INVOCATION = re.compile(r"python\s+-m\s+(?P<module>[a-zA-Z_][\w.]*)")

# Where a documented command may live. Plans record intent rather than procedure, so a
# command in a plan is a proposal and not yet a promise.
DOC_ROOTS = (
    "docs/findings",
    "docs/engineering/CODEBASE.md",
    "README.md",
    "BRIEFING.md",
    "AGENTS.md",
)

# Import roots a documented module name may resolve under.
PACKAGE_ROOTS = ("src", "research/phase0/src")

# Third-party modules documented for direct invocation. Their entry points are upstream's
# and are not ours to assert on. Listed rather than pattern-matched, so adding one is a
# decision somebody makes on purpose.
THIRD_PARTY = frozenset({"pycg", "pytest", "pip", "venv", "build", "uv"})

# Suppression for a command that is documented but deliberately not built yet. Counted and
# printed on every run, exactly like `no-vague-refs:allow` -- the point is that "we have
# not wired this up" stays visible in CI output instead of being silently absent. It is
# not a general escape hatch: an unbuilt command still blocks anyone relying on it.
UNBUILT = "documented-command:unbuilt"
FLOOR = 2  # below today's 4: catches discovery collapsing, not drift


def _module_path(root: Path, dotted: str) -> Path | None:
    """The file a dotted module name refers to, or None when nothing claims that name."""
    relative = Path(*dotted.split("."))
    for package_root in PACKAGE_ROOTS:
        for candidate in (
            root / package_root / relative.with_suffix(".py"),
            root / package_root / relative / "__main__.py",
        ):
            if candidate.is_file():
                return candidate
    return None


def _has_entry_point(path: Path) -> bool:
    """Whether running this file as `__main__` would do anything at all.

    An `if __name__ == "__main__":` block is the whole test. A module with a `main()`
    nobody calls still exits 0 in silence, which is the defect this guard exists for.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
            and any(isinstance(c, ast.Constant) and c.value == "__main__" for c in test.comparators)
        ):
            return True
    return False


def _logical_lines(text: str) -> list[tuple[int, str]]:
    """Shell commands joined across `\\` continuations, tagged with their first line.

    A documented command spans several physical lines, so the `python -m` and the
    suppression marker naturally sit on different ones. Scanning physical lines would
    force the marker onto the invocation line -- contorting the docs to suit the guard,
    which is how a guard earns its way into being switched off.
    """
    joined: list[tuple[int, str]] = []
    buffer, start = "", 0
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\r")
        if not buffer:
            start = number
        if line.rstrip().endswith("\\"):
            buffer += line.rstrip()[:-1] + " "
            continue
        joined.append((start, buffer + line))
        buffer = ""
    if buffer:
        joined.append((start, buffer))
    return joined


def _documents(root: Path) -> list[Path]:
    found: list[Path] = []
    for entry in DOC_ROOTS:
        target = root / entry
        if target.is_file():
            found.append(target)
        elif target.is_dir():
            found.extend(sorted(target.rglob("*.md")))
    return found


def main() -> int:
    root = project_root()
    violations: list[Violation] = []

    suppressed = 0
    examined = 0
    for document in _documents(root):
        for number, line in _logical_lines(document.read_text(encoding="utf-8")):
            match = INVOCATION.search(line)
            if not match:
                continue
            dotted = match.group("module")
            if dotted.split(".")[0] in THIRD_PARTY:
                continue
            examined += 1
            if UNBUILT in line:
                suppressed += 1
                continue
            path = _module_path(root, dotted)
            if path is None:
                violations.append(
                    Violation(
                        document,
                        number,
                        "documented-command",
                        f"`python -m {dotted}` names a module that does not exist",
                    )
                )
            elif not _has_entry_point(path):
                violations.append(
                    Violation(
                        document,
                        number,
                        "documented-command",
                        f"`python -m {dotted}` has no `__main__` block: it exits 0, "
                        f"writes nothing, and reads as success",
                    )
                )

    if suppressed:
        # Printed every run, clean or not: an unbuilt command is a known gap in the
        # instrument, and this guard exists because such a gap was once invisible.
        print(f"[documented-commands] {suppressed} documented command(s) NOT BUILT", flush=True)
    assert_examined("documented python -m invocations", examined, FLOOR, root)
    return report(violations, root, "documented-commands")


if __name__ == "__main__":
    # Refused HERE, not inside main(): inside, `sys.argv` belongs to whoever
    # imported this module -- under pytest that is pytest's own command line.
    sys.exit(refuse_path_argument(sys.argv, "documented-commands") or main())
