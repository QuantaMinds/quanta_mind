"""A dated external figure must be re-checked on its stated cadence, or it fails here.

WHAT: Finds every figure marked `re-check <Month YYYY>` in the documents and fails when that
      date has passed. One rule: if a number carries a re-check date, the date is enforced.
WHY:  Every other mechanism in this repository reports what it did -- the drop-rate counter,
      the shadow ranker, the retention counter, the bin-sum check against an independently
      known total. The citation cadence was the only one left that depended on somebody
      remembering, and it guards the failure class this repository has already produced
      twice: a correct citation that went stale. CodeRabbit's leaderboard claim was accurate
      when written and superseded five months later; a 2021 study sat beside a 2026 one for
      one commit. Neither was a wrong citation when made.
      A cadence nobody owns is a wish. This makes the calendar the owner.
IMPORTS: scripts/guard/discovery.py; stdlib datetime and re.
CONSUMED BY: justfile (`just check`), .github/workflows/guards.yml.
"""

from __future__ import annotations

import sys
from pathlib import Path

# The guards import each other by bare name, which works because Python puts a script's own
# directory on sys.path[0]. These two live one level down, so the parent is added explicitly
# rather than relying on an invocation style. A guard that only runs from one directory is a
# guard that stops running when someone moves the recipe.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import re
import sys
from datetime import date
from pathlib import Path

from discovery import Violation, iter_text_files, project_root, report

# `re-check November 2026`, `re-check due Nov 2026`. Case-insensitive, "due" optional.
RECHECK = re.compile(r"re-check(?:\s+due)?\s+([A-Z][a-z]{2,8})\s+(\d{4})", re.IGNORECASE)

MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

# Prose describing the rule rather than carrying a dated figure. Same escape as the other
# guards: counted and printed, never silent.
ALLOW = "citation-freshness:allow"


def _due(month_word: str, year_text: str) -> date | None:
    """First day of the stated month, or None when the month name is not one."""
    key = month_word[:3].lower()
    if key not in MONTHS:
        return None
    try:
        return date(int(year_text), MONTHS[key], 1)
    except ValueError:
        return None


def scan(root: Path, today: date) -> tuple[list[Violation], int, int]:
    """Every re-check date found, and whether it has passed.

    Returns violations, the number of dated figures found, and the number suppressed.
    **The count is returned and printed even when clean**, because a guard that finds
    nothing and a guard whose pattern stopped matching print the same thing otherwise --
    which is the failure this file exists to prevent, applied to itself.
    """
    violations: list[Violation] = []
    found = suppressed = 0
    for path in iter_text_files(root):
        if path.name == Path(__file__).name:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(lines, start=1):
            match = RECHECK.search(line)
            if match is None:
                continue
            if ALLOW in line:
                suppressed += 1
                continue
            due = _due(match.group(1), match.group(2))
            if due is None:
                continue
            found += 1
            if due <= today:
                violations.append(
                    Violation(
                        path,
                        number,
                        "citation-stale",
                        f"re-check was due {match.group(1)} {match.group(2)}. Read the source "
                        f"again, update the figure and the date, or remove the claim. A correct "
                        f"citation that went stale is the failure this repository has produced "
                        f"twice.",
                    )
                )
    return violations, found, suppressed


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else project_root()
    violations, found, suppressed = scan(root, date.today())
    code = report(violations, root, "citation-freshness")
    print(
        f"[citation-freshness] {found} dated figure(s) tracked, {suppressed} suppressed with "
        f"'{ALLOW}'"
    )
    if found == 0 and not violations:
        print(
            "[citation-freshness] WARNING: no dated figures found at all. Either none is "
            "load-bearing, or the pattern stopped matching. Check before believing this."
        )
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
