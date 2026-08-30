"""Change a constant, run the tests, and report the ones nothing noticed.

WHAT: `python scripts/mutate/sweep.py` mutates every module-level numeric constant in the
      files this branch changed and names what the suite fails to catch. `--all` sweeps a tree.
WHY:  **A SUITE CAN PASS EXHAUSTIVELY WHILE THE NUMBERS IT DEPENDS ON ARE FREE TO MOVE.** Run
      against `scripts/guard` this found 15 of 17 thresholds weakenable with everything green,
      the pre-edit hook's `DENY` among them — at 0 it turns every refusal into a permission.

      **THE BASELINE IS RUN FIRST AND A RED ONE REFUSES**: if the suite already fails, every
      mutation reads as caught and the report claims total coverage. An empty population refuses
      too — nothing to mutate is not a clean sweep.

      **IT RESTORES WHAT IT TOUCHED AND RE-READS EVERY FILE**: a mutation left behind is a
      corrupted tree that looks like ordinary work.
IMPORTS: stdlib only. Never `quantamind`: it must work when a mutation breaks the import.
CONSUMED BY: a person. `scripts/mutate/verdict.py` decides what the results MEAN.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from verdict import verdict

GIT_TIMEOUT_S, SUITE_TIMEOUT_S = 60, 1800
TESTS = ("tests/unit", "tests/property")


class Refused(RuntimeError):
    """The sweep cannot produce a meaningful verdict, and says so rather than producing one."""


@dataclass(frozen=True, slots=True)
class Target:
    """One constant and the value to try in its place."""

    path: Path
    line: int
    column: int
    old: str
    new: str
    name: str

    def label(self) -> str:
        return f"{self.name} {self.old}->{self.new} ({self.path})"


def targets_in(paths: list[Path]) -> list[Target]:
    """Every module-level numeric constant in `paths`, with two replacements tried for each."""
    found: list[Target] = []
    for path in sorted(paths):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        for node in ast.parse(text).body:
            if not isinstance(node, ast.Assign | ast.AnnAssign):
                continue
            names = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            if not isinstance(value, ast.Constant) or isinstance(value.value, bool):
                continue
            if not isinstance(value.value, int | float):
                continue
            for name in names:
                if not (isinstance(name, ast.Name) and name.id.isupper()):
                    continue
                # A replacement equal to the original is never applied and would be recorded as
                # a survivor, inflating the count with mutations that never happened.
                # **THE SOURCE TEXT, NOT `repr(value)`.** `30_000` reprs to "30000", five
                # characters against six on the line, so the slice landed on "30_00" and the
                # sweep refused at the third such constant rather than corrupting the file.
                written = lines[value.lineno - 1][value.col_offset : value.end_col_offset or 0]
                for new in (type(value.value)(0), value.value * 2 + 1):
                    if new != value.value:
                        found.append(
                            Target(
                                path, value.lineno, value.col_offset, written, repr(new), name.id
                            )
                        )
    return found


def python_files(root: Path, base: str | None) -> list[Path]:
    """The files to sweep: everything under `root`, or only what this branch changed."""
    if base is None:
        return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]
    done = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD", "--", str(root)],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_S,
        check=False,
    )
    if done.returncode != 0:
        raise Refused(
            f"cannot diff against {base}: {done.stderr.strip() or 'git failed'}. "
            f"Pass --all to sweep the tree instead of guessing what changed."
        )
    return [Path(n) for n in done.stdout.split() if n.endswith(".py") and Path(n).is_file()]


def suite_passes() -> bool:
    """True when the suite passes. Bytecode is cleared first: a same-length edit inside one
    second leaves a valid `.pyc`, and the tests then import the pre-mutation value."""
    subprocess.run(
        ["find", "src", "scripts", "tests", "-name", "*.pyc", "-delete"],
        timeout=GIT_TIMEOUT_S,
        check=False,
        capture_output=True,
    )
    done = subprocess.run(
        [sys.executable, "-m", "pytest", *TESTS, "-x", "-q", "--timeout=120"],
        capture_output=True,
        text=True,
        timeout=SUITE_TIMEOUT_S,
        check=False,
    )
    return done.returncode == 0


def _write(target: Target, text: str) -> None:
    lines = text.splitlines(keepends=True)
    line = lines[target.line - 1]
    seen = line[target.column : target.column + len(target.old)]
    if seen != target.old:
        raise Refused(
            f"{target.path}:{target.line} holds {seen!r}, not {target.old!r}; "
            f"the file moved under the sweep and nothing was mutated."
        )
    lines[target.line - 1] = (
        line[: target.column] + target.new + line[target.column + len(target.old) :]
    )
    target.path.write_text("".join(lines), encoding="utf-8")


def sweep(targets: list[Target]) -> tuple[list[tuple[Target, bool]], list[Path]]:
    """Every mutation in turn. Returns (target, caught) for each, and any file left changed."""
    if not targets:
        raise Refused(
            "no numeric constants found. Either the tree holds none or discovery is "
            "broken; both are reasons to stop rather than report a clean sweep."
        )
    print(f"[mutate] baseline: {' '.join(TESTS)} before mutating anything", flush=True)
    if not suite_passes():
        raise Refused(
            f"{' '.join(TESTS)} fails before any mutation, so every mutation would "
            f"read as caught. Fix the suite first."
        )

    before = {t.path: t.path.read_text(encoding="utf-8") for t in targets}
    results: list[tuple[Target, bool]] = []
    for number, target in enumerate(targets, 1):
        try:
            _write(target, before[target.path])
            caught = not suite_passes()
        finally:
            target.path.write_text(before[target.path], encoding="utf-8")
        results.append((target, caught))
        verdict = "caught  " if caught else "SURVIVED"
        print(f"[mutate] {number}/{len(targets)} {verdict} {target.label()}", flush=True)

    left = [p for p, text in before.items() if p.read_text(encoding="utf-8") != text]
    return results, left


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="mutate constants; report what nothing catches")
    parser.add_argument("--root", default="src/quantamind")
    parser.add_argument("--all", action="store_true", help="sweep the tree, not just the diff")
    parser.add_argument("--base", default="main", help="branch to diff against")
    args = parser.parse_args(argv[1:])
    root = Path(args.root)
    if not root.is_dir():
        print(f"[mutate] no tree at {root}", file=sys.stderr)
        return 2
    try:
        files = python_files(root, None if args.all else args.base)
        if not files:
            print(f"[mutate] {args.base}...HEAD changes no Python file under {root}")
            return 0
        results, left = sweep(targets_in(files))
    except Refused as refusal:
        print(f"[mutate] {refusal}", file=sys.stderr)
        return 2

    for path in left:
        print(f"[mutate] NOT RESTORED: {path}", file=sys.stderr)

    survivors = [t for t, caught in results if not caught]
    for line in verdict(results):
        print(line)
    return 1 if survivors or left else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
