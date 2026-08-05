"""The agent arm, built from AIDev and asserted against it.

WHAT: That `agent_prs` returns agent PRs and only agent PRs, that each Candidate carries
      the agent that actually wrote it, and that the arm's star band is the one A15
      describes rather than the human arm's.
WHY:  This population is the study's PRIMARY arm and it did not exist until now -- the
      pilot ran on the human arm for 90 repositories without anything objecting. The
      assertions here are the ones that would have objected.

      Real tables, not fixtures. A fixture would prove the join runs; the claims worth
      guarding are which rows come back and which arm they are in, and only AIDev can
      answer that. The star assertions matter most: 47.3% of agent repositories sit
      below 500 stars and 0% of human ones do, so a population that had silently
      reverted to the human source would show a floor above 500 and pass every other
      check in this file.
IMPORTS: phase0.arm, phase0.pilot.options, phase0.population.agent, pandas, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import pandas as pd
import pytest

from phase0.arm import AGENTS, HUMAN, ArmMismatch, arms_present, verify
from phase0.pilot.options import ROOT
from phase0.population.agent import agent_prs

AIDEV = ROOT / "data" / "aidev"

pytestmark = pytest.mark.skipif(
    not (AIDEV / "pr_commit_details.parquet").is_file(), reason="AIDev tables not downloaded"
)


@pytest.fixture(scope="module")
def population() -> list:
    return agent_prs(AIDEV)


def test_every_pr_is_in_the_agent_arm_and_none_is_human(population: list) -> None:
    """The assertion the 90-repo pilot never had."""
    tally = arms_present([c.pr_id for c in population], AIDEV)
    assert set(tally) <= AGENTS, f"non-agent ids present: {set(tally) - AGENTS}"
    assert HUMAN not in tally
    assert verify([c.pr_id for c in population], AGENTS, AIDEV) == tally


def test_each_candidate_carries_the_agent_that_wrote_it(population: list) -> None:
    """Per row, from the data -- A17 reports RR by agent and needs the field."""
    labels = {c.arm for c in population}
    assert labels <= AGENTS
    assert len(labels) >= 4, f"only {labels} present; the arm is not being read per row"


def test_the_star_band_is_the_agent_arms_not_the_humans(population: list) -> None:
    """A15's 26x popularity gap, asserted as a guard against reverting to the human source.

    The human arm floors at 503 with 0% below 500. If this population were ever rebuilt
    from the figshare package by accident, this is the assertion that would fail.
    """
    repos = pd.read_parquet(AIDEV / "repository.parquet")
    stars = repos[repos["full_name"].isin({c.repo for c in population})]["stars"]
    assert stars.min() < 503, "star floor is the human arm's; population may be human"
    assert (stars < 500).mean() > 0.2, "no low-star repositories: this is not the agent arm"


def test_claiming_the_human_arm_for_it_raises(population: list) -> None:
    """Symmetric to the human-side guard: the wrong claim fails in both directions."""
    with pytest.raises(ArmMismatch):
        verify([c.pr_id for c in population], HUMAN, AIDEV)


def test_the_population_is_the_size_and_composition_it_was_measured_at(
    population: list,
) -> None:
    """Golden counts from the first real build, against the pinned AIDev tables.

    Pinned deliberately. The tables do not move, so a change here is a change in the
    join -- and the join is where a silent narrowing would show up as a smaller corpus
    that still passes every other assertion in this file. 5,132 detail rows carry a null
    filename, which must drop out rather than raise or count as a Python file; if that
    handling changed, these numbers move.
    """
    assert len(population) == 3566
    assert len({c.repo for c in population}) == 389
    by_agent: dict[str, int] = {}
    for candidate in population:
        by_agent[candidate.arm] = by_agent.get(candidate.arm, 0) + 1
    assert by_agent == {
        "OpenAI_Codex": 2815,
        "Devin": 301,
        "Copilot": 271,
        "Cursor": 132,
        "Claude_Code": 47,
    }


def test_every_candidate_has_the_evidence_the_gate_requires(population: list) -> None:
    """A commit SHA and a `.py` file -- the same floor the human arm is held to."""
    assert [c.pr_id for c in population if not c.commit_shas] == []
    assert [c.pr_id for c in population if not c.changed_files] == []
    non_python = [f for c in population for f in c.changed_files if not f.endswith(".py")]
    assert non_python == []
