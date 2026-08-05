"""The population a labelling sample may be drawn from.

WHAT: Every merged human Python PR carrying enough evidence to be judged at all -- a
      mined commit SHA and at least one changed `.py` file.
WHY:  Eligibility is decided here, once, on facts that cannot correlate with the outcome.
      Nothing about breakage enters this module and nothing may: if the population is
      narrowed after anyone has seen a verdict, the gate measures whoever narrowed it.

      The human arm is used because it needs no GitHub token -- the replication package
      supplies commit SHAs and changed filenames directly -- so this gate runs while the
      token still blocks everything downstream. The classifier reads git history and is
      arm-agnostic, but the choice is recorded rather than assumed.
IMPORTS: pandas, phase0.joins.
CONSUMED BY: handlabel/draw.py; tests/handlabel/.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pandas as pd

from phase0.joins import checked_merge

PACKAGE_MEMBER = "AIDev_BC_Analyser/{name}.parquet"


@dataclass(frozen=True, slots=True)
class Candidate:
    """One PR that could be labelled. Carries no outcome and no verdict."""

    pr_id: int
    repo: str  # owner/name
    number: int
    merged_at: str
    title: str
    commit_shas: tuple[str, ...]
    changed_files: tuple[str, ...]

    @property
    def url(self) -> str:
        """What the labeller opens -- the only field that reaches the blind sheet."""
        return f"https://github.com/{self.repo}/pull/{self.number}"


def _read(package: Path, name: str) -> pd.DataFrame:
    with zipfile.ZipFile(package) as archive:
        return pd.read_parquet(BytesIO(archive.read(PACKAGE_MEMBER.format(name=name))))


def _repo_full_name(url: str) -> str:
    """`https://api.github.com/repos/owner/name` -> `owner/name`."""
    return "/".join(str(url).rstrip("/").split("/")[-2:])


def eligible_prs(package: Path) -> list[Candidate]:
    """Every judgeable PR, in a fixed order. Deterministic given the package."""
    prs = _read(package, "human_pr_python")
    commits = _read(package, "human_commit")
    details = _read(package, "human_commit_detail")
    # The package ships `pr_id` as a string on both commit tables while the PR table
    # holds int64. Joining uncast returns zero rows, silently.
    for frame in (commits, details):
        frame["pr_id"] = frame["pr_id"].astype("int64")

    merged = prs[prs["merged_at"].notna()].copy()
    python_files = details[details["filename"].str.endswith(".py")]

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
        name="merged human PRs x mined evidence",
        # SHA coverage is 96.8%; this join also requires a .py file, so the floor is a
        # broken-key tripwire rather than a claim about the corpus.
        minimum_match_rate=0.3,
    )
    joined = joined.sort_values("id").reset_index(drop=True)

    return [
        Candidate(
            pr_id=int(row["id"]),
            repo=_repo_full_name(row["repo_url"]),
            number=int(row["number"]),
            merged_at=str(row["merged_at"]),
            title=str(row["title"]),
            commit_shas=tuple(row["sha_list"]),
            changed_files=tuple(row["file_list"]),
        )
        for _, row in joined.iterrows()
    ]
