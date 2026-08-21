"""Merged pull requests from six repositories this project has never touched, with their diffs.

WHAT: `pulls()` lists merged pull requests per repository via `gh`; `diff()` fetches one, cached.
WHY:  Thirty-two repositories are already burned across the ranker samples, the aged corpus and
      Martian's five. A design measured on a repository that shaped it is a design tuned on its own
      test set, and this project has voided measurements that way twice.

      THE REPOSITORY LIST IS A LITERAL AND MUST STAY ONE. Choosing repositories after seeing a
      result is the same defect as moving a threshold after seeing a number.
IMPORTS: stdlib only (json, pathlib, subprocess).
CONSUMED BY: `run.py` in this package.
"""

from __future__ import annotations

import json

# Re-exported so designs nine through fourteen import the names they always did.
from fetch import CACHE, MAX_DIFF_CHARS, FetchFailed, _gh, base_sha, blob, diff, root_names

__all__ = [
    "CACHE",
    "MAX_DIFF_CHARS",
    "REPOS",
    "REPOS_D9",
    "REPOS_D10",
    "REPOS_D11",
    "REPOS_D13",
    "REPOS_D14",
    "FetchFailed",
    "base_sha",
    "blob",
    "diff",
    "pulls",
    "root_names",
]

# Fixed in the quote-anchor pre-registration before any run. Never edited to fit a result.
# → docs/plans/preregistrations/reviewer/quote-anchor-preregistration.md
REPOS = (
    "apache/superset",
    "ray-project/ray",
    "pydantic/pydantic",
    "fastapi/fastapi",
    "mitmproxy/mitmproxy",
    "PrefectHQ/prefect",
)
# Design nine. Six more repositories, none of the thirty-eight already burned. Fixed in
# docs/plans/preregistrations/reviewer/path-filter-preregistration.md before the run.
REPOS_D9 = (
    "dbt-labs/dbt-core",
    "streamlit/streamlit",
    "dagster-io/dagster",
    "encode/httpx",
    "huggingface/datasets",
    "bokeh/bokeh",
)
# Design ten. Six more, verified unused against the 48 burned. Fixed in
# docs/plans/preregistrations/reviewer/scoring-pass-preregistration.md before the run.
REPOS_D10 = (
    "pallets/quart",
    "aio-libs/aiohttp",
    "tiangolo/sqlmodel",
    "pytest-dev/pytest-asyncio",
    "python-attrs/attrs",
    "psycopg/psycopg",
)
# Design eleven. Six more, verified unused against the 54 burned.
REPOS_D11 = (
    "encode/starlette",
    "Textualize/rich",
    "redis/redis-py",
    "tox-dev/tox",
    "agronholm/anyio",
    "marshmallow-code/marshmallow",
)
# Design thirteen. Six more, each verified absent from every file under research/ before selection,
# each carrying a conventions file. Fixed in
# docs/plans/preregistrations/reviewer/expansion-conventions-preregistration.md before the run.
REPOS_D13 = (
    "pyca/cryptography",
    "falconry/falcon",
    "pytest-dev/pluggy",
    "jazzband/pip-tools",
    "scikit-build/scikit-build-core",
    "aws/aws-cli",
)
# Design fourteen. Six more, each verified at zero prior mentions anywhere under research/ by
# check_burned_corpora.py --check BEFORE selection. Fixed in
# docs/plans/preregistrations/reviewer/design14-model-lever-preregistration.md before the run.
REPOS_D14 = (
    "sqlalchemy/sqlalchemy",
    "python-poetry/poetry",
    "pylint-dev/pylint",
    "urllib3/urllib3",
    "explosion/spaCy",
    "Lightning-AI/pytorch-lightning",
)
PER_REPO = 10
PER_REPO_D9 = 15
PER_REPO_D10 = 10
PER_REPO_D13 = 15
PER_REPO_D14 = 50
# Pagination bound. Stated so a shortfall is the repository's, not an unreported page limit.
MAX_PAGES = 8


def pulls(repos: tuple[str, ...] = REPOS, per_repo: int = PER_REPO) -> list[dict[str, object]]:
    """The pre-registered sample: `per_repo` merged pull requests from each repository.

    Sorted by GitHub's default (most recently updated) and filtered to merged. Recency is
    acceptable here BECAUSE nothing in this experiment looks forward -- adjudication asks whether a
    claim is true of the code shown, not whether a fix later returned. The recency rule that voided
    two earlier corpora applies to outcome measurement, and this is not one.
    """
    out: list[dict[str, object]] = []
    for repo in repos:
        got = 0
        for page in range(1, MAX_PAGES + 1):
            if got >= per_repo:
                break
            raw = _gh([f"repos/{repo}/pulls?state=closed&per_page=100&page={page}"])
            batch = json.loads(raw)
            if not batch:
                break
            for pr in batch:
                if got >= per_repo:
                    break
                if not pr.get("merged_at"):
                    continue
                if (pr.get("changed_files") or 0) > 40:
                    continue
                out.append(
                    {
                        "repo": repo,
                        "number": int(pr["number"]),
                        "title": str(pr.get("title") or ""),
                        "url": str(pr.get("html_url") or ""),
                    }
                )
                got += 1
        if got == 0:
            raise FetchFailed(f"{repo}: no merged pull requests found")
        if got < per_repo:
            # **SAID, NOT SWALLOWED.** This function used to read ONE page of 40 and stop, so any
            # per_repo above ~40 came back short in silence. Design thirteen asked for 90 pull
            # requests and ran on 80; nothing in its output recorded the other ten. A sample that
            # is quietly smaller than the one that was pre-registered is the silent-truncation
            # shape -- it reads as "we covered the corpus" when it did not.
            print(
                f"  [corpus] {repo}: {got} merged pull requests, {per_repo} asked for "
                f"-- the repository does not have more within {MAX_PAGES} pages",
                flush=True,
            )
    return out
