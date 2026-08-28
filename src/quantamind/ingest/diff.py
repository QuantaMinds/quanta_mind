"""The files a pull request changed, and the commit its ranking must be bounded by.

WHAT: `changed_files()` returns the paths a pull request touches, and `base_commit()` returns the
      commit it was opened against, with the timestamp the ranking window ends at.
WHY:  Until now the live tests fetched this with `gh` by hand, which meant the product could not
      rank a pull request without help and the seam nobody had exercised was the one that decides
      **which commit bounds the window**.

      **The base commit, never the head.** Ranking against the head would count the pull request's
      own commits as prior history — the change would raise its own score, and the more a branch
      touched a file the more important that file would appear. It is the leak the whole store is
      built to prevent, arriving one layer earlier.

      **A pull request whose base is absent from the clone is a REFUSAL, not a zero.** It happens
      with forks and force-pushed branches, and guessing a timestamp would produce a ranking bounded
      by the wrong instant with nothing to show it.

      **Removed files are excluded, added and modified are kept.** A file the change deletes has a
      history and no future; ranking it wastes budget on something no reviewer can read.
IMPORTS: types (nothing else). Shells out to `gh`, like every other read in this layer.
CONSUMED BY: rank, via the caller that owns a review; the live tests, which no longer hand-fetch.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from quantamind.ingest import github_api
from quantamind.types.change import REVIEWABLE_SUFFIXES

# Declared, not defaulted: a GitHub read is a network call and 30s is the house default.
API_TIMEOUT_S = 30
GIT_TIMEOUT_S = 60
PER_PAGE = 100
MAX_PAGES = 10
# Statuses whose file still exists after the change. "removed" is dropped: it has a history and no
# future, and funding it spends budget on something nobody can open.
KEPT_STATUSES = frozenset({"added", "modified", "changed", "renamed", "copied"})


class DiffReadFailed(RuntimeError):
    """A pull request read that did not complete. Never silently an empty file list.

    An empty list is a legitimate answer — a change touching no source at all — so a failure must
    not be able to produce one. This project has already conflated "we failed" with "there is
    nothing here" once, and counted the failures as repositories that did not qualify.
    """

    def __init__(self, repo: str, number: int, reason: str) -> None:
        self.repo, self.number, self.reason = repo, number, reason
        super().__init__(f"{repo}#{number}: {reason}")


@dataclass(frozen=True, slots=True)
class Base:
    """The commit a pull request was opened against, and when it landed."""

    sha: str
    committed_at: int


def _read(repo: str, number: int, path: str, accept: str = github_api.JSON) -> bytes:
    """One authenticated read, with the failure re-raised as this module's own error.

    **THIS USED TO BE `gh api`, AND THAT IS WHY THE ENDPOINT ONLY EVER RAN ON A LAPTOP.**
    `changed_files()` and `base_commit()` are on the webhook's delivery path, so the product needed
    a `gh` CLI authenticated as a PERSON to read a pull request. In a container there is no
    `gh auth login` and every delivery would have failed.
    """
    try:
        return github_api.call(repo, path, accept=accept)
    except github_api.ApiFailed as exc:
        raise DiffReadFailed(repo, number, str(exc)) from None


def _gh(repo: str, number: int, path: str) -> object:
    raw = _read(repo, number, path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DiffReadFailed(repo, number, f"GET {path} returned non-JSON: {exc}") from None


def changed_files(
    repo: str, number: int, suffixes: tuple[str, ...] = REVIEWABLE_SUFFIXES
) -> list[str]:
    """Paths the pull request changed that still exist afterwards, sorted.

    Returns `[]` only when the change genuinely touches no matching file. Every failure raises.
    """
    out: list[str] = []
    for page in range(1, MAX_PAGES + 1):
        got = _gh(
            repo, number, f"repos/{repo}/pulls/{number}/files?per_page={PER_PAGE}&page={page}"
        )
        if not isinstance(got, list):
            raise DiffReadFailed(repo, number, f"files page {page} was {type(got).__name__}")
        if not got:
            break
        for entry in got:
            if not isinstance(entry, dict):
                raise DiffReadFailed(repo, number, "a files entry was not an object")
            name = str(entry.get("filename") or "")
            status = str(entry.get("status") or "")
            if not name or not status:
                raise DiffReadFailed(repo, number, f"a files entry lacked filename/status: {entry}")
            if name.endswith(suffixes) and status in KEPT_STATUSES:
                out.append(name)
        if len(got) < PER_PAGE:
            break
    else:
        raise DiffReadFailed(
            repo,
            number,
            f"more than {MAX_PAGES * PER_PAGE} files; refusing to "
            "rank a change this size on a truncated list",
        )
    return sorted(set(out))


def unified_diff(repo: str, number: int) -> str:
    """The pull request's patch, for `parse/` to read hunk headers out of.

    Raises rather than returning an empty string: `git log -p` on a blob-filtered clone exits
    non-zero AND emits a truncated patch, and the same shape of failure through the API would
    otherwise read as a change that touched nothing.
    """
    # `_read` raises on any non-2xx, so reaching here means the request succeeded. The emptiness
    # check below is the one that matters and it survives the move off the `gh` CLI unchanged.
    patch = _read(repo, number, f"repos/{repo}/pulls/{number}", "application/vnd.github.v3.diff")
    text = patch.decode("utf-8", "replace")
    if not text.strip():
        raise DiffReadFailed(
            repo,
            number,
            "the patch was empty on a successful read, which a real change "
            "never is — treat this as a failed read, not a no-op",
        )
    return text


@dataclass(frozen=True, slots=True)
class Stated:
    """What the author SAYS the change is for. The claim a review is measured against."""

    title: str
    body: str

    def text(self) -> str:
        """Title and body as one block, or an empty string when the author wrote neither."""
        return f"{self.title}\n\n{self.body}".strip()


def stated_goal(repo: str, number: int) -> Stated:
    """The pull request's own description of its purpose.

    **THE REVIEW IS MEASURED AGAINST THIS, SO IT COMES FROM THE AUTHOR AND NOT FROM THE DIFF.**
    "Did this change do what it set out to do" has no meaning without the second half, and
    inferring the intent from the code makes the question circular: a diff always achieves what
    the diff does. An empty description is a real answer — it means the author stated no goal, and
    the review must say so rather than invent one.
    """
    payload = _gh(repo, number, f"repos/{repo}/pulls/{number}")
    if not isinstance(payload, dict):
        raise DiffReadFailed(repo, number, "the pull request payload was not an object")
    return Stated(str(payload.get("title") or ""), str(payload.get("body") or ""))


def base_commit(repo: str, number: int, clone: Path) -> Base:
    """The commit the pull request was opened against, resolved in `clone`.

    Raises when the base is not in the clone. That is a fork or a force-pushed branch, and a
    ranking bounded by a guessed instant is worse than no ranking.
    """
    pull = _gh(repo, number, f"repos/{repo}/pulls/{number}")
    if not isinstance(pull, dict):
        raise DiffReadFailed(repo, number, f"pull payload was {type(pull).__name__}, not an object")
    sha = str((pull.get("base") or {}).get("sha") or "")
    if not sha:
        raise DiffReadFailed(repo, number, "the pull request payload carried no base sha")

    shown = subprocess.run(
        ["git", "-C", str(clone), "show", "-s", "--format=%ct", sha],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_S,
    )
    if shown.returncode != 0:
        raise DiffReadFailed(
            repo,
            number,
            f"base commit {sha[:10]} is not in {clone.name} — a fork or a force-pushed branch. "
            "Refusing to guess a bound; a ranking against the wrong instant looks identical to a "
            "correct one",
        )
    return Base(sha=sha, committed_at=int(shown.stdout.strip().split("\n")[-1]))
