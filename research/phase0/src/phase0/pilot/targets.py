"""Which repositories this run walks, and which the journal lets it skip.

WHAT: `choose` — resolves the repository set for one pilot invocation, honouring
      `--only-repo` and the journal's done-markers.
WHY:  Split from `run.py` when the re-scan flag pushed it over the file cap. Selecting
      the work and doing the work are separate concerns, and this one carries the rule
      that matters: a re-scan must ignore the done-markers for its own targets and
      honour them for everything else. Getting that backwards either re-walks all ninety
      repositories or silently walks none.

      A name that is not in the eligible population is refused rather than skipped. The
      alternative walks nothing, exits 0, and reports a re-scan that did not happen --
      which is the failure shape this project keeps finding in its own diagnostics.
IMPORTS: stdlib dataclasses, pathlib. phase0.pipeline.journal.
CONSUMED BY: pilot/run.py.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path

from phase0.pipeline import resume


@dataclass(frozen=True, slots=True)
class Targets:
    """The repositories to walk, those to skip, and the reason if this is a re-scan."""

    chosen: list[str]
    already: set[str]
    rescan: str

    @property
    def announcement(self) -> str:
        """What the run prints before it starts, so a log says which mode it ran in."""
        if self.rescan:
            return f"re-walking {len(self.chosen)} repo(s) — {self.rescan}"
        return f"taking {len(self.chosen)} repos"


def choose(
    grouped: Collection[str],
    journal_path: Path,
    repos: int,
    only_repo: list[str] | None = None,
    rescan_reason: str = "",
) -> Targets:
    """Resolve the repository set, refusing a target that is not in the population."""
    if only_repo:
        missing = [name for name in only_repo if name not in grouped]
        if missing:
            raise SystemExit(f"not in the eligible population: {', '.join(sorted(missing))}")
        chosen = sorted(only_repo)
        # The done-markers are dropped for these and kept for everything else.
        return Targets(chosen, resume.completed_repos(journal_path) - set(chosen), rescan_reason)

    return Targets(sorted(grouped)[:repos], resume.completed_repos(journal_path), "")
