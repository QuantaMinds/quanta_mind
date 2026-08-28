"""Refuse a findings pack that leaks its own key, and say what each check examined.

WHAT: `audit(pack)` returns every leak found, empty when there are none. `PackRejected` is
      raised by `require_clean` for callers that must not proceed.
WHY:  Split from `findings.py`, which owns building a pack. This owns disbelieving one. The
      separation is the point: the code that constructs the arms is the last code that should
      certify them, and every leak found so far was invisible to the constructor.

      **EVERY CHECK REPORTS ITS OWN COVERAGE.** The first version of this audit announced "no
      planted item's named symbols appear in the code shown" while having examined 7 of 12 --
      the five it skipped were the generic claims most at risk of being accidentally true, and
      the clean result came from not looking. A count that does not equal the arm size is a
      failure here, never a footnote. This is AGENTS.md rule 14 and the same shape as
      `bench/forensic/population.py:assert_intersects`.

      What each check defends against, in the order they were found by breaking them:
        - a claim repeated ANYWHERE: the labeller reads one sentence twice and both answers
          arrive together, which is worse when the repeats share an arm;
        - a diff repeated: same, in the other direction;
        - a lopsided test/source split: a rule learnable instead of reading;
        - a planted claim whose named entities DO appear in its host: a control that may be
          accidentally TRUE, marking a correct labeller wrong and withholding a real result;
        - a planted claim naming nothing at all: falsity never established.
IMPORTS: stdlib, phase0.handlabel.findings.
CONSUMED BY: `phase0/findings/sample.py`; tests/findings/test_pack_leaks.py.
"""

from __future__ import annotations

from collections import defaultdict

from phase0.findings.pack import Pack, overlap

# Above this share of a planted claim's named entities appearing in its host diff, the claim
# may be describing the code shown, and the key's answer is no longer safe.
ACCIDENTAL_TRUTH = 0.5
# Test-file diffs may differ between arms by at most this, beyond which the split is learnable.
KIND_SKEW = 2


class PackRejected(RuntimeError):
    """A pack that would hand the labeller its key. Carries every leak found, not the first."""


def _repeats(pack: Pack, of: str) -> list[str]:
    """Items sharing a claim or a diff, named with the arms they fall in."""
    groups: dict[str, list[int]] = defaultdict(list)
    for item in pack.blind:
        groups[getattr(item, of)].append(item.label_id)
    return [
        f"{of} repeated across items {ids} -> arms {sorted(pack.arm_of(i) for i in ids)}"
        for ids in groups.values()
        if len(ids) > 1
    ]


def coverage(pack: Pack) -> dict[str, int]:
    """How many items each arm holds, and how many of the planted arm were assessable.

    Returned rather than printed so a caller can assert on it. `planted_examined` below
    `planted` is the defect this module exists to make impossible to miss.
    """
    planted = [i for i in pack.blind if pack.arm_of(i.label_id) == "PLANTED"]
    real = [i for i in pack.blind if pack.arm_of(i.label_id) == "REAL"]
    return {
        "real": len(real),
        "planted": len(planted),
        "planted_examined": sum(overlap(i.claim, i.diff) >= 0.0 for i in planted),
        "real_examined": sum(overlap(i.claim, i.diff) >= 0.0 for i in real),
    }


def audit(pack: Pack) -> list[str]:
    """Every leak in `pack`, empty when it is clean. Never stops at the first."""
    found: list[str] = []
    found += _repeats(pack, "claim")
    found += _repeats(pack, "diff")

    arms: dict[str, list[str]] = defaultdict(list)
    for item in pack.blind:
        arms[pack.arm_of(item.label_id)].append(item.path)
    if (
        abs(sum("test" in p for p in arms["REAL"]) - sum("test" in p for p in arms["PLANTED"]))
        > KIND_SKEW
    ):
        found.append(
            f"test-file diffs are lopsided: REAL {sum('test' in p for p in arms['REAL'])}, "
            f"PLANTED {sum('test' in p for p in arms['PLANTED'])} -- learnable without reading"
        )

    untestable: list[int] = []
    for item in pack.blind:
        if pack.arm_of(item.label_id) != "PLANTED":
            continue
        share = overlap(item.claim, item.diff)
        if share < 0.0:
            untestable.append(item.label_id)
        elif share > ACCIDENTAL_TRUTH:
            found.append(
                f"item {item.label_id}: {share:.0%} of the claim's named entities DO appear in "
                f"the code shown -- this control may be accidentally TRUE"
            )
    if untestable:
        found.append(
            f"planted items naming nothing checkable, so falsity is unverified: {untestable}"
        )

    seen = coverage(pack)
    if seen["planted_examined"] != seen["planted"]:
        found.append(
            f"the accidental-truth check examined {seen['planted_examined']} of "
            f"{seen['planted']} planted items; the rest were never assessed"
        )
    # The REAL arm is deliberately NOT filtered on being assessable. Excluding published
    # findings that happen to name no symbol would bias the sample toward specific claims and
    # quietly change what the measurement is of. Its coverage is reported, never enforced.
    return found


def require_clean(pack: Pack) -> dict[str, int]:
    """Coverage counts, or `PackRejected` naming every leak. Use before showing anyone a sheet."""
    leaks = audit(pack)
    if leaks:
        raise PackRejected(f"{len(leaks)} leak(s): " + "; ".join(leaks))
    return coverage(pack)
