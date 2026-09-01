"""An amendment that withdraws a code change must name the check that enforces it.

WHAT: Scans the amendment log for rows declaring something ABANDONED or WITHDRAWN, and
      requires each to name a `guard:`, `ci:` or `hook:` mechanism that exists -- or to
      tag itself ADVISORY.
WHY:  A31 pre-registered a stop rule, the known-answer test failed, and `--filter=blob:none`
      was declared ABANDONED. The commit recording that touched thirteen files: docs and
      results, no source. The flag stayed in `pipeline/worktree.py` and two pilot arms
      were walked under the withdrawn strategy before anything noticed.

      Its failure mode is that a diff over blobs which never arrived is EMPTY rather than
      wrong, so the harness writes `no_python` -- a claim about the repository -- when the
      truth is that a lazy fetch returned nothing. An agent-arm `no_python` rate of 18.1%
      against the human arm's 4.0% was read as a finding about how agents write code.

      This is a class the other guards do not cover. They catch code producing a wrong
      VALUE. This catches code and documentation DISAGREEING, with the documentation
      authoritative and unenforced. `$enforcement_map` already pairs every AGENTS.md rule
      with a mechanism for exactly this reason; a withdrawal is a rule too -- "this must
      no longer be in the code" -- and it was the one kind nothing checked.

      A withdrawal that genuinely needs no mechanism is allowed, and must say ADVISORY.
      Being unable to enforce something is a fine answer; not noticing is not.
IMPORTS: scripts/guard/discovery.py; stdlib re. No project imports.
CONSUMED BY: `just guards`; CI.
"""

from __future__ import annotations

import pathlib
import re
import sys
from pathlib import Path

# Running a guard as a script puts only ITS directory on sys.path[0]. This one lives one level
# down, so the parent is added explicitly -- the same reason `citations/` does it.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from coverage import assert_examined, guarded, refuse_path_argument
from discovery import Violation, project_root, report

LOG = Path("docs/findings/PHASE0_PREREGISTRATION.md")

# A row of the amendment table: `| **A31** | 4.20 | ... | ... |`
AMENDMENT_ROW = re.compile(r"^\|\s*\*\*(?P<id>A\d+)\*\*\s*\|")

# Words that declare a code change reversed. Matched only in CAPITALS: the log discusses
# withdrawal in prose constantly ("would be withdrawing", "withdrawn under its own rule"),
# and a case-insensitive match would fire on every mention and train people to ignore it.
WITHDRAWAL = re.compile(r"\b(ABANDONED|WITHDRAWN)\b")

MECHANISM = re.compile(r"\b(guard|ci|hook):([A-Za-z0-9_./-]+)")
"""**`/` IS PART OF THE NAME.** Guards live in sub-packages — `guard:runtime/check_no_partial_clone`
— and a pattern stopping at the slash resolved `guard:runtime`, reported it missing, and told the
author their enforcer did not exist. `check_enforcement_map.py` has accepted sub-package paths since
`guard:citations/freshness`; this one had not, so moving a guard into a directory made every
withdrawal that named it read as a phantom."""
ADVISORY = re.compile(r"\bADVISORY\b")


def check(root: Path | None = None) -> list[Violation]:
    base = root or project_root()
    path = base / LOG
    if not path.is_file():
        return []

    violations: list[Violation] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        row = AMENDMENT_ROW.match(line)
        if not row or not WITHDRAWAL.search(line):
            continue
        if ADVISORY.search(line):
            continue
        named = MECHANISM.findall(line)
        if not named:
            violations.append(
                Violation(
                    path=path,
                    line=number,
                    rule="withdrawal-without-enforcer",
                    detail=(
                        f"{row.group('id')} declares a change ABANDONED or WITHDRAWN but names "
                        f"no `guard:`/`ci:`/`hook:` mechanism. A31 was honoured in prose while "
                        f"the flag stayed in the code and two arms were walked under it. Name "
                        f"the check, or tag the row ADVISORY."
                    ),
                )
            )
            continue
        for kind, name in named:
            if kind == "guard" and not (base / "scripts" / "guard" / f"{name}.py").is_file():
                violations.append(
                    Violation(
                        path=path,
                        line=number,
                        rule="withdrawal-phantom-enforcer",
                        detail=(
                            f"{row.group('id')} names guard:{name}, which does not exist. A "
                            f"withdrawal pointing at a missing enforcer reads as enforced and "
                            f"is not -- the same failure it is meant to prevent."
                        ),
                    )
                )
    return violations


# **A FLOOR, NOT A TARGET.** 56 amendment rows today; this fires only if the log stops parsing.
AMENDMENT_FLOOR = 20


def main() -> int:
    root = project_root()
    found = check()
    # **COUNTED THE WAY THE GUARD MATCHES.** `AMENDMENT_ROW` is anchored with `^` and compiled
    # without `re.M`, so `findall` over the whole document matches nothing — the floor fired on
    # a healthy repository until this counted per line, exactly as `check()` does.
    rows = (
        sum(1 for line in LOG.read_text(encoding="utf-8").splitlines() if AMENDMENT_ROW.match(line))
        if LOG.exists()
        else 0
    )
    assert_examined("amendment rows", rows, AMENDMENT_FLOOR, root)
    return report(found, root, "withdrawn-amendments")


if __name__ == "__main__":
    # Refused HERE, not inside main(): inside, `sys.argv` belongs to whoever
    # imported this module -- under pytest that is pytest's own command line.
    sys.exit(refuse_path_argument(sys.argv, "withdrawn-amendments") or guarded(lambda: main()))
