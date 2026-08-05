"""Which arm a PR belongs to, taken from the table that defines it and asserted.

WHAT: `arm_index` reads AIDev's own `agent` column into `pr_id -> arm`, and `verify`
      refuses a population whose claimed arm disagrees with it.
WHY:  A 90-repository pilot ran to completion on the HUMAN arm while every metric it
      produced was read as the agent arm. Nothing lied: `handlabel/select.py` draws
      from the figshare replication package, which ships `human_pr_python`,
      `human_commit` and `human_commit_detail` and no agent table at all, and says so
      in its docstring. `pilot/run.py` imported it as its population and inherited the
      arm silently, because no record, row or report ever named an arm to disagree with.

      The star band was the tell and it was read the favourable way: the journal's
      repositories floor at 528 stars, and A15 already records 503-with-none-below-500
      as the HUMAN arm's defining filter against the agent arm's 101 and 47.3%. The
      falsifying evidence was pre-registered, quantified, and in the same repository.

      So the arm is not inferred here and never derived from a filename. It is read out
      of the `agent` column both AIDev tables carry -- "Human" in `human_pull_request`,
      one of five agent labels in `pull_request` -- and a population that claims one arm
      while its ids live in the other RAISES. Cheap: two id columns, one set lookup per
      PR, run once before the clone loop rather than after thirty hours.
IMPORTS: pandas, stdlib dataclasses/functools/pathlib. Nothing from phase0.
CONSUMED BY: pilot/run.py, handlabel/select.py; tests/test_arm.py.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

HUMAN = "Human"
AGENT_TABLE = "pull_request.parquet"
HUMAN_TABLE = "human_pull_request.parquet"
# The column both tables carry. Reading the arm from the FILENAME would restate the
# assumption that was wrong; reading it from the data lets the data object.
ARM_COLUMN = "agent"


class ArmMismatch(RuntimeError):
    """A population's claimed arm disagrees with the table its PRs are in.

    Not a warning and not a filter. A run that proceeds past this measures a different
    population than the one it reports, which is indistinguishable from a correct run
    in every artefact it produces -- the failure this exists to make loud.
    """


def _read(aidev: Path, name: str) -> pd.DataFrame:
    return pd.read_parquet(aidev / name, columns=["id", ARM_COLUMN])


@lru_cache(maxsize=4)
def arm_index(aidev: Path) -> dict[int, str]:
    """`pr_id -> arm`, from both AIDev tables' own `agent` column.

    Cached on the directory: the study makes one of these calls per run, and the tables
    are ~40k rows across the two.
    """
    index: dict[int, str] = {}
    for name in (HUMAN_TABLE, AGENT_TABLE):
        frame = _read(aidev, name)
        index.update(zip(frame["id"].astype("int64"), frame[ARM_COLUMN].astype(str), strict=True))
    return index


def arms_present(pr_ids: list[int], aidev: Path) -> dict[str, int]:
    """How many of these ids fall in each arm, `unknown` for ids in neither table.

    Returned rather than printed so a caller can assert on it. A survey that reported
    this to stdout and proceeded would be the same shape as the defect it detects.
    """
    index = arm_index(aidev)
    counts: dict[str, int] = {}
    for pr_id in pr_ids:
        found = index.get(pr_id, "unknown")
        counts[found] = counts.get(found, 0) + 1
    return counts


def verify(pr_ids: list[int], claimed: str, aidev: Path) -> dict[str, int]:
    """Raise unless EVERY id is in the arm this population claims to be.

    Returns the tally so the caller can print what it verified. An id in neither table
    is a mismatch, not an abstention: it means the population was built from a source
    this index does not cover, and no later stage would notice.
    """
    counts = arms_present(pr_ids, aidev)
    wrong = {arm: n for arm, n in counts.items() if arm != claimed}
    if wrong:
        raise ArmMismatch(
            f"population claims arm {claimed!r} but {sum(wrong.values())} of {len(pr_ids)} "
            f"ids are elsewhere: {wrong}. Nothing downstream records an arm, so a run "
            f"past this point reports one population's numbers under another's name."
        )
    return counts
