"""What this change took away, and who outside this repository was using it.

WHAT: `crossing(breaks, found)` renders the API-break section: the public symbols this change
      removed or narrowed, and the declared repositories that import them.
WHY:  **D3b. THE ONE THING ON THE CATEGORY'S LIST WE DID NOT HAVE**, and the only claim in the
      comment that is about somebody else's repository — which is why every word of it is a
      parser's answer and none of it is a model's. → `docs/product/comment-golden-rules.md`

      **THE BREAKS RENDER WHETHER OR NOT A CONSUMER WAS READ.** "You removed `total`" is true and
      actionable on its own; waiting for a consumer check that will usually be unavailable would
      throw away the half that always works. This is the same shape as D6a: the deterministic part
      does not wait on the part that needs somebody else's permission.

      **AND AN UNREADABLE LINK IS NAMED, NOT OMITTED.** The App is installed on the repository
      under review and very often not on the one consuming it, so "nothing imports this" and "we
      could not open it" will diverge constantly. Printing only the first would be a clean bill of
      health for a check that never ran.

      **NO SEVERITY AND NO ADVICE.** Whether removing an export is acceptable depends on the
      release the team is cutting, which we cannot see. The section says what changed and who
      imports it; the reader decides whether that is a problem.
IMPORTS: parse.public_api, verify.consumers. Leftward, value objects only.
CONSUMED BY: `render/comment.py`.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.parse.public_api import Break
from quantamind.verify.consumers import Crossing

HEADING = "**This change narrows what other code can use**"
CONSUMED = "**Declared consumers that import it**"
UNREAD = "**Declared consumers not checked**"
MAX_BREAKS = 5


def crossing(breaks: Sequence[Break], found: Crossing) -> str:
    """The section, or an empty string when nothing public was taken away."""
    if not breaks:
        return ""

    lines = [HEADING, ""]
    lines += [f"- {item.render()}" for item in breaks[:MAX_BREAKS]]
    hidden = len(breaks) - MAX_BREAKS
    if hidden > 0:
        lines.append(f"- and {hidden} more public symbol(s)")

    if found.consumers:
        lines += ["", CONSUMED, ""]
        lines += [f"- {consumer.render()}" for consumer in found.consumers]
    if found.unread:
        lines += ["", UNREAD, ""]
        lines += [f"- {item.render()}" for item in found.unread]
    return "\n".join(lines)
