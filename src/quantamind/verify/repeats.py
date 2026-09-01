"""Find the findings that say the same thing twice, without deciding to drop them.

WHAT: `repeats(findings)` returns the indices that repeat one already kept, newest-last order
      preserved. It REPORTS; the caller decides, and nothing in the pipeline calls it yet.
WHY:  **WE EMIT 194 COMMENTS COVERING 81 GOLDEN DEFECTS WHERE QODO EMITS 152 COVERING 98.** The
      extra output is the same defect said again — 17.3% redundancy against Qodo's 1.0%, measured
      in `docs/findings/reviewer/why-the-correct-rate-is-low.md`. That is the one lever here that
      is model-free: every mechanism tried against the correctness rate has been a filter on
      generation, and five moved nothing, but redundancy is an emission property.

      **IT RETURNS INDICES RATHER THAN A SHORTER LIST, AND THAT IS THE POINT.** A function that
      silently returned fewer findings would make "we dropped a repeat" and "we lost a finding"
      the same value on the wire, which is the collapse this project exists to avoid. The caller
      can count what it discarded and say so.

      **NOTHING CALLS THIS.** `docs/plans/preregistrations/reviewer/dedup-preregistration.md`
      registers two bars and only the first can be paid for without model calls. Wiring it into
      `render/` before the coverage bar is met would be removing output and hoping nothing was
      lost, which is the reasoning this project rejects in other people's evidence.

      **SAME FILE IS REQUIRED, NOT INFERRED.** Two findings about different files are different
      findings however alike their prose, and a rule that crossed files would collapse a genuine
      pair on the strength of shared vocabulary.
IMPORTS: stdlib only, plus `types.finding`. Nothing to its right.
CONSUMED BY: nothing yet — by design. See the pre-registration.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from difflib import SequenceMatcher

from quantamind.types.finding import Finding

SIMILAR_AT = 0.86
"""Similarity at or above which two claims about one file are the same claim.

Chosen before any outcome was read, and the pre-registration's first bar is what tests it: the
rule must remove at most 3.0% of `qodo-extended-v2`'s comments, whose redundancy was independently
measured at 1.0% by a different method. A threshold that fires more than that is detecting
something other than repetition.
"""

_NOISE = re.compile(r"[^a-z0-9 ]+")


def _plain(text: str) -> str:
    """Lowercased, punctuation dropped, whitespace collapsed. Wording varies; the claim does not."""
    return " ".join(_NOISE.sub(" ", text.lower()).split())


def alike(first: str, second: str) -> float:
    """How alike two claims read, in [0, 1]. Empty against anything is 0, never 1.

    **`autojunk=False` IS LOAD-BEARING AND THE DEFAULT IS WRONG FOR THIS INPUT.** `SequenceMatcher`
    treats any element occurring in more than 1% of a sequence longer than 200 characters as
    "popular junk" and ignores it. Compared character by character, that junk is ordinary letters
    and spaces, so the ratio collapses on exactly the long claims this rule exists to compare: two
    real findings measured 97.3% alike scored **0.100** with the default. Most review comments are
    longer than 200 characters, so the rule was close to inert on real input while every unit test
    passed -- each of them compared strings short enough that the heuristic never engaged.
    """
    left, right = _plain(first), _plain(second)
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right, autojunk=False).ratio()


def repeats(findings: Sequence[Finding]) -> tuple[int, ...]:
    """Indices of findings that repeat an EARLIER one about the same file. Order preserved.

    The first statement of a claim is kept and later ones are reported, so the retained finding
    is the one the model reached first rather than an arbitrary member of the group.
    """
    said: list[tuple[str, str]] = []
    found: list[int] = []
    for index, finding in enumerate(findings):
        claim = finding.claim
        if any(path == finding.path and alike(claim, seen) >= SIMILAR_AT for path, seen in said):
            found.append(index)
            continue
        said.append((finding.path, claim))
    return tuple(found)
