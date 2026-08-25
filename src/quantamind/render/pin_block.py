"""Render a pin mismatch as a comment block. A fact with its authority named, never a judgement.

WHAT: `block(mismatches)` returns the markdown for the pins whose version comment GitHub
      contradicts, or an empty string when there are none.
WHY:  **THIS IS THE ONLY FINDING IN THE PRODUCT THAT NO MODEL PRODUCED.** A parser read the pin, an
      API answered, and the disagreement is stated. It cannot be wrong the way a semantic claim can:
      two requests settle it, and the block names both what was claimed and what the authority
      reports so a reader can check it in a browser.

      **IT IS RENDERED SEPARATELY FROM THE RANKING AND SAYS SO.** The ranking is an ordering with no
      claim attached — the property that let the deterministic half of this product survive when the
      reviewing half did not. Folding a factual claim into that block would put the two on the same
      footing, and the first time the claim was wrong it would take the ordering's credibility with
      it.

      **AND IT FIRES RARELY.** 3 genuine mismatches in 1,244 real commented pins across 22
      repositories — 0.24%. A block that is absent on almost every change is the intended
      behaviour, not a failure to find anything.
IMPORTS: verify.pin_mismatch (its `Mismatch`). Left of serve.
CONSUMED BY: `serve/review_delivery.py`.
"""

from __future__ import annotations

from quantamind.verify.pin_mismatch import Mismatch


def block(mismatches: list[Mismatch]) -> str:
    """Markdown for the mismatched pins. Empty when there are none, which is the common case."""
    if not mismatches:
        return ""
    lines = [
        "",
        "---",
        "",
        "**Pinned action versions that disagree with the tag list** — checked against the GitHub "
        "API, not inferred:",
        "",
    ]
    for m in mismatches:
        actual = ", ".join(m.actual) if m.actual else "no tag"
        lines.append(
            f"- `{m.repo}` is pinned to `{m.sha[:8]}` and commented `# {m.commented}`, "
            f"but GitHub reports that commit as **{actual}**."
        )
    lines += [
        "",
        "_Two API calls settle each of these. They are facts about the tag list, not opinions "
        "about the code._",
    ]
    return "\n".join(lines)
