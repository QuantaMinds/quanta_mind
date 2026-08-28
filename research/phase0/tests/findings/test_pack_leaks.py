"""Verification that a findings pack cannot hand the labeller its own key.

WHAT: Pins the balance that makes a constant answer fail, the exclusions that are counted
      rather than dropped, and -- by breaking each one -- that every audit check fires.
WHY:  Three leaks reached a built pack before any of them was noticed: one claim used three
      times, six claims present in BOTH arms, and repeated diffs homogeneous by arm. All were
      invisible to the code that built them and all were found by an audit that itself had a
      hole -- it examined 7 of 12 planted items and reported success.

      **SO EVERY CHECK HERE IS SABOTAGED, NOT JUST CALLED.** A test that only builds a clean
      pack and asserts `audit() == []` passes just as well when `audit` returns `[]`
      unconditionally. Each test below breaks the specific property and requires the specific
      complaint, which is the only thing that separates a working check from a silent one.
IMPORTS: pytest, phase0.findings.{pack,audit}.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import dataclasses
import re

import pytest

from phase0.findings.audit import PackRejected, audit, coverage, require_clean
from phase0.findings.pack import Finding, NotEnoughFindings, Pack, draw, overlap


def _findings(n: int) -> list[Finding]:
    """A pool whose claims each name a symbol that appears only in their own diff."""
    out = []
    for i in range(n):
        kind = "tests/test_mod.py" if i % 7 == 0 else f"pkg/mod_{i}.py"
        quote = f"    value_{i} = compute_{i}(arg)"
        diff = f"--- a/{kind}\n+++ b/{kind}\n@@\n+{quote}\n+    return value_{i}\n"
        out.append(
            Finding(
                sha=f"{i:040x}",
                path=kind,
                claim=f"The `compute_{i}` call mishandles `value_{i}` and returns early.",
                quote=quote,
                diff=diff,
            )
        )
    return out


def _pack(n: int = 30, **kw) -> Pack:
    return draw(_findings(n), real=6, planted=6, **kw)


def _replace(pack: Pack, label_id: int, **changes) -> Pack:
    blind = tuple(
        dataclasses.replace(i, **changes) if i.label_id == label_id else i for i in pack.blind
    )
    return dataclasses.replace(pack, blind=blind)


def _first(pack: Pack, arm: str):
    return next(i for i in pack.blind if pack.arm_of(i.label_id) == arm)


def test_a_clean_pack_passes_and_reports_full_coverage() -> None:
    """The baseline. Meaningless alone -- every test below breaks something to earn it."""
    seen = require_clean(_pack())
    assert seen == {"real": 6, "planted": 6, "planted_examined": 6, "real_examined": 6}, seen


def test_the_arms_are_balanced_so_a_constant_answer_scores_half() -> None:
    """An always-TRUE labeller must score 50%, not 100%. This is why controls exist."""
    pack = _pack()
    arms = [pack.arm_of(i.label_id) for i in pack.blind]
    assert arms.count("REAL") == arms.count("PLANTED") == 6, arms


def test_the_sheet_carries_no_arm() -> None:
    """The blind side is separated by TYPE, not by remembering to omit a column."""
    assert not any(
        "REAL" in str(v) or "PLANTED" in str(v)
        for i in _pack().blind
        for v in (i.claim, i.diff, i.path)
    ), "an arm name reached the blind sheet"


def test_a_repeated_claim_is_refused() -> None:
    """SABOTAGE: the leak that put six claims in both arms."""
    pack = _pack()
    victim, donor = _first(pack, "PLANTED"), _first(pack, "REAL")
    pack = _replace(pack, victim.label_id, claim=donor.claim)
    complaints = [c for c in audit(pack) if "claim repeated" in c]
    assert len(complaints) == 1, audit(pack)
    assert str(sorted([victim.label_id, donor.label_id])) in complaints[0], complaints[0]
    assert "['PLANTED', 'REAL']" in complaints[0], complaints[0]


def test_a_repeated_diff_is_refused() -> None:
    """SABOTAGE: three planted items once shared one diff, so judging one judged all three."""
    pack = _pack()
    victim, donor = _first(pack, "PLANTED"), _first(pack, "REAL")
    pack = _replace(pack, victim.label_id, diff=donor.diff)
    complaints = [c for c in audit(pack) if "diff repeated" in c]
    assert len(complaints) == 1, audit(pack)
    assert str(sorted([victim.label_id, donor.label_id])) in complaints[0], complaints[0]


def test_a_control_that_may_be_accidentally_true_is_refused() -> None:
    """SABOTAGE: a planted claim describing the code it is shown against."""
    pack = _pack()
    victim = _first(pack, "PLANTED")
    word = re.search(r"(value_\d+)", victim.diff).group(1)
    pack = _replace(pack, victim.label_id, claim=f"The `{word}` assignment here is wrong.")
    assert overlap(pack.blind[victim.label_id - 1].claim, victim.diff) == 1.0, "sabotage missed"
    assert any("accidentally TRUE" in c for c in audit(pack)), audit(pack)


def test_a_control_naming_nothing_checkable_is_refused() -> None:
    """SABOTAGE: the five items the first audit skipped in silence."""
    pack = _pack()
    victim = _first(pack, "PLANTED")
    pack = _replace(pack, victim.label_id, claim="This code is not correct.")
    complaints = [c for c in audit(pack) if "naming nothing checkable" in c]
    assert len(complaints) == 1, audit(pack)
    assert complaints[0].endswith(f"unverified: [{victim.label_id}]"), complaints[0]


def test_an_unexamined_planted_item_is_a_failure_not_a_footnote() -> None:
    """The specific defect: coverage below the arm size must be reported as a leak."""
    pack = _pack()
    pack = _replace(pack, _first(pack, "PLANTED").label_id, claim="Nothing nameable at all.")
    assert coverage(pack)["planted_examined"] == 5, coverage(pack)
    assert any("never assessed" in c for c in audit(pack)), audit(pack)


def test_require_clean_raises_and_names_every_leak_not_just_the_first() -> None:
    pack = _pack()
    pack = _replace(pack, _first(pack, "PLANTED").label_id, claim=_first(pack, "REAL").claim)
    with pytest.raises(PackRejected) as caught:
        require_clean(pack)
    assert "claim repeated" in str(caught.value), str(caught.value)


def test_untestable_overlap_is_minus_one_not_zero() -> None:
    """ "Checked and absent" and "never checked" must not be the same number."""
    assert overlap("This is wrong.", "any diff") == -1.0
    assert overlap("The `compute_9` call is wrong.", "no such symbol") == 0.0


def test_a_quote_outside_its_diff_is_counted_not_dropped() -> None:
    """A silently shrunk sample fabricates an error rate out of the pack's own truncation."""
    pool = _findings(30)
    pool[0] = dataclasses.replace(pool[0], quote="    line_that_was_truncated_away = 1")
    pack = draw(pool, real=6, planted=6)
    assert pack.unjudgeable == 1, pack.unjudgeable
    assert pack.considered == 30, pack.considered


def test_a_filter_admitting_nothing_raises() -> None:
    """AGENTS.md rule 14: a clean zero is a broken comparison until shown otherwise."""
    pool = [dataclasses.replace(f, quote="absent from every diff") for f in _findings(30)]
    with pytest.raises(NotEnoughFindings, match="admitting NOTHING"):
        draw(pool, real=6, planted=6)


def test_too_small_a_pool_raises_rather_than_shrinking_the_pack() -> None:
    with pytest.raises(NotEnoughFindings, match="distinct diffs available"):
        draw(_findings(8), real=6, planted=6)
