"""The agent arm: merged agent-authored Python PRs with mined commit evidence.

WHAT: `agent_prs(aidev)` -- every merged agent PR carrying at least one commit SHA and
      one changed `.py` file, as `Candidate`s stamped with the agent that wrote them.
WHY:  This is the study's PRIMARY population and it did not exist. The pilot ran on
      `handlabel/select.py`, which is a human-arm source by design and says so, and the
      resulting 90-repository journal was read as the agent arm for weeks.

      The tables mirror the figshare human package exactly -- `pr_commits` for
      `human_commit`, `pr_commit_details` for `human_commit_detail`, `pull_request` for
      `human_pr_python` -- so the shape of the join is deliberately identical to
      `eligible_prs`. What differs is the arm, and it is not a constant here: AIDev's
      `agent` column holds five distinct labels and each Candidate carries its own, so
      A17's per-agent stratification has a field to stratify on rather than a filename
      to infer from.

      The `.py` filter comes from the details join, exactly as on the human side. There
      is no agent equivalent of `human_pr_python`'s pre-filtering, and inventing one by
      language metadata would narrow the population on a fact the human arm was not
      narrowed on -- a difference between arms introduced by us rather than by the data.
IMPORTS: pandas, phase0.handlabel.select (Candidate, repo_full_name), phase0.joins.
CONSUMED BY: pilot/run.py; tests/pilot/test_agent_population.py.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from phase0.handlabel.select import Candidate, repo_full_name
from phase0.joins import checked_merge

PR_TABLE = "pull_request.parquet"
COMMIT_TABLE = "pr_commits.parquet"
DETAIL_TABLE = "pr_commit_details.parquet"
# `pr_commit_details` is 712k rows and ships the full patch text on every one. Reading
# only what the join needs keeps this to a few hundred MB instead of several GB.
DETAIL_COLUMNS = ["pr_id", "filename"]


def agent_prs(aidev: Path) -> list[Candidate]:
    """Every judgeable agent PR, in a fixed order. Deterministic given the tables."""
    prs = pd.read_parquet(
        aidev / PR_TABLE, columns=["id", "number", "title", "agent", "merged_at", "repo_url"]
    )
    commits = pd.read_parquet(aidev / COMMIT_TABLE, columns=["pr_id", "sha"])
    details = pd.read_parquet(aidev / DETAIL_TABLE, columns=DETAIL_COLUMNS)
    # Same cast as the human side, for the same reason: a str/int64 key mismatch joins
    # to zero rows and reports it as an empty corpus rather than as a broken join.
    for frame in (commits, details):
        frame["pr_id"] = frame["pr_id"].astype("int64")

    merged = prs[prs["merged_at"].notna()].copy()
    # `na=False` is a decision, not a coercion. 5,132 of 711,923 detail rows carry a
    # null filename, touching 5,025 of 33,580 PRs -- a commit whose file list AIDev did
    # not mine. The human tables have none, so this is a real difference between the
    # arms and not a parsing artefact. A null filename is not evidence of a `.py` file,
    # so it drops out here; what it must not do is raise or be counted as one. The PR
    # survives on its other rows if it has any, which is the same rule the human side
    # applies to a commit with no `.py` file in it.
    python_files = details[details["filename"].str.endswith(".py", na=False)]

    shas = commits.groupby("pr_id")["sha"].apply(lambda s: tuple(dict.fromkeys(s)))
    files = python_files.groupby("pr_id")["filename"].apply(lambda s: tuple(sorted(set(s))))
    evidence = pd.DataFrame({"sha_list": shas}).join(
        pd.DataFrame({"file_list": files}), how="inner"
    )
    evidence = evidence.reset_index().rename(columns={"pr_id": "id"})

    joined, _ = checked_merge(
        merged,
        evidence,
        on="id",
        how="inner",
        name="merged agent PRs x mined evidence",
        # A tripwire for a broken key, not a claim about coverage. This join also
        # requires a `.py` file, so most merged PRs are expected to drop out here.
        minimum_match_rate=0.05,
    )
    joined = joined.sort_values("id").reset_index(drop=True)

    return [
        Candidate(
            pr_id=int(row["id"]),
            repo=repo_full_name(row["repo_url"]),
            number=int(row["number"]),
            merged_at=str(row["merged_at"]),
            title=str(row["title"]),
            commit_shas=tuple(row["sha_list"]),
            changed_files=tuple(row["file_list"]),
            # Per row, from the data. Five agents, and A17 reports RR by agent.
            arm=str(row["agent"]),
        )
        for _, row in joined.iterrows()
    ]
