"""Which declared repository imports the symbol this change just broke.

WHAT: `affected(links, breaks, clone_for)` pairs each broken export with the linked repositories
      that import it, and records a typed refusal for every link that could not be read.
WHY:  **D3b, AND IT IS THE ONE THING ON THE CATEGORY'S LIST WE DID NOT HAVE.** Qodo advertises
      *modified response formats consumed by other services* and *broken API contracts read against
      registered consumer repositories*; "registered" is their word for D3a's declaration and this
      is the check on top of it.

      **A LINK WE COULD NOT READ IS THE COMMON CASE AND IT IS REPORTED, NOT SKIPPED.** The App is
      installed on the repository under review; it is very often not installed on the one that
      consumes it. **"No consumer imports this" and "we could not open the consumer" are the two
      answers this whole product exists to keep apart**, and here the second will be the frequent
      one for a long time. Every refusal names its repository.

      **THE MATCH IS AN IMPORT, NOT A MENTION.** `parse/imports.py` reads the import statements;
      grepping for the symbol's text would hit a comment, a docstring, a variable of the same name,
      and a string in a test fixture. A false "your change breaks billing" is the most expensive
      sentence this product could print, because it is about somebody else's repository and the
      reader cannot check it without leaving the pull request.

      **NOTHING IS CLONED SPECULATIVELY.** With no breaking change there is no question to ask, so
      `affected` returns immediately and no linked repository is fetched at all. A review of an
      additive change costs nothing here.
IMPORTS: ingest.standards.links_file, parse.{imports,public_api,suite_reach}. Leftward only; the
      clone itself is injected, because `verify/` may not reach into `serve/`.
CONSUMED BY: `serve/change_facts.py`.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from quantamind.ingest.standards.links_file import Link
from quantamind.parse.public_api import Break
from quantamind.parse.suite_reach import is_library

CloneFor = Callable[[str], Path | None]
"""Opens a linked repository, or returns None when it cannot. **None is the expected answer.**"""

FILE_CAP = 4_000
"""Files read in one linked repository. A consumer we cannot finish reading is reported as such."""


@dataclass(frozen=True, slots=True)
class Consumer:
    """One linked repository that imports a symbol this change broke."""

    repo: str
    symbol: str
    where: tuple[str, ...]

    def render(self) -> str:
        shown = ", ".join(f"`{path}`" for path in self.where[:3])
        more = len(self.where) - 3
        return f"`{self.repo}` imports `{self.symbol}` — {shown}" + (
            f" and {more} more file(s)" if more > 0 else ""
        )


@dataclass(frozen=True, slots=True)
class Unread:
    """One declared link we could not check, and the repository it names."""

    repo: str

    def render(self) -> str:
        return f"`{self.repo}` — could not be opened, so nothing in it was checked"


@dataclass(frozen=True, slots=True)
class Crossing:
    """What a breaking change does to the repositories the customer declared."""

    consumers: tuple[Consumer, ...] = ()
    unread: tuple[Unread, ...] = ()

    def asked(self) -> bool:
        """Whether any linked repository was looked at. False when nothing broke."""
        return bool(self.consumers or self.unread)


def _imported_names(source: str) -> set[str]:
    """Every name this module imports, however it spells the import.

    Only `from x import NAME` and `import x` bind a name a caller can use; an attribute access on
    a module (`mod.NAME`) is not an import and is deliberately out of scope — catching it needs
    resolution this layer does not do, and guessing would produce the false positive above.
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            found.update(alias.asname or alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            found.update((alias.asname or alias.name).split(".")[-1] for alias in node.names)
    return found


def _scan(clone: Path, symbols: frozenset[str]) -> dict[str, list[str]]:
    """Which of `symbols` this repository imports, and the files that import each."""
    hits: dict[str, list[str]] = {}
    read = 0
    for path in sorted(clone.rglob("*.py")):
        relative = path.relative_to(clone).as_posix()
        if not is_library(relative) or read >= FILE_CAP:
            continue
        read += 1
        try:
            names = _imported_names(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        for symbol in symbols & names:
            hits.setdefault(symbol, []).append(relative)
    return hits


def affected(links: Sequence[Link], breaks: Sequence[Break], clone_for: CloneFor) -> Crossing:
    """The declared repositories that import what this change broke.

    **NOTHING IS OPENED WHEN NOTHING BROKE.** The first line is the cost control: an additive
    change asks no question, so no linked repository is fetched and the block renders nothing.
    """
    if not breaks or not links:
        return Crossing()

    symbols = frozenset(item.name for item in breaks)
    consumers: list[Consumer] = []
    unread: list[Unread] = []
    for link in links:
        clone = clone_for(link.repo)
        if clone is None:
            unread.append(Unread(link.repo))
            continue
        for symbol, where in sorted(_scan(clone, symbols).items()):
            consumers.append(Consumer(link.repo, symbol, tuple(where)))
    return Crossing(tuple(consumers), tuple(unread))
