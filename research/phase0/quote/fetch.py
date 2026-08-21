"""Fetch one artefact from a repository: a diff, a base SHA, a blob, a root listing.

WHAT: `diff()`, `base_sha()`, `blob()` and `root_names()`, each cached on disk, plus the `gh` call
      and the `FetchFailed` they all raise.
WHY:  **Split from `corpus.py` at the 200-line cap, on the seam between WHICH pull requests a design
      measures and HOW one of them is fetched.** The literals in `corpus.py` are pre-registered and
      must never move to fit a result; nothing here is a study parameter at all. Keeping them in one
      file meant every edit to a fetch helper touched the module whose whole point is being fixed.

      `corpus.py` re-exports all four names, so designs nine through fourteen import exactly what
      they always did and their runs stay reproducible.
IMPORTS: stdlib only (json, pathlib, subprocess).
CONSUMED BY: `corpus.py`, which re-exports these; `run9.py` through `run14.py` via that.
"""

from __future__ import annotations

import json
import pathlib
import subprocess

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
