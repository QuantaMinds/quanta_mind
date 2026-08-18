"""Map a diff's hunks to the functions they touch, and emit a typed record for every one we cannot.

WHAT: `units_in()` returns `(units, unresolved)` for a unified diff. Every hunk produces exactly one
      of the two.
WHY:  **Conservation is the contract: `len(units) + len(unresolved) == hunks`.** A hunk that
      appears in neither list has vanished, and a coverage line computed over a list something
      silently fell out of is worse than no coverage line — it is a specific, checkable, false
      claim about what we read.

      **The pass is git's funcname hunk header, and that is deliberate.** Git already computes the
      enclosing declaration for every hunk — `@@ -266,17 +269,12 @@ def get_dumper(self, obj)` —
      and it costs nothing. A parser must answer anything a parser can, and this one already has.
      It resolved 50.8% of 453 real hunks in the research; the other half get an `Unresolved`.

      **The exact pass is not built and is not pretended.** It needs tree-sitter, which
      `pyproject.toml` does not depend on. Hunks the header cannot name are
      `Reason.UNPARSEABLE_SYNTAX`, not silently dropped and not guessed at from surrounding lines.

      **`scope` is what the caller intends to review, and hunks outside it are not parsed at all.**
      Without it, a scrapy pull request reported *"19 constructs could not be parsed"* naming
      `install.rst`, `commands.rst` and `pyproject.toml` — documentation and configuration we never
      intended to read, rendered to the customer as a parse FAILURE. It also dropped the resolution
      rate from 91% to 52% by counting hunks that were never in scope. **"We do not review this"
      and "we tried and could not" are different facts**, and only the second belongs in the
      unresolved list.

      **An unsupported language inside scope is `Reason.LANGUAGE_UNSUPPORTED` on the FILE**, one
      record per hunk because conservation demands every hunk be accounted for — the caller
      deduplicates for display.
IMPORTS: types (ChangedUnit, Language, Site, Unresolved), parse.languages. Nothing to its right.
CONSUMED BY: render.coverage_line, which names what could not be read.
"""

from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass

from quantamind.parse.languages import Depth, depth_of, language_of
from quantamind.types.change import ChangedUnit
from quantamind.types.verdict import Construct, Reason, Site, Unresolved

# `@@ -a,b +c,d @@ <declaration>` -- the declaration is what git's funcname driver found.
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)$")
FILE_HEADER = re.compile(r"^\+\+\+ b/(.*)$")
# A declaration git names but that carries no identifier -- a brace, a decorator line, a comment.
NAMED = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass(frozen=True, slots=True)
class Parsed:
    """What one diff yielded. Both lists together account for every hunk."""

    units: tuple[ChangedUnit, ...]
    unresolved: tuple[Unresolved, ...]
    hunks: int

    def conserved(self) -> bool:
        """Every hunk is in exactly one list. The caller asserts this; it is the contract."""
        return len(self.units) + len(self.unresolved) == self.hunks


def _declaration(header: str) -> str:
    """The identifier git named after the second `@@`, or '' when it named nothing usable."""
    text = header.strip()
    return text if text and NAMED.search(text) else ""


def units_in(diff: str, scope: Collection[str] | None = None) -> Parsed:
    """Every in-scope hunk of `diff`, resolved to a unit or recorded as unresolved.

    `scope` is the set of paths the caller intends to review — normally what `ingest.diff`
    returned. Hunks for other files are skipped entirely and do not count toward `hunks`: they
    were never going to be read, and calling them unresolved reports a failure we did not have.
    Passing `None` parses everything, which is the right default only when the caller has already
    narrowed the diff.

    The unit's `site` carries the hunk's first added line, and its `qualified_name` is the
    declaration git named. Nothing here guesses: a header without an identifier is unresolved.
    """
    units: list[ChangedUnit] = []
    unresolved: list[Unresolved] = []
    hunks = 0
    path = ""

    for line in diff.split("\n"):
        header = FILE_HEADER.match(line)
        if header:
            path = header.group(1).strip()
            continue
        match = HUNK.match(line)
        if not match or not path:
            continue
        if scope is not None and path not in scope:
            continue  # never in scope; not a parse failure

        hunks += 1
        start = int(match.group(1))
        language = language_of(path)
        site = Site(path=path, line=start)

        if depth_of(language) is Depth.NONE:
            # One record per FILE, not per hunk -- but every hunk must still be accounted for, so
            # the first hunk of the file carries it and the rest are attributed to the same fact.
            unresolved.append(
                Unresolved(site=site, reason=Reason.LANGUAGE_UNSUPPORTED, construct=Construct.FILE)
            )
            continue

        declaration = _declaration(match.group(2))
        if not declaration:
            unresolved.append(
                Unresolved(
                    site=site, reason=Reason.UNPARSEABLE_SYNTAX, construct=Construct.CALL_SITE
                )
            )
            continue

        units.append(ChangedUnit(site=site, qualified_name=declaration, language=language))

    return Parsed(units=tuple(units), unresolved=tuple(unresolved), hunks=hunks)
