"""Run the retrospective against a real repository and assert on what it actually printed.

WHAT: Clones a real repository, replays it, and checks the arithmetic that must hold on ANY
      history -- not a golden string, which would only prove the renderer is deterministic.
WHY:  The invariants asserted here are the ones a customer's own eyes would check, and each has a
      way of being wrong that a green "no exception raised" would hide.

      **THE DEGENERATE STRATUM MUST SCORE ZERO ON EVERY ARM.** With a budget of three, a change
      touching three or fewer files is read entirely, so no ordering can miss. If that row is ever
      non-zero the budget, the stratum boundary or the target set disagree, and the headline is
      built on sand. It is checked rather than assumed because it is the one number in the report
      whose correct value is known in advance.

      **AND THE PROVENANCE MUST BE IN THE OUTPUT.** The published figure and a fresh run have the
      same units; the text separating them is the only thing stopping them being pasted into one
      slide, so its absence is a defect and is asserted like any other.
IMPORTS: quantamind.render.replay_report, quantamind.serve.retrospective.
CONSUMED BY: `just verify`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from quantamind.render.replay_report import PROVENANCE, report
from quantamind.serve.retrospective import replay

REPO = "pallets/flask"


@pytest.fixture(scope="module")
def clone(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dest = tmp_path_factory.mktemp("retro") / "flask"
    done = subprocess.run(
        ["git", "clone", "-q", f"https://github.com/{REPO}.git", str(dest)],
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert done.returncode == 0, f"clone failed: {done.stderr[:200]}"
    return dest


def test_a_real_repository_replays_with_the_arithmetic_intact(clone: Path, tmp_path: Path) -> None:
    outcome = replay(clone, REPO, tmp_path / "index.db", cap=None)

    assert outcome.whole.events > 50, (
        f"only {outcome.whole.events} events (rejected: {outcome.rejected}) — too few to have "
        f"exercised anything"
    )
    assert outcome.whole.events == outcome.degenerate.events + outcome.informative.events, (
        "the strata do not sum to the whole; an event was counted twice or lost"
    )
    # The known answer: a budget of three covers a change of three, so nothing can miss.
    assert outcome.degenerate.miss == 0.0, (
        f"the <=3-file stratum missed {outcome.degenerate.miss:.2f}%, which is arithmetically "
        f"impossible when the budget reads the whole change"
    )
    assert outcome.degenerate.decides_nothing, "every arm must score identically where all is read"
    # Chance is a probability per event, so it cannot be worse than always-miss or better than hit.
    assert 0.0 <= outcome.whole.chance_miss <= 100.0
    assert outcome.b + outcome.c > 0, "no discordant pairs at all — the arms never disagreed"

    print(f"\n  {REPO}: {outcome.whole.events} events, ranker vs chance {outcome.whole.lift:+.2f}")
    informative = outcome.informative
    print(f"  informative: {informative.events} events, {informative.lift:+.2f}")


def test_the_report_states_which_corpus_it_is(clone: Path, tmp_path: Path) -> None:
    """A fresh run and the validated figure have the same units. The text is the only separation."""
    text = report([replay(clone, REPO, tmp_path / "i.db", cap=200)])

    assert PROVENANCE in text, "the report did not say this is not the validated result"
    assert "Measured ELSEWHERE" in text, "the published figure lost its separate attribution"
    for forbidden in ("compared with", "in line with", "confirms"):
        assert forbidden not in text.lower(), (
            f"the report says {forbidden!r}, which invites combining a one-repository run with a "
            f"figure measured on six others"
        )
