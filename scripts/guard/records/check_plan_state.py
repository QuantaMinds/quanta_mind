"""Regenerate the implementation plan's state block from the filesystem, and fail when it drifts.

WHAT: Counts the modules in each layer of `src/quantamind/`, renders a table between the
      `plan-state` markers in `docs/plans/implementation.md`, and exits non-zero when the file does
      not already contain exactly that. `--write` updates it.
WHY:  The plan carries a "Where this is now" section so a reader arriving cold knows what is built.
      **Ask what that section prints when it is wrong: the same thing.** It is prose, so it stays
      convincing for exactly as long as nobody checks it, and this project has already shipped a
      runbook whose "Days 3-5" reported success for a command that did nothing.

      This makes the one part that can be mechanised mechanical. It cannot check that a stage's
      prose is honest; it can check that a layer claiming zero modules has zero modules, which is
      the claim most likely to rot and the one a resuming reader acts on first.
IMPORTS: stdlib only (pathlib, re, sys).
CONSUMED BY: `just check` via the `guards` recipe.
"""

from __future__ import annotations

import pathlib
import sys

PLAN = pathlib.Path("docs/plans/implementation.md")
PACKAGE = pathlib.Path("src/quantamind")
BEGIN = "<!-- plan-state:begin -->"
END = "<!-- plan-state:end -->"
# Layer order is the product's spine; printing it in order is part of what the block is for.
LAYERS = (
    "types",
    "store",
    "ingest",
    "parse",
    "rank",
    "allocate",
    "infer",
    "verify",
    "render",
    "serve",
)


def render(root: pathlib.Path) -> str:
    """The state block as the filesystem says it is."""
    rows = [f"{BEGIN}", "", "| layer | modules | files |", "|---|---|---|"]
    for layer in LAYERS:
        d = root / PACKAGE / layer
        mods = (
            sorted(p.stem for p in d.glob("*.py") if p.name != "__init__.py") if d.is_dir() else []
        )
        names = ", ".join(f"`{m}.py`" for m in mods) if mods else "—"
        rows.append(f"| `{layer}/` | **{len(mods)}** | {names} |")
    rows += ["", f"{END}"]
    return "\n".join(rows)


def main(argv: list[str]) -> int:
    root = pathlib.Path(argv[1] if len(argv) > 1 else ".").resolve()
    path = root / PLAN
    if not path.exists():
        print(f"[plan-state] {PLAN} not found")
        return 1
    text = path.read_text()
    if BEGIN not in text or END not in text:
        print(f"[plan-state] markers missing from {PLAN}; the state block cannot be checked")
        return 1

    want = render(root)
    start, end = text.index(BEGIN), text.index(END) + len(END)
    have = text[start:end]
    if have == want:
        print("[plan-state] ok — the plan's state block matches the filesystem")
        return 0
    if "--write" in argv:
        path.write_text(text[:start] + want + text[end:])
        print("[plan-state] state block rewritten from the filesystem")
        return 0
    print("[plan-state] the plan's state block does not match src/quantamind/.")
    print("  A layer gained or lost a module and the plan still says otherwise.")
    print("  Run: uv run python scripts/guard/records/check_plan_state.py . --write")
    for line in want.split("\n"):
        if line.startswith("| `") and line not in have:
            print(f"    should read: {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
