"""When a merge entered the default branch, and what follows when it never did.

WHAT: `arrival_in_default` -- the committer date at which a merge commit first became
      reachable from the default branch, or None when it is not reachable at all.
WHY:  A PR that merged into a feature branch since deleted cannot have its own window
      walked: the ref is gone. The question is then whether the default branch is a
      defensible substitute, and that turns on WHEN the merge arrived there, not merely
      whether it did. Ancestry says the commit is somewhere in default's history; it says
      nothing about which week, and the window is time-bounded.

      Measured rather than assumed, which is the point of this module existing. The
      expectation on record was that feature branches merge back late and every
      substitution would measure a different week. On four PRs whose base branch was
      deleted, three arrived within MINUTES and the fourth within three and a half days --
      all inside the window. See `docs/engineering/CORRECTIONS.md`.

      None means the merge is not in default's history at all, and there the caller must
      stop: a squash-merged feature branch and an abandoned one are indistinguishable,
      because a squash writes a NEW commit and the PR's own merge sha is absent either
      way. Separating them would mean inferring an arrival date from a content match on a
      diff that may have been modified in the squash, introduced independently, or arrived
      by another path. That is a heuristic dressed as a measurement, so this function
      refuses the guess and `Exclusion.BASE_REF_UNRESOLVABLE` names whose limitation it is.
IMPORTS: stdlib subprocess, datetime, pathlib. Nothing from phase0.
CONSUMED BY: outcome/window.py; tests/outcome/test_arrival.py.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

GIT_TIMEOUT_S = 60


def _git(clone: Path, *args: str) -> str | None:
    """One git call. None on any failure, because a failed call is not an answer."""
    try:
        done = subprocess.run(
            ["git", "-C", str(clone), *args],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout if done.returncode == 0 else None


def sha_absent_from_clone(clone: Path, sha: str) -> bool:
    """True when a full clone holds no such object at all.

    Two of the three legs of the rewritten-history signature are local and are checked
    here: the sha came from GitHub's own PR payload, so GitHub has it, and a FULL clone
    (A31 forbids `--filter`, so this is never shallow) does not. A shallow clone would
    fail this too, which is why the no-partial-clone guard is what makes the inference
    sound rather than a coincidence.

    The third leg -- asking GitHub to resolve the commit -- is deliberately NOT made.
    `scan` runs entirely from a local clone and consumes no quota, which is a property the
    runbook relies on; adding a per-PR API call here would cost a request for every PR in
    the corpus to confirm something the merge payload already implied. The cost is that a
    garbage sha and a rewritten history are not separated locally, and `merge_commit_sha`
    is only ever populated from GitHub, so the first is not a state this pipeline produces.
    """
    return bool(sha) and _git(clone, "cat-file", "-e", f"{sha}^{{commit}}") is None


def default_ref(clone: Path) -> str | None:
    """The clone's default branch, from origin's own HEAD rather than a guessed name."""
    out = _git(clone, "symbolic-ref", "refs/remotes/origin/HEAD")
    return out.strip().replace("refs/remotes/", "") if out and out.strip() else None


def resolve_deleted_base(
    clone: Path, merge_sha: str, merged: datetime, window_end: datetime
) -> tuple[str | None, str]:
    """Where to walk when the PR's own base branch is gone, or why we cannot.

    Three of the four arms live here; the fourth is the ordinary case where the base ref
    still resolves and this is never called.

        arrived inside the window  -> (default_ref, "")        substitute, and say so
        arrived after the window   -> (None, window_shifted)   default's week is not this PR's
        never arrived              -> (None, unresolvable)     squashed or abandoned, not separable

    Returns the exclusion as a plain string so this module stays free of the enum it
    would otherwise import from `window`, which imports nothing from here.
    """
    default = default_ref(clone)
    if default is None:
        return None, "base_ref_unresolvable"
    arrived = arrival_in_default(clone, merge_sha, default)
    if arrived is None:
        return None, "base_ref_unresolvable"
    # `<=` on the end, and no lower bound: a merge can enter default a second before its
    # own committer date via clock skew, and refusing that would exclude a PR for a
    # timestamp artefact rather than for anything about the repository.
    if arrived <= window_end:
        return default, ""
    return None, "base_ref_window_shifted"


def arrival_in_default(clone: Path, merge_sha: str, default: str) -> datetime | None:
    """When `merge_sha` became reachable from `default`, or None when it never did.

    The last commit on `rev-list --ancestry-path merge_sha..default` is the one that first
    carried it in, and its committer date is the arrival.
    """
    if not merge_sha or not default:
        return None
    if _git(clone, "merge-base", "--is-ancestor", merge_sha, default) is None:
        return None

    walked = _git(clone, "rev-list", "--ancestry-path", f"{merge_sha}..{default}")
    if walked is None:
        return None
    path = walked.split()
    # An empty path means the merge IS the tip of default, so it arrived when it was made.
    stamp = _git(clone, "show", "-s", "--format=%cI", path[-1] if path else merge_sha)
    if not stamp or not stamp.strip():
        return None
    try:
        return datetime.fromisoformat(stamp.strip()).astimezone(timezone.utc)
    except ValueError:
        return None
