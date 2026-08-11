"""Corpus extraction: the AIDev dataset to a flat list of merged PRs.

WHAT: Loads the AIDev parquet tables, joins them, filters to the population fixed in
      `PHASE0_PREREGISTRATION.md` “Design”, and emits one PRRecord per PR. Both arms.
WHY:  Every later stage keys off `parent_sha`, which must be the commit the change
      LANDED on, never the merged state and never `base.sha`. AIDev carries no SHA
      at all, so it is resolved here, once, by amendment A2's decision table. Doing
      it in one place is what makes the guarantee auditable rather than a
      convention each stage is trusted to follow.

      Merged-only is a hard filter, not a convenience. The outcome is a 7-day
      post-merge scan, so an unmerged PR has no window and cannot be classified.
      The corpus arithmetic already accounts for it: ~4,798 structural PRs become
      ~3,300 merged at the 69.3% acceptance rate.

      Licences are recorded per repository. AIDev's terms are that "each source
      repository retains its original copyright", and `PHASE0_RUNBOOK.md`
      “Authenticity checklist” requires publishing the raw inputs alongside the
      result — so the publishable subset is filtered before results/, not after.
IMPORTS: pandas, phase0.attrition, phase0.joins, phase0.github_pulls,
      phase0.parent_commit.
CONSUMED BY: run_pipeline.py; tests/test_extract_prs.py.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from phase0.attrition import Attrition
from phase0.joins import JoinReport, checked_merge

Language = str  # "python" | "typescript" — the two arms in scope, `PHASE0_RUNBOOK.md` “TS/JS arm”

# `PHASE0_PREREGISTRATION.md` “Design”: the five task types that "directly impact program
# structure". docs and test
# are excluded, which is what turns 7,191 agent PRs into 4,798.
STRUCTURAL_TASK_TYPES: frozenset[str] = frozenset({"feat", "fix", "perf", "refactor", "chore"})

# Redistributable licences. Anything else is analysed but never published.
PUBLISHABLE_LICENCES: frozenset[str] = frozenset(
    {"mit", "apache-2.0", "bsd-3-clause", "bsd-2-clause", "isc", "unlicense", "cc0-1.0"}
)

AGENT_TABLES = ("pull_request", "pr_task_type")
HUMAN_TABLES = ("human_pull_request", "human_pr_task_type")


@dataclass(frozen=True, slots=True)
class PRRecord:
    """One merged pull request, with everything the later stages need."""

    pr_id: str
    repo: str  # owner/name
    language: Language
    parent_sha: str
    merged_sha: str
    merged_at: str  # ISO 8601 UTC
    changed_files: tuple[str, ...]
    changed_symbols: tuple[str, ...]
    arm: str = "agent"  # "agent" | "human"
    task_type: str = ""
    licence: str = ""
    repo_id: str = ""  # the clustering unit, per A8
    # The branch the PR merged INTO. The outcome scan walks this, not the clone's HEAD:
    # 15.5% of the corpus merges into dev, develop or a feature branch, and walking HEAD
    # scored every one of them CLEAN.
    base_ref: str = ""
    # HOW the parent above was decided, and by WHICH rule -- `MergeShape.value` and
    # `ResolutionRule.value`. Carried on the record so `run_pipeline` can CONSUME the
    # resolution instead of recomputing it; the version that recomputed passed a file
    # count where a commit count belongs and omitted the subjects entirely, so it ran
    # A28's corpus-free rule never and the corpus file rules always. A46, and the same
    # rebuild-instead-of-consume shape as `_as_record`.
    #
    # Appended last with empty defaults, so a records file written before this field
    # reads as UNRECORDED. Empty is never "ambiguous" and never "we checked" -- it is
    # "nothing on disk says", which is the only honest reading of an older file.
    parent_resolution_method: str = ""
    parent_resolution_rule: str = ""

    @property
    def is_publishable(self) -> bool:
        """Licences decide what may be published — `PHASE0_RUNBOOK.md`, “Authenticity
        checklist”.
        """
        return self.licence.lower() in PUBLISHABLE_LICENCES


def load_table(dataset: Path, name: str) -> pd.DataFrame:
    """One AIDev table, from a local parquet directory.

    Kept separate so a re-run reads the same bytes: the study must reproduce from raw
    data, and a loader that reached for the network would make the corpus a moving
    target.
    """
    path = dataset / f"{name}.parquet"
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} not found. Download the AIDev tables first:\n"
            f"  huggingface-cli download hao-li/AIDev --repo-type dataset --local-dir {dataset}"
        )
    return pd.read_parquet(path)


def _select(
    pulls: pd.DataFrame, tasks: pd.DataFrame, repos: pd.DataFrame
) -> tuple[pd.DataFrame, list[JoinReport]]:
    """Join the three tables and keep only the population the design fixes.

    Both joins are LEFT, which is the dangerous shape: a zero-match join returns the
    full frame with `type` and `language` all null, `_filter` then drops every row for
    not being Python, and the attrition counter reports `not_python = total`. That is
    a computed-looking number with no data behind it. The floors below make it raise.

    The floors are deliberately loose. They are a tripwire for a broken key, not a
    claim about the corpus — AIDev does not label every PR with a task type, and the
    real rates are measured and reported rather than asserted here.
    """
    with_type, task_join = checked_merge(
        pulls,
        tasks[["id", "type"]],
        on="id",
        how="left",
        name="pull_request x pr_task_type",
        minimum_match_rate=0.5,
    )
    with_repo, repo_join = checked_merge(
        with_type,
        repos[["id", "language", "license"]].rename(columns={"id": "repo_id"}),
        on="repo_id",
        how="left",
        name="pull_request x repository",
        # Every PR belongs to a repository, so anything below near-total is a key
        # fault. `language` gates the Python filter, which is the population itself.
        minimum_match_rate=0.99,
    )
    return with_repo, [task_join, repo_join]


def _filter(frame: pd.DataFrame) -> tuple[pd.DataFrame, Attrition]:
    """Apply the population filters, counting what each one removes."""
    total = len(frame)
    python_only = frame[frame["language"].str.lower() == "python"]
    structural = python_only[python_only["type"].isin(STRUCTURAL_TASK_TYPES)]
    merged = structural[structural["merged_at"].notna() & (structural["merged_at"] != "")]

    return merged, Attrition(
        not_python=total - len(python_only),
        not_structural=len(python_only) - len(structural),
        not_merged=len(structural) - len(merged),
    )


def iter_candidates(dataset: Path, arm: str = "agent") -> Iterator[dict[str, object]]:
    """Every row that survives the population filters, as plain dicts."""
    pull_table, task_table = AGENT_TABLES if arm == "agent" else HUMAN_TABLES
    frame, _ = _select(
        load_table(dataset, pull_table),
        load_table(dataset, task_table),
        load_table(dataset, "repository"),
    )
    kept, _ = _filter(frame)
    for row in kept.to_dict(orient="records"):
        yield dict(row)


def population_counts(dataset: Path, arm: str = "agent") -> tuple[int, Attrition, list[JoinReport]]:
    """How many survive, why the rest did not, and what the joins actually matched.

    The design's arithmetic is a prediction; this is the measurement, and
    `PHASE0_RUNBOOK.md` “Days 3-5” treats a large deviation as a stop condition.

    The join reports are returned rather than logged because the pilot has to report
    them as shape metrics. An attrition count is only interpretable next to the match
    rate of the join that produced the column it filters on.
    """
    pull_table, task_table = AGENT_TABLES if arm == "agent" else HUMAN_TABLES
    frame, joins = _select(
        load_table(dataset, pull_table),
        load_table(dataset, task_table),
        load_table(dataset, "repository"),
    )
    kept, attrition = _filter(frame)
    return len(kept), attrition, joins
