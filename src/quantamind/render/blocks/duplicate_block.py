"""The same body, found in more than one place, printed as a fact and not as advice.

WHAT: `duplicates(found)` renders `parse.duplicate_bodies.Duplicates` as one comment section.
WHY:  **D2c. "THE SAME LOGIC IS WRITTEN IN TWO PLACES, AND A FIX TO ONE LEAVES THE OTHER WRONG."**
      A parser answers that exactly, so a model must not — and unlike everything `infer/` produces,
      this claim can be re-run on the same commit and shown to give the same answer.

      **IT SAYS WHERE, NOT WHAT TO DO.** "These two bodies are identical" is a measurement. "Extract
      a helper" is a design opinion about somebody's codebase, and the two deliberate duplicates in
      the measurement run — `pallets/flask`'s `render_template`/`stream_template` pair — are exactly
      the case where that advice would be wrong and confident. A reader who wants a helper does not
      need us to suggest one; a reader who chose the duplication should not be argued with by a
      comment.

      **THE CHANGED SIDE IS NAMED FIRST AND SEPARATELY.** A reviewer is holding one pull request:
      what they act on is "this function you just touched", and the other place is context. Printing
      a flat list of sites makes them find their own file in it.

      **WHAT WAS READ IS PRINTED WHEN IT IS NOT THE WHOLE TREE.** `Duplicates.limits()` returns the
      cap or the unparsed count, and the section states it — "no duplicates" and "no duplicates in
      the 5,000 files we got through" are different claims, and this product does not let those
      print the same.
IMPORTS: parse.duplicate_bodies. Leftward, value objects only.
CONSUMED BY: `render/comment.py`.
"""

from __future__ import annotations

from quantamind.parse.duplicate_bodies import Duplicates

HEADING = "**This code already exists somewhere else**"
CAVEAT = (
    "_Matched on structure with names normalised, so a renamed copy still counts and a changed "
    "literal does not. Whether the repeat is worth removing is your call._"
)
MAX_SHOWN = 5
"""Repeats printed before the rest become a count. The same reasoning as every other cap here:
a section nobody reads to the bottom hides its own last line."""


def duplicates(found: Duplicates, changed: list[str]) -> str:
    """The section, or an empty string when nothing repeated.

    **EMPTY IS THE COMMON ANSWER AND IT PRINTS NOTHING.** Measured over this repository: 139
    library files, 443 functions, **zero** repeated bodies at the floor. A section that announced
    "no duplicates found" on every clean change would be noise on the overwhelming majority of
    them, and the coverage line already states what was read.
    """
    if not found.repeats:
        return ""

    touched = frozenset(changed)
    lines = [HEADING, ""]
    for repeat in found.repeats[:MAX_SHOWN]:
        here = repeat.changed(touched)
        there = repeat.elsewhere(touched)
        # Both halves can be non-empty on either side: a change that touches two files holding the
        # same body has no "elsewhere", and that is still worth saying.
        subject = ", ".join(site.render() for site in here) or "this change"
        others = ", ".join(site.render() for site in there)
        tail = f" — also at {others}" if others else " — and in each other"
        lines.append(f"- {subject}{tail} ({repeat.statements} statements, identical)")

    hidden = len(found.repeats) - MAX_SHOWN
    if hidden > 0:
        lines.append(f"- and {hidden} more repeated bod{'y' if hidden == 1 else 'ies'}")

    limit = found.limits()
    lines += ["", CAVEAT if not limit else f"{CAVEAT[:-1]} {limit}._"]
    return "\n".join(lines)
