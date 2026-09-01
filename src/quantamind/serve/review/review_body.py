"""Assemble the comment body, or decide there is nothing worth posting.

WHAT: `body_for(...)` returns the markdown to post, or `None` when the review has nothing to say
      beyond the ranking. It renders the full comment and the fallback through the SAME arguments.
WHY:  **THE TWO RENDERERS MUST NEVER DRIFT APART, AND THEY DID.** Written inline as an expression,
      the "does this comment say anything" check omitted `blind` and silently discarded the "I
      could not review this" banner — a refusal became silence. `render/speaks.beyond_the_ranking`
      takes `comment()`'s own arguments so a section cannot be added to one without the other, and
      keeping both calls in one small function is what makes that visible.
      → `QuantaMinds/quanta_mind#91`, found by this product's own review of itself.

      **SPLIT OUT OF `serve/review_delivery.py` AT THE 200-LINE CAP, AND IT IS A REAL SEAM.**
      `deliver()` orchestrates: clone, rank, review, enforce, render, post. "Decide what the
      comment says" is one step with its own inputs and one output, and it was the largest block of
      `deliver()` that never touched the network or the store.
IMPORTS: render.{comment,speaks}, serve.change_facts, types.standards.{checked,judged}. Leftward
      and sideways from `serve/`.
CONSUMED BY: `serve/review_delivery.py`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from quantamind.render.comment import comment as rendered
from quantamind.render.speaks import beyond_the_ranking
from quantamind.types.standards.checked import Checked
from quantamind.types.standards.judged import Judged


def body_for(
    ranking: Any,
    *,
    summary: Any,
    findings: Sequence[Any],
    checks: Sequence[Checked],
    judged: Sequence[Judged],
    blind: str,
    facts: Any,
    inherited: Any,
) -> str | None:
    """The comment body, or `None` when nothing beyond the ranking is worth saying.

    **BOTH CALLS TAKE THE SAME ARGUMENTS ON PURPOSE.** See the module docstring: the last time they
    were allowed to differ, a refusal to review turned into an empty comment.
    """
    full = rendered(
        ranking,
        summary=summary,
        findings=findings,
        checks=checks,
        judged=judged,
        blind=blind,
        context=facts.intent,
        repeated=facts.repeated,
        effort=facts.sizes,
        links=facts.links,
        links_unreadable=facts.links_unreadable,
        breaks=facts.breaks,
        crossed=facts.crossing,
        inherited=inherited,
    )
    speaks = beyond_the_ranking(
        summary=summary,
        findings=findings,
        checks=checks,
        blind=blind,
        context=facts.intent,
        repeated=facts.repeated,
        breaks=facts.breaks,
    )
    return full if speaks else None
