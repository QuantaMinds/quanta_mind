"""`quantamind retrospective` — replay the ranker over a clone's own history.

WHAT: `run_retrospective(clones, repo)` replays each clone, pools when there is more than one, and
      prints the report. The index is scratch and is thrown away.
WHY:  **EVERY OTHER COMMAND ALREADY LIVED IN `serve/commands/` AND THIS ONE DID NOT.** It sat
      inside `serve/cli.py`, which is the argument parser, so that module both described the
      command line and implemented one command. Splitting it out was forced by the 200-line cap
      and is the right shape regardless: the parser now dispatches, uniformly, and nothing else.

      **THE RETROSPECTIVE IS THE ONLY BOTTOM-UP MOTION THIS PRODUCT HAS** — one clone, no access,
      no install — which is why it is worth keeping easy to find.
IMPORTS: render.replay_report, serve.retrospective, types.pooled_outcome, imported at module scope
      here because a caller has already chosen this command by the time it is loaded.
CONSUMED BY: `serve/cli.py`.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from quantamind.render.replay_report import report
from quantamind.serve.retrospective import replay
from quantamind.types.pooled_outcome import pool


def run_retrospective(clones: list[Path], repo: str) -> int:
    """Replay one clone and print the report. The index is scratch and is thrown away."""
    for clone in clones:
        if not (clone / ".git").exists():
            print(f"{clone} is not a git clone; a retrospective reads history and nothing else")
            return 1
    outcomes = []
    with TemporaryDirectory() as scratch:
        for index, clone in enumerate(clones):
            # NO CAP. `SURVIVOR_CAP` stops one large repository dominating a pooled figure in the
            # RESEARCH, where the six were compared to each other. Here the customer's own history
            # is the answer, and capping would discard it and then report it short of the floor:
            # scrapy has 1,447 events and the capped run announced "132 short of 500".
            # owner/name is what store.touches requires; a colon or a bare directory is rejected.
            name = repo if len(clones) == 1 else f"{repo}/{clone.name}"
            outcomes.append(replay(clone, name, Path(scratch) / f"{index}.db"))
    print(report(outcomes, pool(outcomes) if len(outcomes) > 1 else None))
    return 0
