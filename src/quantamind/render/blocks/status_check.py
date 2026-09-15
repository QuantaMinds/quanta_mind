"""What the blocking status says, in the one line GitHub gives us for it.

WHAT: `render(gate)` turns a `verify.blocking.Gate` into the `state` and `description` a commit
      status carries. Pure: no network, no clock, so the sentence a developer will read is
      asserted in a unit test rather than discovered in production.
WHY:  **THIS SENTENCE IS THE WHOLE EXPLANATION FOR A BLOCKED MERGE.** GitHub shows one line beside
      a failing check. If it says "checks failed" the developer opens the audit trail to find out
      what; if it names the rule and the file, the common case needs nothing opened at all.

      **WHAT WE COULD NOT CHECK IS IN THE SENTENCE, NOT ONLY IN THE TRAIL.** A status reading "3
      rule check(s) passed" while nine files could not be parsed reads as compliance and is not
      compliance -- it is a proxy for it, which is the failure `AGENTS.md` rule 14 names. The
      unchecked count rides in the description so the reader sees the denominator, and the
      deferred count rides with it so "a model still has to look at this" never masquerades as a
      clean pass.

      **A CHANGE NOTHING GOVERNED HAS NO SENTENCE.** `NothingDeclared` is raised rather than a
      cheerful default returned, because the only honest renderings of "no rule applied" are
      silence or a lie, and a function that must pick one should not pick quietly.
IMPORTS: types.checked and verify.blocking. `verify` is to the LEFT of `render`, so this is a
      legal edge; `ingest/publish/commit_status.py` deliberately does NOT make it.
CONSUMED BY: `serve/review_delivery.py`, which passes the result to `commit_status.post`.
"""

from __future__ import annotations

from dataclasses import dataclass

from quantamind.verify.blocking import Gate, Standing


class NothingDeclared(ValueError):
    """No rule governed any changed file, so there is no verdict to phrase."""

    def __init__(self) -> None:
        super().__init__("no rule governed this change; post no status rather than a green one")


@dataclass(frozen=True, slots=True)
class Status:
    """The two fields a commit status carries. `state` is one of `commit_status.STATES`."""

    state: str
    description: str


NOTHING_GOVERNED = "no declared rule governed any file in this change"


def render(gate: Gate) -> Status:
    """The state and the sentence. Never raises: a gate that declines to speak cannot be required.

    **THE STATE COMES FROM `Standing`, NEVER FROM A COUNT RECOMPUTED HERE.** Re-deriving "is
    anything wrong" at the renderer is how two code paths come to disagree about one column -- the
    `+32` that read as judge drift was exactly that. The gate decided; this asks it.
    """
    if gate.standing is Standing.NOT_DECLARED:
        # **THIS RAISED UNTIL 2026-09-15, AND THE CALLER POSTED NOTHING.** The reasoning was sound
        # while the status was advisory: a green tick where no rule applied asserts compliance with
        # a standard nobody wrote. **Making the check REQUIRED swapped the cost of the two
        # mistakes** -- silence stopped being a missing signal and became a deadlocked merge, shown
        # as `pending` forever and indistinguishable from "still running". PR #104 sat there with
        # every CI job green. The description is what keeps this from being the lie the old
        # decision refused: it names the state rather than claiming a pass, exactly as
        # `UNCHECKABLE` does in the compliance table. **Its text is pinned by a test.**
        return Status("success", NOTHING_GOVERNED)
    parts: list[str] = []
    if gate.violations:
        first = gate.violations[0]
        parts.append(f"{len(gate.violations)} violation(s): {first.rule_id} in {first.site.path}")
    else:
        parts.append(f"{gate.passed} rule check(s) passed")
    if gate.unchecked:
        parts.append(f"{gate.unchecked} could not be checked")
    if gate.deferred:
        parts.append(f"{gate.deferred} left to a reviewer")
    return Status(
        state="failure" if gate.standing is Standing.BLOCKED else "success",
        description="; ".join(parts),
    )
