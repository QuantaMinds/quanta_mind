"""The shape of a change, written out as facts a reviewer can read before the diff.

WHAT: `sentence(shape)` turns an `ingest.change_shape.Shape` into plain prose — how big this
      change is against the repository's own median, how many other people have been in these
      files, how often they change, and when it landed.
WHY:  **THIS FILE WAS NAMED BY `ingest/change_shape.py` AND NEVER WRITTEN.** That module's
      docstring said `CONSUMED BY: render/blocks/shape_line.py` while nothing in the tree
      imported it, so a fully built measurement sat dead. The docstring was the only evidence it
      was meant to be used, and a promised consumer that does not exist is the same silence this
      product refuses everywhere else.

      **EVERY LINE IS COUNTED, NONE IS JUDGED.** "6 files where your median is 2" is settled by
      two git commands; "this change is risky" is not. The prose says the first and never the
      second, and the block handed to a model says so explicitly — an unusual shape is a reason
      to read carefully, never a defect to report.
IMPORTS: ingest.change_shape, for the `Shape` it renders. Leftward, so allowed.
CONSUMED BY: `serve/deep_review.py`, which puts it in front of the model's diff.
"""

from __future__ import annotations

from quantamind.ingest.change_shape import Shape

# Handed to the model ahead of the diff. It names the facts as facts, because a model shown
# "23 files against a median of 2" and no instruction will report the size itself as the defect
# -- and the prompt already forbids that class of finding.
PREAMBLE = (
    "Context about this change, counted from this repository's own history. Every line is a\n"
    "fact git settles, not a judgement about the code. A change being unusually large or\n"
    "touching busy files is a reason to read it carefully. It is NOT a defect, and you must\n"
    "not report the shape of the change as a finding."
)


def sentence(shape: Shape) -> str:
    """The change's shape as prose. Empty string when there is nothing measured to say."""
    parts: list[str] = []
    if shape.files:
        size = f"- Touches {shape.files} file(s) and {shape.lines} line(s)."
        if shape.median_files and shape.median_lines:
            size += (
                f" This repository's median change is {shape.median_files} file(s)"
                f" and {shape.median_lines} line(s)."
            )
        parts.append(size)
    # **THE WINDOW ENDS AT THE CHANGE, NOT AT NOW**, which is what `change_shape` was fixed to do.
    # Saying "in the 30 days before it" rather than "recently" is what makes that legible to a
    # reader who would otherwise assume the window ends today.
    parts.append(
        f"- In the 30 days before it, these files changed {shape.churn} time(s),"
        f" and {shape.hands} other person/people touched them."
    )
    if shape.when:
        parts.append(f"- It landed on a {shape.when}.")
    for odd in shape.unusual:
        parts.append(f"- Outside this repository's normal range: {odd}.")
    return "\n".join(parts)


def block(shape: Shape) -> str:
    """`sentence` with the preamble, ready to sit in front of a diff. Empty when there is none."""
    body = sentence(shape)
    return f"{PREAMBLE}\n\n{body}\n\n" if body else ""
