"""A labelling pack for the correctness of PUBLISHED model findings.

WHAT: `draw(findings)` returns a `Pack` -- every item a real published finding shown beside the
      diff it points at. There is no control arm and no sealed key.
WHY:  A6 measured 0.686 findings published per change and could not say how many were right.

      **THE PLANTED-CONTROL DESIGN WAS TRIED AND IS GONE.** Half the pack used to be a genuine
      claim shown beside code it was not about, so that marking everything TRUE scored 50%. It
      failed for a reason worth recording: a rater scores 100% on such controls by checking
      whether the claim's filename appears in the diff header, **never once assessing whether a
      finding is correct**. Measured on the built pack, a real claim's named symbols appeared in
      its diff 93% of the time against 5% for a planted one -- the arms were separable by a
      surface cue orthogonal to the thing being measured. An isolated judge then demonstrated
      it: 12 of 12 controls "caught", every rejection reading "the diff contains no X at all".
      It scored full marks on the control arm without performing the task.

      **ATTENTION IS CHECKED BY THE DECIDING LINE INSTEAD**, which is this project's own
      precedent -- `adjudication-preregistration.md` recorded every verdict "with the specific
      line of code that decides it". A rater who did not read cannot quote a line that is in the
      diff, and `scoring.py` checks that mechanically. This needs no controls, cannot be gamed
      by a filename cue, and removes the sealed key that A57 warns about: with nothing to leak,
      auditing the pack cannot burn the draw.
IMPORTS: stdlib only.
CONSUMED BY: `findings/audit.py`, `findings/sample.py`; tests/findings/test_pack_leaks.py.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

SIZE_DEFAULT = 24


class NotEnoughFindings(RuntimeError):
    """The harvested pool cannot fill the pack. Carries what was available and what was needed."""


@dataclass(frozen=True, slots=True)
class Finding:
    """One published finding and the change it points at."""

    sha: str
    path: str
    claim: str
    quote: str
    diff: str

    def judgeable(self) -> bool:
        """Whether the line the claim anchors to is inside the diff the labeller will see.

        `diff_for` truncates. An item whose quoted line fell outside cannot be judged, and a
        rater marking it FALSE would be recording the pack's truncation as the finding's error.
        """
        return bool(self.quote.strip()) and self.quote.strip() in self.diff


@dataclass(frozen=True, slots=True)
class Item:
    """One row of the sheet: a real finding, its code, and the anchor it claims."""

    label_id: int
    claim: str
    diff: str
    path: str
    quote: str


@dataclass(frozen=True, slots=True)
class Pack:
    """A completed draw. Every item is a real published finding; there is nothing sealed."""

    items: tuple[Item, ...]
    seed: int
    considered: int
    # Findings excluded because their quoted line fell outside the truncated diff. Returned
    # rather than dropped: a pack that silently passed over them would look identical to one
    # that met none, and the count is the instrument reporting on itself.
    unjudgeable: int = 0


def draw(findings: list[Finding], *, size: int = SIZE_DEFAULT, seed: int = 20260828) -> Pack:
    """Draw `size` published findings. Raises rather than quietly returning a smaller pack."""
    judgeable = [f for f in findings if f.judgeable()]
    if findings and not judgeable:
        raise NotEnoughFindings(
            f"all {len(findings)} findings quote a line outside their own diff. A filter "
            f"admitting NOTHING is a statement about the two populations -- the quotes and the "
            f"diff text -- not about the findings. Check `diff_for`'s truncation."
        )

    # One finding per distinct diff. Two items showing the same code invite a rater to answer
    # the second from the first, and the second finding is not worth that.
    by_diff: dict[tuple[str, str], Finding] = {}
    for f in judgeable:
        by_diff.setdefault((f.sha, f.path), f)
    pool = list(by_diff.values())

    # Distinct claims too: a repeated sentence is answered once and copied.
    seen: set[str] = set()
    unique: list[Finding] = []
    for f in pool:
        if f.claim not in seen:
            seen.add(f.claim)
            unique.append(f)

    rng = random.Random(seed)
    rng.shuffle(unique)
    if len(unique) < size:
        raise NotEnoughFindings(
            f"{len(unique)} distinct findings available, {size} needed. Harvest more commits "
            f"rather than shrinking the pack, which would change what is measured."
        )

    chosen = unique[:size]
    items = tuple(Item(i, f.claim, f.diff, f.path, f.quote) for i, f in enumerate(chosen, 1))
    return Pack(items, seed, len(findings), len(findings) - len(judgeable))
