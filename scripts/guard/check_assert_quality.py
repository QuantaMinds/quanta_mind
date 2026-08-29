"""Test-quality guard: catches tests that are green without verifying anything.

WHAT: Statically inspects every test function and fails CI when the test cannot
      possibly have verified a behaviour — no assertions, assertions only on truthiness,
      assertions only against mocks, or a live test that never touches the real pipeline.
WHY:  This is the single highest-value guard in the repository. A green test suite is
      the most convincing lie a codebase can tell. Our product exists to expose silent
      failure in other people's systems; shipping silent failure in our own would be
      disqualifying. The specific patterns below are the ones that produce a passing
      test which proves nothing:
        - no assert at all (the function ran, therefore "it works")
        - `assert result` / `assert result is not None` (shape, not value)
        - every assert references a Mock (you asserted your own stub)
        - a file in tests/live/ that imports mock (live means live)
IMPORTS: scripts/guard/discovery.py; stdlib ast.
CONSUMED BY: justfile (`just check`), .github/workflows/guards.yml.
SEE ALSO: docs/engineering/VALIDATION.md for the doctrine this guard mechanises.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from coverage import assert_examined, guarded
from discovery import Violation, report

MOCK_TOKENS: frozenset[str] = frozenset(
    {"Mock", "MagicMock", "AsyncMock", "patch", "mocker", "monkeypatch", "stub", "fake"}
)

# Assertions that prove only that *something* came back, not that it is correct.
WEAK_COMPARATORS: frozenset[type[ast.cmpop]] = frozenset({ast.Is, ast.IsNot})


def _is_weak_assert(node: ast.Assert) -> bool:
    """True if the assertion checks existence or truthiness rather than a value."""
    test = node.test
    if isinstance(test, ast.Name | ast.Attribute | ast.Call):
        return True  # `assert result`, `assert obj.field`, `assert fn()`
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        op = test.ops[0]
        comparator = test.comparators[0]
        if type(op) in WEAK_COMPARATORS and isinstance(comparator, ast.Constant):
            return comparator.value is None  # `assert x is not None`
    return False


def _is_vacuous_assert(node: ast.Assert) -> bool:
    """True if the assertion cannot depend on the code under test at all.

    **`assert True` PASSED THIS GUARD.** `_is_weak_assert` classifies `Name`, `Attribute`, `Call`
    and `x is not None`; a bare `Constant` fell through every branch and was scored as a STRONG
    assertion. So did `assert 1`, `assert "x"`, `assert [1]`, `assert not False` and
    `assert 1 == 1` — a test containing only those verifies nothing and the guard printed ok.

    An expression naming nothing — no identifier, no attribute, no call, no subscript — is
    constant-folded before the test runs. It cannot be affected by the system, so it cannot be
    evidence about it. This is the guard for rule 1, and rule 1 is that a green test is not a
    verified test.
    """
    return not any(
        isinstance(child, ast.Name | ast.Attribute | ast.Call | ast.Subscript)
        for child in ast.walk(node.test)
    )


def _mentions_mock(node: ast.AST) -> bool:
    """True if any identifier in the subtree looks like a test double."""
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in MOCK_TOKENS:
            return True
        if isinstance(child, ast.Attribute) and child.attr in MOCK_TOKENS:
            return True
    return False


def _check_function(path: Path, fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[Violation]:
    """Apply every test-quality rule to a single test function."""
    violations: list[Violation] = []
    asserts = [n for n in ast.walk(fn) if isinstance(n, ast.Assert)]
    raises = [
        n
        for n in ast.walk(fn)
        if isinstance(n, ast.With | ast.AsyncWith) and "raises" in ast.dump(n)
    ]

    if not asserts and not raises:
        violations.append(
            Violation(
                path,
                fn.lineno,
                "test-no-assert",
                f"{fn.name}() has no assertion. A test that only proves 'no exception "
                f"was raised' is a silent failure. Assert on the value.",
            )
        )
        return violations

    if asserts and all(_is_vacuous_assert(a) for a in asserts):
        violations.append(
            Violation(
                path,
                fn.lineno,
                "test-vacuous-assert",
                f"{fn.name}() asserts only constants — `assert True`, `assert 1 == 1` and the "
                f"like. The expression names nothing, so it cannot depend on the code under "
                f"test and cannot fail. This is worse than no assertion: it looks like one.",
            )
        )
        return violations

    if asserts and all(_is_weak_assert(a) for a in asserts):
        violations.append(
            Violation(
                path,
                fn.lineno,
                "test-weak-assert",
                f"{fn.name}() only asserts truthiness or non-None. Assert the actual "
                f"value, or compare against a golden fixture.",
            )
        )

    if asserts and all(_mentions_mock(a) for a in asserts):
        violations.append(
            Violation(
                path,
                fn.lineno,
                "test-mock-only",
                f"{fn.name}() asserts exclusively against mocks. You verified your own "
                f"stub, not the system. Move this to tests/live/ or assert on real output.",
            )
        )
    return violations


def _check_live_purity(path: Path, tree: ast.Module) -> list[Violation]:
    """Files under tests/live/ must not import mocking machinery."""
    if "live" not in path.parts:
        return []
    for node in ast.walk(tree):
        module = ""
        if isinstance(node, ast.ImportFrom) and node.module:
            module = node.module
        elif isinstance(node, ast.Import):
            module = ",".join(alias.name for alias in node.names)
        if "mock" in module:
            return [
                Violation(
                    path,
                    getattr(node, "lineno", 1),
                    "live-test-mocked",
                    "tests/live/ imports a mocking library. Live tests run the real "
                    "pipeline against real repositories and diff against golden files.",
                )
            ]
    return []


def main(argv: list[str]) -> int:
    """Inspect every test module under the given root (default: ./tests)."""
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd() / "tests"
    if not root.is_dir():
        print(f"[assert-quality] no test directory at {root}", file=sys.stderr)
        return 2

    violations: list[Violation] = []
    for path in sorted(root.rglob("test_*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            violations.append(Violation(path, exc.lineno or 1, "test-syntax", str(exc.msg)))
            continue
        violations.extend(_check_live_purity(path, tree))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith(
                "test_"
            ):
                violations.extend(_check_function(path, node))

    assert_examined("test modules", sum(1 for _ in root.rglob("test_*.py")), 20, root)
    return report(violations, root, "assert-quality")


if __name__ == "__main__":
    raise SystemExit(guarded(lambda: main(sys.argv)))
