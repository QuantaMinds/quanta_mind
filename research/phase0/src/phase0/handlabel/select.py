"""Which 20 PRs get hand-labelled, decided before anyone looks at them.

WHAT: A deterministic, outcome-blind draw of 20 PRs from the human arm, plus a manifest
      hash so the set that was labelled is provably the set that was scored.
WHY:  If the sample is chosen after seeing anything about breakage, the day-2 gate
      measures the chooser rather than the classifier. So the rule is fixed here and
      takes no input that could correlate with the outcome: sort by `pr_id`, then take a
      fixed stride across the whole range.

      The stride matters. Taking the first 20 by id would draw one narrow slice of
      calendar time — ids are issued in order — and a classifier keyed on commit-message
      conventions could look better or worse purely by era. A stride spreads the draw
      across the full range at no cost in determinism.

      The human arm is used because it needs no GitHub token: the replication package
      (A19) supplies commit SHAs and changed filenames directly, so the gate can run
      while the token is still the blocker for everything else. The classifier reads git
      history and is arm-agnostic, but this choice is recorded rather than assumed —
      `PHASE0_PREREGISTRATION.md` “Timeline” gate does not specify an arm, and a reviewer will ask.
IMPORTS: pandas, phase0.joins. No outcome code — see the package docstring.
CONSUMED BY: sheet.py, score.py; tests/test_handlabel.py.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import pandas as pd

from phase0.joins import checked_merge

SAMPLE_SIZE = 20
PACKAGE_MEMBER = "AIDev_BC_Analyser/{name}.parquet"


@dataclass(frozen=True, slots=True)
class Candidate:
    """One PR offered for hand-labelling. Carries no outcome and no verdict."""

    pr_id: int
    repo: str  # owner/name
    number: int
    merged_at: str
    title: str
    commit_shas: tuple[str, ...]
    changed_files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Selection:
    """The drawn sample, with the hash that binds labelling to scoring."""

    candidates: tuple[Candidate, ...]
    population: int
    stride: int
    manifest_sha256: str = field(default="")

    def to_manifest(self) -> str:
        """Stable JSON of the draw. Any change to the sample changes the hash."""
        return json.dumps(
            [[c.pr_id, c.repo, c.number] for c in self.candidates],
            sort_keys=True,
            separators=(",", ":"),
        )


def _read(package: Path, name: str) -> pd.DataFrame:
    with zipfile.ZipFile(package) as archive:
        return pd.read_parquet(BytesIO(archive.read(PACKAGE_MEMBER.format(name=name))))


def _repo_full_name(url: str) -> str:
    """`https://api.github.com/repos/owner/name` -> `owner/name`."""
    return "/".join(str(url).rstrip("/").split("/")[-2:])


def select_prs(package: Path, sample_size: int = SAMPLE_SIZE) -> Selection:
    """Draw the sample. Deterministic: same package, same twenty, every time.

    Eligibility is everything the labeller needs to be able to judge at all — merged,
    at least one mined commit, and at least one changed `.py` file. Nothing about
    breakage enters here, and nothing may.
    """
    prs = _read(package, "human_pr_python")
    commits = _read(package, "human_commit")
    details = _read(package, "human_commit_detail")
    # A19's join hazard: `pr_id` ships as a string on both commit tables.
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

    eligible, _ = checked_merge(
        merged,
        evidence,
        on="id",
        how="inner",
        name="merged human PRs x mined evidence",
        # A19 measured 96.8% SHA coverage; this join additionally requires a .py file,
        # so the floor is well below that and is a broken-key tripwire, not a claim.
        minimum_match_rate=0.3,
    )
    eligible = eligible.sort_values("id").reset_index(drop=True)

    population = len(eligible)
    if population < sample_size:
        raise ValueError(
            f"only {population} eligible PRs, need {sample_size}. The gate cannot be "
            f"weakened to fit the corpus — widen eligibility in the pre-registration first."
        )

    stride = population // sample_size
    picked = eligible.iloc[:: max(stride, 1)].head(sample_size)

    candidates = tuple(
        Candidate(
            pr_id=int(row["id"]),
            repo=_repo_full_name(row["repo_url"]),
            number=int(row["number"]),
            merged_at=str(row["merged_at"]),
            title=str(row["title"]),
            commit_shas=tuple(row["sha_list"]),
            changed_files=tuple(row["file_list"]),
        )
        for _, row in picked.iterrows()
    )
    selection = Selection(candidates=candidates, population=population, stride=stride)
    digest = hashlib.sha256(selection.to_manifest().encode("utf-8")).hexdigest()
    return Selection(
        candidates=candidates,
        population=population,
        stride=stride,
        manifest_sha256=digest,
    )
