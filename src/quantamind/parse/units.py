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
from quantamind.types.change import ChangedUnit, Language
from quantamind.types.verdict import Construct, Reason, Site, Unresolved

# `@@ -a,b +c,d @@ <declaration>` -- the declaration is what git's funcname driver found.
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)$")
FILE_HEADER = re.compile(r"^\+\+\+ b/(.*)$")
# A declaration git names but that carries no identifier -- a brace, a decorator line, a comment.
NAMED = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class MalformedDiff(ValueError):
    """The diff carried hunks but no file they belong to.

    Raised rather than returning zero hunks, because zero hunks reads as "a change containing
    nothing": conservation is satisfied vacuously, the coverage line is computed over an empty
    list, and the review reports that it looked and found nothing to look at. A patch we cannot
    parse and a patch with nothing in it must not be the same value.
    """


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

    **`lines_added` AND `lines_removed` ARE FILLED HERE, AND FOR A LONG TIME THEY WERE NOT.**
    `ChangedUnit` has carried both fields and a `churn` property since it was written, and this
    function — its only producer — left all three at zero. Nothing read them, so nothing failed;
    the first consumer to arrive, `parse/change_effort.py`, rendered "0 lines" beside files that
    plainly had changed. **A field that looks meaningful and is never populated is the same defect
    as a check that cannot fail**, and this codebase has found two dead constants the same way.
    """
    units: list[ChangedUnit] = []
    unresolved: list[Unresolved] = []
    hunks = 0
    path = ""
    saw_hunk_marker = False
    # The unit whose body we are currently counting. A hunk's `+`/`-` lines arrive AFTER its
    # header, so the unit cannot be built until the next header or the end of the diff.
    pending: tuple[Site, str, Language] | None = None
    added = removed = 0

    def _flush() -> None:
        nonlocal pending, added, removed
        if pending is not None:
            site, declaration, language = pending
            units.append(ChangedUnit(site, declaration, language, added, removed))
        pending = None
        added = removed = 0

    for line in diff.split("\n"):
        header = FILE_HEADER.match(line)
        if header:
            _flush()
            path = header.group(1).strip()
            continue
        match = HUNK.match(line)
        if not match:
            # **ONLY COUNTED WHILE A UNIT IS OPEN.** Body lines of a hunk that became `Unresolved`
            # belong to no unit, and attributing them to the previous one would inflate a file's
            # size with a function we could not identify.
            if pending is not None and line[:1] in ("+", "-"):
                if line.startswith("+"):
                    added += 1
                else:
                    removed += 1
            continue
        _flush()
        saw_hunk_marker = True
        if not path:
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

        pending = (site, declaration, language)

    _flush()
    if saw_hunk_marker and hunks == 0 and scope is None:
        raise MalformedDiff(
            "the diff contains hunk headers but no `+++ b/<path>` line naming the file they "
            "belong to. Returning zero hunks would report this as a change containing nothing, "
            "and conservation would hold vacuously over an empty list"
        )
    return Parsed(units=tuple(units), unresolved=tuple(unresolved), hunks=hunks)
