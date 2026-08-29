"""Where a rater's deciding line sits in the diff it was taken from.

WHAT: `locate(line, diff)` returns `Placed(direction, reason)` — `ADDED`, `REMOVED`, or neither
      with the reason it could not be placed. Never a bare empty answer.
WHY:  **THE FIRST VERSION SKIPPED WHAT IT COULD NOT EVALUATE**, which is the defect class this
      whole instrument was built after. A cited line it failed to locate produced an empty
      direction, and the caller's `if truth and said != truth` then passed over the item in
      silence — so a sheet citing diff headers sailed through the check that exists to catch
      exactly that, and a different gate fired instead. Traced from a real test that "passed".

      Three rules, each of which was a way through:

      1. **A HEADER IS NOT CODE.** `+++ b/path`, `--- a/path`, `@@ ... @@`, `diff --git` and
         `index ...` all appear in the diff text, so a substring check accepts them as deciding
         lines. None of them is a line a claim can be about.
      2. **STRIP ONE MARKER, NOT ALL OF THEM.** `"+++ b/x".lstrip("+")` yields `"b/x"`, matching
         nothing and looking like an unlocatable line rather than a rejected header.
      3. **AMBIGUOUS IS ITS OWN ANSWER.** A line appearing as both added and removed — common
         when a block moves — cannot settle a direction, and saying so is not the same as
         finding nothing.
IMPORTS: stdlib only.
CONSUMED BY: `findings/scoring.py`; tests/findings/test_deciding_line.py.
"""

from __future__ import annotations

from dataclasses import dataclass

HEADERS = ("+++", "---", "@@", "diff --git", "index ")
ADDED = "ADDED"
REMOVED = "REMOVED"


@dataclass(frozen=True, slots=True)
class Placed:
    """Where the line sits, or why it could not be placed. `direction` empty means not placed."""

    direction: str
    reason: str

    @property
    def placed(self) -> bool:
        return bool(self.direction)


def _body(line: str) -> str:
    """The line without exactly one leading marker, and without surrounding whitespace."""
    stripped = line.strip().strip("`")
    if stripped[:1] in {"+", "-"}:
        return stripped[1:].strip()
    return stripped


def is_header(line: str) -> bool:
    """Whether this is diff furniture rather than a line of code."""
    return line.strip().strip("`").startswith(HEADERS)


def locate(line: str, diff: str) -> Placed:
    """Place `line` in `diff` as added or removed, or say why it cannot be placed."""
    # **BACKTICKS COME OFF BEFORE THE BLANK TEST, NOT AFTER.** A cite of "`  `" is blank, but
    # backticks are not whitespace, so testing `line.strip()` first let it through to be reported
    # as a marker instead. Garbage that reaches a later rule wearing the wrong label is how a
    # rule passes on something it never evaluated.
    if not line.strip().strip("`").strip():
        return Placed("", "no line given")
    if is_header(line):
        return Placed("", "that is a diff header, not a line of code")

    want = _body(line)
    if not want:
        return Placed("", "the line is only a marker")
    added = any(
        r.startswith("+") and not r.startswith("+++") and r[1:].strip() == want
        for r in diff.splitlines()
    )
    removed = any(
        r.startswith("-") and not r.startswith("---") and r[1:].strip() == want
        for r in diff.splitlines()
    )
    if added and removed:
        return Placed("", "appears as both added and removed, so it settles nothing")
    if added:
        return Placed(ADDED, "")
    if removed:
        return Placed(REMOVED, "")
    context = any(r.startswith(" ") and r[1:].strip() == want for r in diff.splitlines())
    if context:
        return Placed("", "present only as unchanged context, so this change did not touch it")
    return Placed("", "not found in the diff at all")
