"""Refuse a findings pack a rater could answer without reading it, and report each check's reach.

WHAT: `audit(pack)` returns every defect found, empty when there are none. `require_clean` raises.
WHY:  Split from `pack.py`, which builds a pack. This owns disbelieving one, because the code
      that constructs a thing is the last code that should certify it.

      **THERE IS NO LONGER A KEY TO LEAK, AND THAT REMOVED MOST OF THIS MODULE.** The planted
      arm is gone (see `pack.py`), so the checks that mattered -- claims appearing in both arms,
      arms separable by file kind, controls that might be accidentally true -- are gone with it.
      What remains is what still lets a rater answer without reading: a repeated diff or a
      repeated claim, either of which is answered once and copied.

      **EVERY CHECK REPORTS ITS OWN COVERAGE.** An earlier version of this file announced a
      clean result over the 7 of 12 items it had examined, having silently skipped the five most
      at risk. A count that does not equal the pack size is a failure here, never a footnote --
      AGENTS.md rule 14, and the shape of `bench/forensic/population.py:assert_intersects`.
IMPORTS: stdlib, phase0.findings.pack.
CONSUMED BY: `findings/sample.py`; tests/findings/test_pack_leaks.py.
"""

from __future__ import annotations

from collections import defaultdict

from phase0.findings.pack import Item, Pack


def anchored(item: Item) -> bool:
    """Whether a deciding line could be quoted for this item at all.

    Named rather than inlined because it is asked in two places, and an item where the answer
    is False is one the rater would be blamed for -- the pack's truncation, not their reading.
    """
    quote = item.quote.strip()
    return bool(quote) and quote in item.diff


class PackRejected(RuntimeError):
    """A pack a rater could answer without reading. Carries every defect, not just the first."""


def _repeats(pack: Pack, of: str) -> list[str]:
    """Items sharing a claim or a diff. Either is answered once and copied to the other."""
    groups: dict[str, list[int]] = defaultdict(list)
    for item in pack.items:
        groups[getattr(item, of)].append(item.label_id)
    return [f"{of} repeated across items {ids}" for ids in groups.values() if len(ids) > 1]


def coverage(pack: Pack) -> dict[str, int]:
    """Pack size, and how many items carry an anchor that is actually inside the code shown.

    `anchored` below `items` means the sheet contains a question the rater cannot fairly answer,
    which would be recorded as the finding's error rather than the pack's.
    """
    return {
        "items": len(pack.items),
        "anchored": sum(anchored(i) for i in pack.items),
        "distinct_diffs": len({i.diff for i in pack.items}),
        "distinct_claims": len({i.claim for i in pack.items}),
    }


def audit(pack: Pack) -> list[str]:
    """Every defect in `pack`, empty when it is clean. Never stops at the first."""
    found: list[str] = []
    found += _repeats(pack, "claim")
    found += _repeats(pack, "diff")

    unanchored = [
        i.label_id for i in pack.items if not (i.quote.strip() and i.quote.strip() in i.diff)
    ]
    if unanchored:
        found.append(
            f"items whose anchor is not inside the code shown, so no deciding line can be "
            f"quoted for them: {unanchored}"
        )

    seen = coverage(pack)
    if seen["anchored"] != seen["items"]:
        found.append(
            f"the anchor check reached {seen['anchored']} of {seen['items']} items; "
            f"the rest were never assessed"
        )
    return found


def require_clean(pack: Pack) -> dict[str, int]:
    """Coverage counts, or `PackRejected` naming every defect. Use before showing anyone a sheet."""
    defects = audit(pack)
    if defects:
        raise PackRejected(f"{len(defects)} defect(s): " + "; ".join(defects))
    return coverage(pack)
