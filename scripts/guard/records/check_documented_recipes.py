"""A documented `just` recipe or `quantamind` subcommand must exist, or be marked unbuilt.

WHAT: Scans the documentation for `just <recipe>` and `quantamind <subcommand>` and checks each
      one against reality -- the recipe names in the justfile, and the subparsers registered in
      `serve/cli.py`. A subcommand `cli.py` itself lists as unbuilt must carry
      `documented-command:unbuilt` on the documenting line.
WHY:  `check_documented_commands.py` matches `python -m` and nothing else, so two whole classes of
      documented command were invisible to it. **`just fixtures` exited 1 on every invocation it
      ever had** -- it ran `git submodule update --init tests/fixtures/repos` against a repository
      with no `.gitmodules` and no submodules registered -- and CONTRIBUTING.md described it as
      working. Nobody noticed, because the only reader who would have run it was told it was not
      needed yet. That is the same failure the sibling guard was written for, arriving through the
      door it does not watch.

      SPLIT RATHER THAN EXTENDED. The sibling is 192 lines against a 200-line cap, and this needs
      a justfile parser and an AST read of the CLI. Both guards answer to the rule "a documented
      command must run" and the enforcement map names both.

      THE CLI'S OWN `UNBUILT` DICT IS THE SOURCE OF TRUTH, read from the AST rather than
      duplicated here. A list of unbuilt commands maintained in a guard would go stale the moment
      one was built, and would then demand the marker on a command that works.
IMPORTS: scripts/guard/discovery.py; stdlib ast, re. No project imports.
CONSUMED BY: `just guards`; CI.
"""

from __future__ import annotations

import ast
import re
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path

# Running a guard as a script puts only ITS directory on sys.path[0]. This one lives one level
# down, so the parent is added explicitly -- the same reason its sibling does it.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coverage import assert_examined, guarded, refuse_path_argument
from discovery import Violation, project_root, report

# **A FLOOR, NOT A TARGET.** Below today's count, to catch discovery collapsing.
RECIPE_FLOOR = 20

DOC_ROOTS = (
    "docs/findings",
    "docs/engineering/CODEBASE.md",
    "docs/engineering/CLI.md",
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "BRIEFING.md",
)
CLI = "src/quantamind/serve/cli.py"
UNBUILT = "documented-command:unbuilt"

# `just <recipe>`, and `quantamind <subcommand>` however it is invoked -- bare or after `uv run`.
JUST_CALL = re.compile(r"\bjust\s+(?P<recipe>[a-z][a-z0-9-]*)")
QM_CALL = re.compile(r"\bquantamind\s+(?P<command>[a-z][a-z0-9-]*)")
# A recipe definition: a name at column 0, optional parameters, then a colon.
RECIPE_DEF = re.compile(r"^([a-z][a-z0-9-]*)\s*(?:[A-Za-z0-9_= \"'.]*)?:", re.MULTILINE)
# Only CODE is scanned: a fenced block, or a backtick span. Prose says "just falsified the
# hypothesis" and means the adverb. The alternative -- a blocklist of English words -- is a
# blocklist that goes stale silently, which is the defect class this guard exists to catch.
FENCE = re.compile(r"^\s*```")
BACKTICKED = re.compile(r"`([^`]+)`")


def _finds(pattern: re.Pattern[str], spans: Sequence[str]) -> Iterator[re.Match[str]]:
    """Matches inside EACH span separately, never across the gap between two of them.

    The first version joined the spans with a space and scanned once, which SYNTHESISED commands
    that no span contained. A sentence mentioning `quantamind` and `just` and
    `docs/engineering/CLI.md` became "quantamind just docs/engineering/CLI.md", out of which this
    guard read a subcommand `quantamind just` and a recipe `just docs` -- two invocations nobody
    had written, both reported as violations against correct prose.

    It failed loudly, which is the right direction for a guard to fail in, but it fails on text
    that is fine: any line with two adjacent code spans can manufacture a phantom command. The
    join was never needed -- a command lives inside ONE span or it is not a command.
    """
    for span in spans:
        yield from pattern.finditer(span)


def _recipes(root: Path) -> set[str]:
    justfile = root / "justfile"
    return (
        set(RECIPE_DEF.findall(justfile.read_text(encoding="utf-8")))
        if justfile.is_file()
        else set()
    )


def _cli_commands(root: Path) -> tuple[set[str], set[str]]:
    """(every registered subcommand, the ones the CLI itself calls unbuilt)."""
    path = root / CLI
    if not path.is_file():
        return set(), set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    registered: set[str] = set()
    unbuilt: set[str] = set()
    for node in ast.walk(tree):
        # subparsers.add_parser("config", ...)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_parser"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            registered.add(node.args[0].value)
        # UNBUILT: dict[str, str] = {"review": "...", ...}
        if isinstance(node, ast.AnnAssign | ast.Assign):
            target = node.target if isinstance(node, ast.AnnAssign) else node.targets[0]
            if isinstance(target, ast.Name) and target.id == "UNBUILT":
                value = node.value
                if isinstance(value, ast.Dict):
                    for key in value.keys:
                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                            unbuilt.add(key.value)
    return registered | unbuilt, unbuilt


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
    recipes = _recipes(root)
    commands, unbuilt = _cli_commands(root)
    violations: list[Violation] = []
    suppressed = checked = 0

    for document in _documents(root):
        fenced = False
        for number, line in enumerate(document.read_text(encoding="utf-8").splitlines(), 1):
            if FENCE.match(line):
                fenced = not fenced
                continue
            spans = [line] if fenced else BACKTICKED.findall(line)
            for match in _finds(JUST_CALL, spans):
                name = match.group("recipe")
                checked += 1
                if UNBUILT in line:
                    suppressed += 1
                elif name not in recipes:
                    violations.append(
                        Violation(
                            document,
                            number,
                            "documented-recipe",
                            f"`just {name}` names no recipe in the justfile",
                        )
                    )
            for match in _finds(QM_CALL, spans):
                name = match.group("command")
                checked += 1
                if UNBUILT in line:
                    suppressed += 1
                elif name not in commands:
                    violations.append(
                        Violation(
                            document,
                            number,
                            "documented-recipe",
                            f"`quantamind {name}` is not a registered subcommand",
                        )
                    )
                elif name in unbuilt:
                    violations.append(
                        Violation(
                            document,
                            number,
                            "documented-recipe",
                            f"`quantamind {name}` is listed UNBUILT in cli.py and exits 2 — "
                            f"document it as not built, or mark it {UNBUILT}",
                        )
                    )

    assert_examined("documented invocations", checked, RECIPE_FLOOR, root)
    print(f"[documented-recipes] {checked} documented invocation(s) checked", flush=True)
    if suppressed:
        print(f"[documented-recipes] {suppressed} documented command(s) NOT BUILT", flush=True)
    return report(violations, root, "documented-recipes")


if __name__ == "__main__":
    # Refused HERE, not inside main(): inside, `sys.argv` belongs to whoever
    # imported this module -- under pytest that is pytest's own command line.
    sys.exit(refuse_path_argument(sys.argv, "documented-recipes") or guarded(lambda: main()))
