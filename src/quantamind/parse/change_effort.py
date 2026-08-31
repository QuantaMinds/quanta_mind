"""How much of each changed file actually changed, and which functions inside it.

WHAT: `effort(diff, scope)` returns one `Effort` per path: lines added and removed, and the names
      of the functions the diff touched.
WHY:  **A LIST OF EIGHTY-TWO PATHS TELLS A REVIEWER NOTHING ABOUT WHERE TO SPEND THEIR TIME.** The
      scope block names every changed file so nothing is hidden, and the complaint that produced
      this module was that the honesty had become a wall: a developer still had to open all of
      them to find out which mattered. A file with four changed lines in one function and a file
      with four hundred across nine are different problems, and the difference is free to compute.

      **EVERY NUMBER HERE COMES FROM THE DIFF, WHICH IS WHY IT MAY BE PUBLISHED.**
      `docs/product/publishing-rules.md` never-publishes *what the ranking is built from* — a
      per-file prior-fix count is exactly that, and one was printed in this comment once. Lines
      added and removed are not ours: GitHub prints them on its own Files-changed tab, so a reader
      already has them and a competitor learns nothing. **The rule is the SOURCE of the number, not
      how useful it looks.** Anything derived from `rank/` stays out of the comment, however
      helpful it would be.

      **THE SIZE IS COUNTED PER FILE, NOT SUMMED FROM UNITS, AND A LIVE RUN IS WHY.** The first
      version added up `ChangedUnit.lines_added` — so a file git named no declaration for scored
      nothing, and **every brand-new file in the change showed no size at all**, silently, because
      a new file's first hunk header is empty and becomes an `Unresolved`. The largest files in a
      change are exactly the new ones. Totals come from the diff's own `+`/`-` lines here; units
      supply only the declarations.

      **A DECLARATION IS SHOWN ONLY WHEN IT LOOKS LIKE ONE.** git's funcname heuristic takes the
      nearest preceding line matching a pattern, which inside a module docstring is prose: a real
      run produced *"WHY: **A COMMENT CAN BE SCROLLED PAST; A REQUIRED CHECK CANNOT.**"* as the
      place to look. `DECLARATION` keeps `def`/`class`/`async def` and drops the rest. **Dropping
      is right and guessing is not** — an omitted location costs a reader nothing, and a wrong one
      sends them to the wrong place with our confidence attached.

      **NO PERCENTAGE IS COMPUTED, AND THAT IS DELIBERATE.** A percentage needs a denominator, and
      every honest candidate is wrong: of the file, it says a big file is easy; of the change, it
      says the largest file is 100% whatever its size. The raw line count is the thing a reviewer
      actually calibrates against, and it cannot be misread as a claim about difficulty we have
      not measured.
IMPORTS: parse.units, types.change. Nothing to its right.
CONSUMED BY: `render/blocks/scope_block.py`, via `serve/review_delivery.py`.
"""

from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass, field

from quantamind.parse.units import FILE_HEADER, units_in

# What git's funcname heuristic produced that is actually a place to look. Everything else it
# offers — a docstring line, an import, an assignment — is dropped rather than guessed at.
DECLARATION = re.compile(r"^(async\s+def|def|class)\s")


@dataclass(frozen=True, slots=True)
class Effort:
    """What changed inside one file. Counts first, names second."""

    added: int = 0
    removed: int = 0
    functions: tuple[str, ...] = field(default_factory=tuple)

    @property
    def lines(self) -> int:
        return self.added + self.removed

    def render(self, cap: int = 2) -> str:
        """`12 lines · def settle(job):`, or just the count when git named nothing.

        **THE DECLARATION IS PRINTED VERBATIM AND IS NOT DRESSED UP AS A NAME.** A first draft
        rendered `f"{name}()"` and produced `def beyond_the_ranking((),
        from __future__ import annotations()` — because `qualified_name` is the text git writes
        after the second `@@`, not an identifier. It is the same string GitHub shows on its own
        hunk headers, which is exactly why it is useful as "where to look" and exactly why it must
        be quoted rather than reformatted.

        **THE COUNT IS NEVER OMITTED AND THE NAMES SOMETIMES ARE.** A header without an identifier
        is common in a data file or a long method, and printing "0 functions" would report our
        parser's silence as a fact about the change.
        """
        size = f"{self.lines} line{'' if self.lines == 1 else 's'}"
        if not self.functions:
            return size
        shown = " · ".join(f"`{name.strip()}`" for name in self.functions[:cap])
        more = len(self.functions) - cap
        return f"{size} · {shown}" + (f" and {more} more" if more > 0 else "")


def effort(diff: str, scope: Collection[str]) -> dict[str, Effort]:
    """One `Effort` per path git reported a hunk for.

    **A PATH WITH NO ENTRY IS A REAL ANSWER AND THE CALLER MUST HANDLE IT.** A file can be in the
    change and absent from the parsed units — a pure rename, a mode change, a binary. Returning a
    zero-line `Effort` for those would print "0 lines" beside a file that certainly changed, which
    is a wrong statement rather than a missing one.
    """
    wanted = set(scope)
    added, removed = _totals(diff, wanted)
    names: dict[str, list[str]] = {}
    for unit in units_in(diff, scope).units:
        if not DECLARATION.match(unit.qualified_name.strip()):
            continue
        # git repeats a declaration when a function has several hunks. The reviewer wants the set.
        seen = names.setdefault(unit.site.path, [])
        if unit.qualified_name not in seen:
            seen.append(unit.qualified_name)
    return {
        path: Effort(added[path], removed.get(path, 0), tuple(names.get(path, ())))
        for path in sorted(added)
    }


def _totals(diff: str, wanted: set[str]) -> tuple[dict[str, int], dict[str, int]]:
    """Added and removed lines per path, counted from the diff itself.

    **`+++`/`---` ARE FILE HEADERS, NOT CONTENT**, and counting them would add one to every file.
    """
    added: dict[str, int] = {}
    removed: dict[str, int] = {}
    path = ""
    for line in diff.split("\n"):
        header = FILE_HEADER.match(line)
        if header:
            path = header.group(1).strip()
            if path in wanted:
                added.setdefault(path, 0)
            continue
        if not path or path not in wanted or line.startswith(("+++", "---")):
            continue
        if line.startswith("+"):
            added[path] = added.get(path, 0) + 1
        elif line.startswith("-"):
            removed[path] = removed.get(path, 0) + 1
    return added, removed
