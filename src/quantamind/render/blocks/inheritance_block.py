"""What this repository changed about the standards its organisation defined.

WHAT: `inheritance(record)` renders the D1e merge — rules dropped, tightened or refused — and
      nothing at all when the repository follows what it inherited.
WHY:  **"A STANDARD THAT CAN BE DISABLED INVISIBLY IS NOT A STANDARD."** That is the row's own
      sentence and this block is where it becomes true or false. `combine` can compute a perfect
      `Dropped` record and it changes nothing if the record never reaches a reader.

      **A DROP IS PRINTED EVEN THOUGH NOTHING FAILED**, which is unusual for this comment and is
      the point: every other section reports on the change under review, and this reports on what
      the change was NOT checked against. A reviewer approving a pull request in a repository that
      switched off the organisation's `no-eval` rule should not have to go looking for that.

      **AN UNREADABLE ORGANISATION FILE IS THE LOUDEST LINE HERE.** A drop is a decision somebody
      made; an unreadable file is enforcement that stopped without anyone deciding anything, and it
      means every inherited standard is currently unchecked. It renders first for that reason.

      **SILENT WHEN NOTHING CHANGED.** A repository following its organisation exactly is the
      common case, and a section saying "nothing to report" on every pull request is how a reader
      learns to skip the section that matters on the one where something did.
IMPORTS: ingest.standards.inherited for the record. Leftward only.
CONSUMED BY: `render/comment.py`.
"""

from __future__ import annotations

from quantamind.ingest.standards.inherited import Inheritance

HEADING = "**Organisation standards**"


def inheritance(record: Inheritance | None) -> str:
    """The inheritance section, or empty when there is nothing a reader must know."""
    if record is None:
        return ""
    if not record.org_read:
        # **NOT A FOOTNOTE.** Nothing inherited was checked on this change.
        return "\n".join(
            [
                "",
                HEADING,
                "",
                "Your organisation's rules file could not be read, so **none of the standards "
                "defined there were checked on this change**. The rules this repository declares "
                "for itself still ran.",
                "",
            ]
        )
    if not record.changed():
        return ""

    lines = ["", HEADING, ""]
    for gone in record.dropped:
        lines.append(f"- **Switched off here:** {gone.render()}")
    for refused in record.refused:
        lines.append(f"- **Not applied as written:** {refused.render()}")
    for raised in record.tightened:
        lines.append(f"- **Stricter here than required:** {raised.render()}")
    lines.append("")
    return "\n".join(lines)
