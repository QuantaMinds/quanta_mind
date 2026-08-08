"""The arm invariant, asserted against the real AIDev tables and the real population.

WHAT: That `arm_index` reads AIDev's own `agent` column, that the pilot's population is
      human throughout, and that claiming the agent arm for it RAISES.
WHY:  This is the regression test for a 90-repository pilot that ran to completion on
      the human arm while every metric it produced was read as the agent arm. Nothing
      raised, nothing looked wrong, and the star band that should have given it away was
      read as evidence FOR the agent reading -- A15 already recorded 503-with-none-below
      -500 as the human arm's defining filter.

      So these assertions run against the real parquet tables and the real
      `eligible_prs` output rather than fixtures. A fixture would prove the function
      compares two strings; the claim that needs guarding is about which rows are
      actually in which table, and only the tables can answer it.
IMPORTS: phase0.arm, phase0.handlabel.select, phase0.pilot.options, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import pytest

from phase0.arm import HUMAN, ArmMismatch, arm_index, arms_present, verify
from phase0.handlabel.select import eligible_prs
from phase0.pilot.options import PACKAGE, ROOT

AIDEV = ROOT / "data" / "aidev"

pytestmark = pytest.mark.skipif(
    not (AIDEV / "pull_request.parquet").is_file() or not PACKAGE.is_file(),
    reason="AIDev tables or replication package not downloaded",
)


def test_the_arm_comes_from_the_data_not_the_filename() -> None:
    """`human_pull_request` is Human throughout; `pull_request` is the five agents."""
    index = arm_index(AIDEV)
    labels = set(index.values())
    assert HUMAN in labels
    assert {"OpenAI_Codex", "Copilot", "Devin", "Cursor", "Claude_Code"} <= labels


def test_the_pilots_population_is_human_and_says_so() -> None:
    """The defect, stated as an assertion: this population is not the agent arm."""
    ids = [c.pr_id for c in eligible_prs(PACKAGE)]
    tally = arms_present(ids, AIDEV)
    assert set(tally) == {HUMAN}, f"population is not purely human: {tally}"
    assert tally[HUMAN] == len(ids)


def test_claiming_the_agent_arm_for_this_population_raises() -> None:
    """Not a warning and not a filter. A run past this reports the wrong population.

    `OpenAI_Codex` rather than a made-up label on purpose: the failure being guarded is
    a plausible claim about a real arm, not a typo.
    """
    ids = [c.pr_id for c in eligible_prs(PACKAGE)]
    with pytest.raises(ArmMismatch) as raised:
        verify(ids, "OpenAI_Codex", AIDEV)
    message = str(raised.value)
    assert HUMAN in message
    assert str(len(ids)) in message


def test_verify_passes_only_because_the_claim_is_true() -> None:
    """The companion to the raise: same call, correct claim, and it returns the tally."""
    ids = [c.pr_id for c in eligible_prs(PACKAGE)]
    assert verify(ids, HUMAN, AIDEV) == {HUMAN: len(ids)}


def test_an_id_in_neither_table_is_a_mismatch_not_an_abstention() -> None:
    """An unknown id means the population came from a source this index does not cover.

    Counting it as "cannot tell" and proceeding is how a population half-built from the
    wrong source would pass: the tally would look clean for every id it recognised.
    """
    assert arms_present([-1], AIDEV) == {"unknown": 1}
    with pytest.raises(ArmMismatch):
        verify([-1], HUMAN, AIDEV)
