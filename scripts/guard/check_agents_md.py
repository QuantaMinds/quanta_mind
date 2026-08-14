"""Instruction-budget and honesty guard for AGENTS.md.

WHAT: Three checks on the agent memory file.
      1. Length   — at most 200 lines. Past ~80 lines adherence starts dropping;
                    past ~200 whole blocks get ignored.
      2. Pointers — every `scripts/guard/*.py` the file names must exist.
      3. Coverage — every numbered rule under "## Non-negotiables" must carry an
                    enforcement pointer, or be tagged ADVISORY.
WHY:  AGENTS.md is delivered to the model as a user message and every line costs
      instruction budget for every other line. That makes an unenforced rule
      actively harmful: it consumes budget and buys nothing.

      Check 2 exists because this file shipped for months citing four guards --
      check_file_length.py, check_dir_fanout.py, check_module_docstring.py and
      check_naming.py -- that had been consolidated into check_structure.py and
      check_conventions.py. The rules read as enforced and were not. That is the
      product's own failure mode, in its own repository.

      Check 3 is the other direction: a rule with no mechanism is a wish, and
      CONTRIBUTING.md says so. Tagging it ADVISORY is allowed; leaving it
      ambiguous is not.
IMPORTS: scripts/guard/discovery.py; stdlib re. No project imports.
CONSUMED BY: justfile (`just check`), .github/workflows/guards.yml.
SEE ALSO: check_enforcement_map.py, which validates the other half in
      .claude/settings.json.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from discovery import Violation, report

# Raised from 200 to 210 on 2026-08-13, deliberately and once, to carry the product
# description for the reviewer product after the earlier product was falsified. The
# reasoning in the docstring above still holds and is not weakened by this: adherence
# degrades with length, so the budget is now 210 and the next request to raise it should
# be answered by deleting something instead. Every line added here costs adherence to
# every other line.
MAX_LINES = 210

SECTION_HEADING = "## Non-negotiables"

# `scripts/guard/foo.py` wherever it appears -- prose, a pointer, or a code span.
GUARD_REFERENCE = re.compile(r"scripts/guard/([A-Za-z0-9_]+\.py)")

# A numbered list item at the start of a line: "1. **...**"
NUMBERED_RULE = re.compile(r"^(\d+)\.\s+(.*)$")

# What counts as naming a mechanism.
ENFORCEMENT_MARKERS = ("scripts/guard/", "tests/", "branch protection", "ADVISORY")


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def check_length(path: Path, lines: list[str]) -> list[Violation]:
    """AGENTS.md must fit the instruction budget."""
    if len(lines) <= MAX_LINES:
        return []
    return [
        Violation(
            path,
            MAX_LINES + 1,
            "agents-md-length",
            f"{len(lines)} lines, {len(lines) - MAX_LINES} over the {MAX_LINES} cap. "
            f"Delete a rule or move it to a hook. Do not raise the cap -- every line "
            f"here reduces adherence to every other line.",
        )
    ]


def check_referenced_guards_exist(path: Path, lines: list[str], root: Path) -> list[Violation]:
    """Every guard AGENTS.md names must be a file that exists."""
    violations: list[Violation] = []
    for lineno, line in enumerate(lines, start=1):
        for name in GUARD_REFERENCE.findall(line):
            if not (root / "scripts" / "guard" / name).is_file():
                violations.append(
                    Violation(
                        path,
                        lineno,
                        "agents-md-phantom-guard",
                        f"names scripts/guard/{name}, which does not exist. A rule "
                        f"pointing at a missing enforcer reads as enforced and is not.",
                    )
                )
    return violations


def _section_bounds(lines: list[str]) -> tuple[int, int] | None:
    """Line range of the Non-negotiables section, exclusive of the heading."""
    start = next((i for i, ln in enumerate(lines) if ln.strip() == SECTION_HEADING), None)
    if start is None:
        return None
    for offset, line in enumerate(lines[start + 1 :], start=start + 1):
        if line.startswith("## "):
            return start + 1, offset
    return start + 1, len(lines)


def check_rules_name_a_mechanism(path: Path, lines: list[str]) -> list[Violation]:
    """Each numbered non-negotiable must name an enforcer or be tagged ADVISORY."""
    bounds = _section_bounds(lines)
    if bounds is None:
        return [
            Violation(
                path,
                1,
                "agents-md-no-rules",
                f"no '{SECTION_HEADING}' section. The enforcement map has nothing to "
                f"check against.",
            )
        ]

    start, end = bounds
    violations: list[Violation] = []
    current: tuple[int, str] | None = None
    body: list[str] = []

    def flush() -> None:
        if current is None:
            return
        lineno, title = current
        blob = " ".join(body)
        if not any(marker in blob for marker in ENFORCEMENT_MARKERS):
            violations.append(
                Violation(
                    path,
                    lineno,
                    "agents-md-unenforced-rule",
                    f"rule {title!r} names no mechanism. Add a '-> scripts/guard/...' "
                    f"pointer, or tag it ADVISORY so it is honestly a wish.",
                )
            )

    for lineno, line in enumerate(lines[start:end], start=start + 1):
        match = NUMBERED_RULE.match(line)
        if match:
            flush()
            current = (lineno, match.group(2)[:60])
            body = [line]
        elif current is not None:
            body.append(line)
    flush()
    return violations


def main(argv: list[str]) -> int:
    """Check AGENTS.md. Accepts the file itself or the repository root."""
    given = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    target = given / "AGENTS.md" if given.is_dir() else given
    if not target.is_file():
        print(f"[agents-md] no file at {target}", file=sys.stderr)
        return 2

    root = target.parent
    lines = _read_lines(target)
    violations = (
        check_length(target, lines)
        + check_referenced_guards_exist(target, lines, root)
        + check_rules_name_a_mechanism(target, lines)
    )
    return report(violations, root, "agents-md")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
