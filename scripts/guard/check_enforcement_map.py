"""Validates $enforcement_map in .claude/settings.json against reality.

WHAT: Two checks, one in each direction.
      1. Resolution — every `guard:`, `ci:` and `hook:` token in the map must name
                      something that exists: a guard file, a justfile recipe or
                      workflow job, or a hook event actually registered.
      2. Orphans    — every file in scripts/guard/ and its subdirectories must be
                      invoked by the justfile,
                      a workflow, or settings.json.
WHY:  The map is the repository's claim about which rules are mechanically
      enforced. Fixing it by hand once does not stop it drifting again, and drift
      here is invisible: a row can name a guard that was renamed, or a guard can
      exist and never run, and both look fine in review.

      Check 2 is the mirror image of the phantom-guard bug in check_agents_md.py.
      A guard nobody invokes is worse than no guard -- the rule appears covered
      and the file makes it look deliberate.
IMPORTS: scripts/guard/discovery.py; stdlib json, re. No project imports.
CONSUMED BY: justfile (`just check`), .github/workflows/guards.yml.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from discovery import Violation, report

TOKEN = re.compile(r"\b(guard|ci|hook):([A-Za-z0-9_.-]+)")

# Recipe names in the justfile: a line starting at column 0 ending in ':'.
JUST_RECIPE = re.compile(r"^([a-z][a-z0-9-]*)\s*(?:[A-Za-z0-9_= \"'.]*)?:", re.MULTILINE)

# Guards that are invoked by Claude Code rather than by a recipe. They still have
# to appear in settings.json, which the orphan check verifies.
HOOK_PREFIX = "hook_"


def _load_map(settings: Path) -> dict[str, str]:
    raw = json.loads(settings.read_text(encoding="utf-8"))
    entries = raw.get("$enforcement_map", {})
    return {k: v for k, v in entries.items() if not k.startswith("$")}


def _hook_events(settings: Path) -> set[str]:
    raw = json.loads(settings.read_text(encoding="utf-8"))
    return set(raw.get("hooks", {}))


def _just_recipes(root: Path) -> set[str]:
    justfile = root / "justfile"
    if not justfile.is_file():
        return set()
    return set(JUST_RECIPE.findall(justfile.read_text(encoding="utf-8")))


def _workflow_text(root: Path) -> str:
    workflows = root / ".github" / "workflows"
    if not workflows.is_dir():
        return ""
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(workflows.glob("*.yml")))


def check_tokens_resolve(settings: Path, root: Path) -> list[Violation]:
    """Every guard:/ci:/hook: token must name something that exists."""
    violations: list[Violation] = []
    recipes = _just_recipes(root)
    events = _hook_events(settings)
    workflows = _workflow_text(root)

    for rule, value in _load_map(settings).items():
        for kind, name in TOKEN.findall(value):
            if kind == "guard":
                ok = (root / "scripts" / "guard" / f"{name}.py").is_file()
                detail = f"scripts/guard/{name}.py does not exist"
            elif kind == "ci":
                ok = name in recipes or name in workflows
                detail = f"'{name}' is neither a justfile recipe nor a job in .github/workflows/"
            else:
                ok = name in events
                detail = f"'{name}' is not a hook event registered in this file"

            if not ok:
                violations.append(
                    Violation(
                        settings,
                        1,
                        "enforcement-unresolved",
                        f"rule {rule!r} claims {kind}:{name}, but {detail}. The map is "
                        f"what we claim is enforced; an unresolvable claim is a wish.",
                    )
                )
    return violations


def check_no_orphan_guards(settings: Path, root: Path) -> list[Violation]:
    """Every guard must be invoked by something."""
    guard_dir = root / "scripts" / "guard"
    if not guard_dir.is_dir():
        return []

    invokers = "\n".join(
        [
            (root / "justfile").read_text(encoding="utf-8")
            if (root / "justfile").is_file()
            else "",
            settings.read_text(encoding="utf-8"),
            _workflow_text(root),
        ]
    )

    violations: list[Violation] = []
    # rglob: hooks live in scripts/guard/hooks/ since the directory hit its fan-out
    # cap. A non-recursive glob would silently stop checking them for orphan
    # status -- the guard-that-guards-guards quietly covering less than it says.
    for path in sorted(guard_dir.rglob("*.py")):
        # discovery.py is the shared walker, imported rather than invoked.
        if path.name == "discovery.py":
            continue
        if path.name not in invokers:
            where = "settings.json" if path.name.startswith(HOOK_PREFIX) else "the justfile or CI"
            violations.append(
                Violation(
                    path,
                    1,
                    "orphan-guard",
                    f"nothing invokes this guard. Register it in {where}, or delete it. "
                    f"A guard that never runs makes a rule look covered when it is not.",
                )
            )
    return violations


def main(argv: list[str]) -> int:
    """Check the enforcement map against the repository root."""
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    settings = root / ".claude" / "settings.json"
    if not settings.is_file():
        print(f"[enforcement-map] no settings at {settings}", file=sys.stderr)
        return 2

    violations = check_tokens_resolve(settings, root) + check_no_orphan_guards(settings, root)
    return report(violations, root, "enforcement-map")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
