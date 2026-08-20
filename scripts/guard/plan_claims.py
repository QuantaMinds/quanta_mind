"""Read the implementation plan into the claims it makes, so a rule can be run over them.

WHAT: `normalise()`, `exists()`, `referenced()`, `sentences()` and `steps()` -- turn a stage
      heading, a table cell or a numbered step into the module names it asserts something about,
      and say whether each is on disk.
WHY:  **Split from `check_stage_table.py` at the 200-line cap, on the seam between reading a
      document and judging it.** The rules are three short conditions; almost all the length was
      deciding what the author actually wrote, which is the part this repository keeps getting
      wrong in both directions.

      **THE PARSING UNIT IS THE WHOLE PROBLEM.** `check_documented_recipes.py` joined every
      backtick span on a line and read a command across the gap between two.
      `check_decided_vocabulary.py` scanned by line and split a negation across a wrapped one, then
      scanned by paragraph and merged a table's rows until a sabotage setting all four columns to
      the rejected value passed silently. Two guards, opposite errors, one cause: the unit they
      read was not the unit the author wrote in. Each function here names its unit and why.
IMPORTS: stdlib re and pathlib. No project imports.
CONSUMED BY: `scripts/guard/records/check_stage_table.py`.

      It lives beside `discovery.py` rather than in `records/` because that is where a guard's
      shared modules already live, and `mypy_path` names this directory. Putting it in `records/`
      made mypy read one file under two module paths.
"""

from __future__ import annotations

import re
from pathlib import Path

PACKAGE = Path("src/quantamind")
# `layer/module.py`, or a bare `layer/`. Backticked, because an unquoted "render" in a sentence is
# the English word and matching it would flag every goal statement in the document.
MODULE = re.compile(r"`([a-z_]+)/([a-z_]+)\.py`")
LAYER = re.compile(r"`([a-z_]+)/`")


def normalise(name: str) -> str:
    """Stage names, comparable across the table and the headings."""
    plain = re.sub(r"[*`]", "", name).strip().lower()
    return plain[4:] if plain.startswith("the ") else plain


def exists(root: Path, layer: str, module: str | None) -> bool:
    directory = root / PACKAGE / layer
    if module is None:
        return directory.is_dir() and any(p.name != "__init__.py" for p in directory.glob("*.py"))
    return (directory / f"{module}.py").is_file()


def referenced(root: Path, text: str) -> list[tuple[str, bool]]:
    """(name, exists) for every module and bare layer the text names."""
    found = [(f"{a}/{b}.py", exists(root, a, b)) for a, b in MODULE.findall(text)]
    found += [(f"{a}/", exists(root, a, None)) for a in LAYER.findall(text)]
    return found


def sentences(cell: str) -> list[str]:
    """**THE UNIT IS A SENTENCE, AND PICKING IT WRONG IS THIS REPOSITORY'S RECURRING GUARD BUG.**

    One evidence cell carried both polarities -- "`ingest/history.py` built. `ingest/diff.py` and
    `parse/` not begun" -- so a whole-cell scan sees an absence marker and condemns the module that
    is legitimately reported as built. `check_documented_recipes.py` joined too much and read a
    command across two backtick spans; `check_decided_vocabulary.py` joined too little and split a
    negation across a wrapped line. Splitting on sentence punctuation is the unit the author wrote
    in, which is what both of those got wrong in opposite directions.
    """
    return [part for part in re.split(r"(?<=[.;])\s+", cell) if part.strip()]


def steps(body: str) -> list[str]:
    """One numbered step per entry, continuation lines folded in.

    A step wraps over several lines and its `**DONE.**` marker sits on the first, so a line-based
    read would see the marker and the module name as unrelated.
    """
    steps: list[str] = []
    for line in body.splitlines():
        if re.match(r"^\d+\.\s", line):
            steps.append(line)
        elif steps and line.startswith("   "):
            steps[-1] += " " + line.strip()
        elif not line.strip():
            continue
    return steps
