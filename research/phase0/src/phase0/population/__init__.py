"""Corpus populations, one module per arm, each stating the arm it draws.

WHAT: `agent.agent_prs` builds the primary arm from AIDev's own tables. The human arm
      lives in `handlabel/select.py`, which predates this package and is left where its
      consumers expect it.
WHY:  There was no such thing as "the population" and the code implied there was. A
      90-repository pilot called `eligible_prs` and got the HUMAN arm, correctly and
      silently, and read every number it produced as the agent arm. A package whose
      modules are named for arms makes the choice a thing a caller has to type.
IMPORTS: phase0.arm, phase0.handlabel.select, phase0.population.agent.
CONSUMED BY: pilot/run.py; tests/pilot/test_agent_population.py.
"""

from __future__ import annotations

from pathlib import Path

from phase0 import arm
from phase0.handlabel.select import Candidate, eligible_prs
from phase0.population.agent import agent_prs

__all__ = ["Candidate", "agent_prs", "for_arm"]


def for_arm(name: str, aidev: Path, package: Path) -> tuple[list[Candidate], str | frozenset[str]]:
    """The population for `name`, and the arm claim a caller must then verify.

    Returns the claim rather than checking it here so that the check happens in the
    runner, next to the print that reports it. A population function that validated
    itself would be agreeing with itself.
    """
    if name == "agent":
        return agent_prs(aidev), arm.AGENTS
    return eligible_prs(package), arm.HUMAN
