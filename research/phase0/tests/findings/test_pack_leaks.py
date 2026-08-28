"""Verification that a findings pack cannot be answered without reading it.

WHAT: Pins the exclusions that are counted rather than dropped, and -- by breaking each one --
      that every audit check fires.
WHY:  The planted-control design this replaced was audited clean and was still answerable
      without doing the task: a rater scores full marks by checking whether the claim's filename
      appears in the diff header. What survives here are the defects that still let a rater
      answer once and copy: a repeated claim, a repeated diff, an item with no quotable anchor.

      **EVERY CHECK IS SABOTAGED, NOT JUST CALLED.** A test that builds a clean pack and asserts
      `audit() == []` passes equally well when `audit` returns `[]` unconditionally.
IMPORTS: pytest, phase0.findings.{pack,audit}.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import dataclasses

import pytest

from phase0.findings.audit import PackRejected, audit, coverage, require_clean
from phase0.findings.pack import Finding, NotEnoughFindings, Pack, draw


def _findings(n: int) -> list[Finding]:
    out = []
    for i in range(n):
        path = "tests/test_mod.py" if i % 7 == 0 else f"pkg/mod_{i}.py"
        quote = f"    value_{i} = compute_{i}(arg)"
        diff = f"--- a/{path}\n+++ b/{path}\n@@\n+{quote}\n+    return value_{i}\n"
        out.append(
            Finding(
                f"{i:040x}", path, f"The `compute_{i}` call mishandles `value_{i}`.", quote, diff
            )
        )
    return out


def _pack(n: int = 30, size: int = 8, **kw) -> Pack:
    return draw(_findings(n), size=size, **kw)


def _replace(pack: Pack, label_id: int, **changes) -> Pack:
    items = tuple(
        dataclasses.replace(i, **changes) if i.label_id == label_id else i for i in pack.items
    )
    return dataclasses.replace(pack, items=items)


def test_a_clean_pack_passes_and_reports_full_coverage() -> None:
    """The baseline. Meaningless alone -- every test below breaks something to earn it."""
    assert require_clean(_pack()) == {
        "items": 8,
        "anchored": 8,
        "distinct_diffs": 8,
        "distinct_claims": 8,
    }


def test_every_item_is_a_real_published_finding() -> None:
    """There is no control arm, so nothing in the pack is a claim about code it is not about."""
    for item in _pack().items:
        assert item.quote in item.diff, f"item {item.label_id} anchors outside its own code"


def test_a_repeated_claim_is_refused() -> None:
    """A sentence already read is answered from memory, not from the code."""
    pack = _pack()
    first, second = pack.items[0], pack.items[1]
    pack = _replace(pack, second.label_id, claim=first.claim)
    complaints = [c for c in audit(pack) if "claim repeated" in c]
    assert len(complaints) == 1, audit(pack)
    assert str(sorted([first.label_id, second.label_id])) in complaints[0], complaints[0]


def test_a_repeated_diff_is_refused() -> None:
    pack = _pack()
    first, second = pack.items[0], pack.items[1]
    pack = _replace(pack, second.label_id, diff=first.diff)
    complaints = [c for c in audit(pack) if "diff repeated" in c]
    assert len(complaints) == 1, audit(pack)
    assert str(sorted([first.label_id, second.label_id])) in complaints[0], complaints[0]


def test_an_item_with_no_quotable_anchor_is_refused() -> None:
    """No deciding line could be given for it, so the rater would be blamed for the pack."""
    pack = _pack()
    victim = pack.items[0]
    pack = _replace(pack, victim.label_id, quote="a line that is nowhere in the diff")
    complaints = [c for c in audit(pack) if "anchor is not inside" in c]
    assert len(complaints) == 1, audit(pack)
    assert complaints[0].endswith(f"[{victim.label_id}]"), complaints[0]
    assert coverage(pack)["anchored"] == 7, coverage(pack)


def test_require_clean_raises_and_names_every_defect() -> None:
    pack = _pack()
    pack = _replace(pack, pack.items[1].label_id, claim=pack.items[0].claim)
    with pytest.raises(PackRejected, match="claim repeated"):
        require_clean(pack)


def test_a_quote_outside_its_diff_is_counted_not_dropped() -> None:
    """A silently shrunk sample fabricates an error rate out of the pack's own truncation."""
    pool = _findings(30)
    pool[0] = dataclasses.replace(pool[0], quote="    truncated_away = 1")
    pack = draw(pool, size=8)
    assert pack.unjudgeable == 1, pack.unjudgeable
    assert pack.considered == 30, pack.considered


def test_a_filter_admitting_nothing_raises() -> None:
    """AGENTS.md rule 14: a clean zero is a broken comparison until shown otherwise."""
    pool = [dataclasses.replace(f, quote="absent from every diff") for f in _findings(30)]
    with pytest.raises(NotEnoughFindings, match="admitting NOTHING"):
        draw(pool, size=8)


def test_too_small_a_pool_raises_rather_than_shrinking_the_pack() -> None:
    with pytest.raises(NotEnoughFindings, match="distinct findings available"):
        draw(_findings(5), size=8)
