"""What each writer needs GitHub to allow, and whether this installation allows it.

WHAT: `NEEDED` names one permission per write surface. `gaps(granted)` returns a `Gap` for each one
      the installation does not hold at the level required, and `sentence(gaps)` phrases them for
      an operator who has to go and fix it.
WHY:  **D1f SHIPPED AGAINST AN APP THAT COULD NOT POST A STATUS, AND EVERY TEST PASSED.** The first
      real call returned `403 Resource not accessible by integration` -- the installation held
      `contents:read`, `metadata:read` and `pull_requests:write`, and nothing else. Unit tests
      replace the writer with a spy that returns True, so no test could have found it, and no
      amount of test-writing would have: a permission that was never granted is not a code path.

      **THE GAP IS ASKED FOR, NOT INFERRED FROM A FAILURE.** Waiting for a 403 means learning about
      it on a customer's pull request, once, in a log line nobody reads -- and then never again,
      because the gate simply stays quiet. A product that claims to block merges while publishing
      nothing is the worst shape available: the claim survives, the behaviour does not.

      **EVERY WRITER DECLARES ITS OWN NEED HERE RATHER THAN IN PROSE.** A fifth writer added
      without a line in `NEEDED` is invisible to this check, which is the one thing this module
      cannot detect about itself -- said plainly because it is the next hole.
IMPORTS: stdlib only. Nothing from this project, so any layer may ask it.
CONSUMED BY: `serve/onboarding.py`, at install time.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

NEEDED: dict[str, tuple[str, str]] = {
    "pull_requests": ("write", "the review comment and its inline findings"),
    "contents": ("read", "reading the changed files at the head commit"),
    "metadata": ("read", "resolving the repository at all"),
    "statuses": ("write", "the blocking status check (D1f)"),
}
"""permission -> (level required, what stops working without it)."""

RANK = {"none": 0, "read": 1, "write": 2, "admin": 3}
"""**`write` IS NOT SATISFIED BY `read`, AND AN UNKNOWN LEVEL IS NOT SATISFIED BY ANYTHING.** An
unrecognised level ranks 0 rather than passing, because a permission model we do not understand is
not one we may assume is sufficient."""


@dataclass(frozen=True, slots=True)
class Gap:
    """One permission the installation does not hold at the level a writer requires."""

    permission: str
    required: str
    held: str
    """`"none"` when the installation does not mention it at all."""

    breaks: str

    def sentence(self) -> str:
        return (
            f"`{self.permission}: {self.required}` (holding {self.held}) — without it, "
            f"{self.breaks} does not work"
        )


def gaps(granted: Mapping[str, str]) -> tuple[Gap, ...]:
    """Every declared need this installation does not meet, in `NEEDED` order.

    **AN EMPTY RESULT MUST MEAN "ASKED AND SATISFIED", NEVER "DID NOT ASK".** The caller reads an
    empty tuple as permission to promise every surface works, so `granted` arriving empty produces
    a gap for everything rather than a clean bill.
    """
    found: list[Gap] = []
    for permission, (required, breaks) in NEEDED.items():
        held = granted.get(permission, "none")
        if RANK.get(held, 0) < RANK[required]:
            found.append(Gap(permission, required, held, breaks))
    return tuple(found)


def sentence(found: tuple[Gap, ...]) -> str:
    """One operator-facing line naming what to grant. Empty string when nothing is missing."""
    if not found:
        return ""
    each = "; ".join(gap.sentence() for gap in found)
    return (
        f"the GitHub App is missing {len(found)} permission(s): {each}. "
        "Grant them in the App's settings, then each installation must ACCEPT the update — "
        "GitHub does not apply new permissions to existing installations on its own."
    )
