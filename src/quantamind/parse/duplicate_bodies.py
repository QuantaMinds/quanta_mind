"""Which functions this change touched have a body that already exists somewhere else.

WHAT: `twins(clone, changed)` walks the repository's library Python at the working head, groups
      functions by `body_shape` digest, and returns the groups a changed file takes part in —
      with the counts behind them.
WHY:  **THE FLOOR AND THE FILTER WERE MEASURED BEFORE THIS SHIPPED, THE WAY D2a MEASURED ITS BASE
      RATE.** Run over two repositories:

      | | library files | functions | groups at 2 | at 3 | at 4 |
      |---|---|---|---|---|---|
      | this repository | 139 | 443 | 2 | **0** | 0 |
      | `pallets/flask` | 24 | 367 | 7 | **5** | 2 |

      **All five of flask's groups at three statements were read, and all five are real.** Three
      are the same body in `app.py` and `blueprints.py` — `get_send_file_max_age`,
      `send_static_file`, `open_resource` — which flask later hoisted into a shared `Scaffold`
      base class, so the finding is confirmed out-of-sample by the maintainers doing the refactor
      it points at. Two are `templating.py`'s `render_template`/`stream_template` pair.

      **AT TWO STATEMENTS IT REPORTS `__init__` PAIRS; AT FOUR IT LOSES THREE OF THE FIVE.**
      Three is where every group was inspectable and every one was a genuine repeat.

      **THE LIBRARY/TEST SPLIT DOES MORE WORK THAN THE FLOOR DOES, AND THAT WAS THE SURPRISE.**
      Unfiltered, flask has 12 groups at three statements and 7 of them are test route handlers —
      `index`, `after_request`, `generate` — which are conventional, not copied, and burying five
      real findings under seven conventional ones is how a section stops being read.
      `suite_reach.is_library` already drew that line for a different question.

      **THIS KEEPS NOTHING.** No table, no migration, no watermark: the tree is parsed at the
      reviewed commit and thrown away. `D2b` is `ON HOLD, recommend DROP` because storing a
      whole-repository graph cost exactly those three things and then gave the same top three as
      alphabetical on 99.2% of changes. Paying that price again before this signal has shown its
      worth would be repeating the bet rather than learning from it.
IMPORTS: parse.{body_shape,suite_reach}; stdlib. Nothing to its right.
CONSUMED BY: `render/relations/duplicate_block.py`, via `serve/review_delivery.py`.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from quantamind.parse.body_shape import Shape, shapes_in
from quantamind.parse.python_names import UnparseableSource
from quantamind.parse.suite_reach import is_library

MIN_STATEMENTS = 3
"""Statements a body needs before a repeat of it is worth reporting. **Measured, not chosen** —
see the table in the module docstring."""

FILE_CAP = 5_000
"""Library files parsed before the walk stops. A monorepo must not turn one review into a minute
of parsing, and a walk that stopped silently would report fewer duplicates as none."""


@dataclass(frozen=True, slots=True)
class Site:
    """One place a body appears."""

    path: str
    shape: Shape

    def render(self) -> str:
        return f"`{self.path}:{self.shape.line}` {self.shape.name}()"


@dataclass(frozen=True, slots=True)
class Repeat:
    """One body, and every place it appears. Always two or more."""

    statements: int
    sites: tuple[Site, ...]

    def changed(self, paths: frozenset[str]) -> tuple[Site, ...]:
        return tuple(site for site in self.sites if site.path in paths)

    def elsewhere(self, paths: frozenset[str]) -> tuple[Site, ...]:
        return tuple(site for site in self.sites if site.path not in paths)


@dataclass(frozen=True, slots=True)
class Duplicates:
    """What was found, and what was read to find it. **The denominator ships with the answer.**"""

    repeats: tuple[Repeat, ...]
    files_read: int
    files_unparsed: int
    touched: frozenset[str]
    """The changed paths this was filtered against. **CARRIED, NOT RE-DERIVED BY THE RENDERER.**

    `render/blocks/duplicate_block.py` needs to know which side of a repeat is the author's, and
    it was passed `ranking.units` — a SUBSET of what `twins()` filtered on, since the ranker drops
    what it cannot read. Two populations for one question, which is `docs/engineering/
    CORRECTIONS.md` entry 7 exactly. Reported by this product against
    `QuantaMinds/quanta_mind#92`; it produced no wrong output yet, and the fix is to have one set.
    """

    capped: bool
    """True when `FILE_CAP` stopped the walk, so "no duplicates" means "none in what we read"."""

    def limits(self) -> str:
        """What this answer does not cover, or an empty string when it covers the tree."""
        if self.capped:
            return f"only the first {self.files_read} library file(s) were read"
        if self.files_unparsed:
            return f"{self.files_unparsed} file(s) could not be parsed and were not searched"
        return ""


def twins(clone: Path, changed: list[str]) -> Duplicates:
    """Repeated bodies that a changed file takes part in.

    **A GROUP IS ONLY REPORTED WHEN THE CHANGE IS IN IT.** The reviewer is answering a question
    about this pull request; the repository's other duplicates are true, not asked about, and
    would make the section longer on every review while never being acted on.

    **THE WALK IS OVER THE WORKING TREE, WHICH IS THE COMMIT UNDER REVIEW.** `serve/working_clone`
    has already checked the head out, so this reads what the change leaves behind rather than
    what was there before it — a duplicate the change itself CREATED is the one worth naming.
    """
    touched = frozenset(path for path in changed if is_library(path))
    by_digest: dict[str, list[Site]] = defaultdict(list)
    read = unparsed = 0
    capped = False

    for path in sorted(clone.rglob("*.py")):
        relative = path.relative_to(clone).as_posix()
        if not is_library(relative):
            continue
        if read >= FILE_CAP:
            capped = True
            break
        read += 1
        try:
            found = shapes_in(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, UnparseableSource):
            # **THE ONLY THING COUNTED HERE IS A FILE WE COULD NOT READ.** An earlier version also
            # counted every module that defines no functions, and reported 51 of this repository's
            # 390 library files as a coverage gap when all 390 had been read.
            unparsed += 1
            continue
        for shape in found:
            if shape.statements >= MIN_STATEMENTS:
                by_digest[shape.digest].append(Site(relative, shape))

    repeats = tuple(
        Repeat(sites[0].shape.statements, tuple(sites))
        for sites in (
            sorted(group, key=lambda s: (s.path, s.shape.line)) for group in by_digest.values()
        )
        if len(sites) > 1 and any(site.path in touched for site in sites)
    )
    return Duplicates(
        repeats=tuple(sorted(repeats, key=lambda r: (-r.statements, r.sites[0].path))),
        files_read=read,
        files_unparsed=unparsed,
        touched=touched,
        capped=capped,
    )
