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
import pathlib
import subprocess

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
PER_REPO = 10
PER_REPO_D9 = 15
PER_REPO_D10 = 10
PER_REPO_D13 = 15
MAX_DIFF_CHARS = 120_000
CACHE = pathlib.Path(
    "/private/tmp/claude-501/-Users-dhanu-Documents-SaaS-quanta-mind/"
    "6063c1dc-2654-4975-b12a-47677aad0026/scratchpad/quote_diffs"
)


class FetchFailed(RuntimeError):
    """A gh read that did not exit zero. Never silently an empty result."""


def _gh(args: list[str], accept: str | None = None) -> bytes:
    cmd = ["gh", "api", *args]
    if accept:
        cmd += ["-H", f"Accept: {accept}"]
    p = subprocess.run(cmd, capture_output=True, timeout=180)
    if p.returncode != 0:
        raise FetchFailed(f"gh {args[0]} exited {p.returncode}: {p.stderr[:200]!r}")
    return p.stdout


def pulls(repos: tuple[str, ...] = REPOS, per_repo: int = PER_REPO) -> list[dict[str, object]]:
    """The pre-registered sample: `per_repo` merged pull requests from each repository.

    Sorted by GitHub's default (most recently updated) and filtered to merged. Recency is
    acceptable here BECAUSE nothing in this experiment looks forward -- adjudication asks whether a
    claim is true of the code shown, not whether a fix later returned. The recency rule that voided
    two earlier corpora applies to outcome measurement, and this is not one.
    """
    out: list[dict[str, object]] = []
    for repo in repos:
        raw = _gh([f"repos/{repo}/pulls?state=closed&per_page=40"])
        got = 0
        for pr in json.loads(raw):
            if not pr.get("merged_at") or got >= per_repo:
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
            raise FetchFailed(f"{repo}: no merged pull requests in the first page")
    return out


def diff(repo: str, number: int) -> str:
    """The unified diff, cached. Raises rather than returning an empty string."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{repo.replace('/', '_')}_{number}.diff"
    if path.exists() and path.stat().st_size > 0:
        return path.read_text()[:MAX_DIFF_CHARS]
    text = _gh([f"repos/{repo}/pulls/{number}"], "application/vnd.github.v3.diff").decode(
        "utf-8", "replace"
    )
    if not text.strip():
        raise FetchFailed(f"{repo}#{number}: empty diff at exit 0")
    path.write_text(text)
    return text[:MAX_DIFF_CHARS]


def base_sha(repo: str, number: int) -> str:
    """The commit the pull request was diffed AGAINST.

    `expand.py` walks the ORIGINAL file, so the base is the correct ref. Reading the head would
    silently misalign every expansion by whatever the pull request itself changed.
    """
    obj = json.loads(_gh([f"repos/{repo}/pulls/{number}"]))
    sha = str((obj.get("base") or {}).get("sha") or "")
    if not sha:
        raise FetchFailed(f"{repo}#{number}: no base sha at exit 0")
    return sha


def blob(repo: str, ref: str, path: str) -> list[str] | None:
    """A file's lines at `ref`, or None when it is absent, binary or too large.

    None is returned for a MISSING file and raised for a broken read, because "this pull request
    adds the file" and "GitHub refused us" are different facts and must not share a value.
    """
    cmd = [
        "gh",
        "api",
        f"repos/{repo}/contents/{path}?ref={ref}",
        "-H",
        "Accept: application/vnd.github.raw",
    ]
    p = subprocess.run(cmd, capture_output=True, timeout=120)
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", "replace")
        if "404" in err or "Not Found" in err:
            return None
        raise FetchFailed(f"contents {repo}:{path}@{ref[:8]} exited {p.returncode}: {err[:160]!r}")
    try:
        return p.stdout.decode("utf-8").split("\n")
    except UnicodeDecodeError:
        return None


def root_names(repo: str, ref: str) -> list[str]:
    """Filenames at the repository root at `ref`. Used to find the conventions file."""
    raw = _gh([f"repos/{repo}/contents?ref={ref}"])
    return [str(e.get("name") or "") for e in json.loads(raw) if e.get("type") == "file"]
