"""Reject references that stop resolving when something is renamed or renumbered.

WHAT: Scans tracked text files for two classes of reference that read as precise and
      are not: section-number citations (`§7`, `RUNBOOK §2.1`) and phase-number
      citations (`Phase 0`, `Phase 4`).
WHY:  Both break silently. Insert a section into a document and every `§7` in the
      repository now points somewhere else, with nothing to catch it -- no test fails,
      no link 404s, and the sentence still reads correctly. Phase numbers are worse:
      they name a position in a plan rather than a thing, so when the plan changes the
      reference does not become wrong, it becomes meaningless.

      A durable reference names something that has to be renamed deliberately: a file
      path, a class, a function, or a heading's text. `check_conventions.py` already
      requires each module's docstring to say what it imports and who consumes it, for
      the same reason -- a reference you cannot follow is not documentation.

      Replace with a file plus a quoted heading, or a `file.py:symbol`:

          §7's gate               ->  PHASE0_RUNBOOK.md, "The 20-PR hand-labelling gate"
          RUNBOOK §2.1            ->  PHASE0_RUNBOOK.md, "Positive control"
          ARCHITECTURE.md §6      ->  ARCHITECTURE.md, "Invariants"
          Phase 0                 ->  the correlation test
          Phase 3                 ->  the probe layer

IMPORTS: scripts.guard.discovery, stdlib re.
CONSUMED BY: `just guards`; scripts/guard/hook_post_edit.py; CI.
"""

from __future__ import annotations

import pathlib
import re
import sys
from pathlib import Path

# Running a guard as a script puts only ITS directory on sys.path[0]. This one lives one level
# down, so the parent is added explicitly -- the same reason `citations/` does it.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from coverage import assert_examined
from discovery import iter_text_files, project_root

# **A FLOOR, NOT A TARGET.** 178 tracked markdown files today.
MARKDOWN_FLOOR = 40

# `§` followed by a digit. The bare symbol is allowed nowhere useful, so match it alone
# too -- it is never correct in this repository and always means a section citation.
SECTION_REF = re.compile(r"§")

# "Phase 0", "Phase 0c", "phase 4". Not `phase0` -- that is a package name, which is a
# real identifier and therefore a durable reference.
PHASE_REF = re.compile(r"\bPhase\s+\d[a-z]?\b", re.IGNORECASE)

# Names taken from each plan section's own heading, so they are not inventions.
PHASE_NAMES = {
    "0": "the correlation test",
    "0b": "the symptom vocabulary study",
    "0c": "the pull-based retrieval test",
    "1": "the call-site census layer",
    "2": "the label layer",
    "3": "the probe layer",
    "4": "the MRO and framework resolvers",
    "5": "the MCP server",
    "6": "the PR comment and free tier",
}

# This file necessarily contains the patterns it bans. Derived from __file__ rather than written
# out, because the literal path went stale the moment this guard moved into `records/` -- and the
# symptom was the guard reporting fifteen violations against its own docstring.
EXEMPT = {
    str(pathlib.Path(__file__).resolve().relative_to(pathlib.Path.cwd()))
    if pathlib.Path(__file__).resolve().is_relative_to(pathlib.Path.cwd())
    else "scripts/guard/records/check_no_vague_refs.py",
    "scripts/guard/records/check_no_vague_refs.py",
    "tests/unit/test_no_vague_refs.py",
}

# A rule that forbids a pattern has to be able to show the pattern. This marker suppresses
# one line, and every use is counted and printed even on success -- an escape hatch nobody
# can see is an escape hatch that spreads. It belongs in AGENTS.md's rule 12 and nowhere
# obvious else; if the count starts climbing, the rule is being worked around.
ALLOW = "no-vague-refs:allow"


def _suggestion(match: str) -> str:
    number = re.sub(r"(?i)^phase\s+", "", match).lower()
    named = PHASE_NAMES.get(number)
    return f'"{match}" -> {named}' if named else f'"{match}" -> name the work, not its number'


def violations(root: Path) -> tuple[list[str], int]:
    """Every banned reference as `path:line: message`, plus the suppression count."""
    found: list[str] = []
    suppressed = 0
    for path in iter_text_files(root):
        relative = path.relative_to(root).as_posix()
        if relative in EXEMPT:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(lines, start=1):
            if ALLOW in line:
                suppressed += 1
                continue
            if SECTION_REF.search(line):
                found.append(
                    f"{relative}:{number}: [section-ref] `§` cites a number that "
                    f"renumbers silently. Name the file and quote the heading instead."
                )
            for phase in PHASE_REF.findall(line):
                found.append(f"{relative}:{number}: [phase-ref] {_suggestion(phase)}")
    return found, suppressed


def main() -> int:
    root = project_root()
    found, suppressed = violations(root)
    # **A FLOOR, NOT A TARGET.** 178 tracked markdown files today; this fires only if the file
    # discovery collapses, which would otherwise print "clean" over nothing.
    assert_examined("markdown documents", sum(1 for _ in root.rglob("*.md")), MARKDOWN_FLOOR, root)
    note = f" ({suppressed} line(s) suppressed with {ALLOW!r})" if suppressed else ""
    if not found:
        print(f"no-vague-refs: clean{note}")
        return 0
    print(f"[no-vague-refs] {len(found)} violation(s):")
    for line in found[:60]:
        print(f"  {line}")
    if len(found) > 60:
        print(f"  …and {len(found) - 60} more")
    print(
        "\nA reference must name something that has to be renamed deliberately: a file "
        "path, a class, a function, or a heading's exact text."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
