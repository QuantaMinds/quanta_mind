"""Which pull-request heads to fetch, and which of them the remote actually has.

WHAT: `refspecs(pull_refs)` maps pull numbers to git refspecs; `present(where, pull_refs, ...)`
      returns the subset the remote really carries, asked in one `ls-remote` that moves no objects.
WHY:  **A PULL HEAD IS ON NO BRANCH OF THE UPSTREAM REPOSITORY WHEN THE PULL REQUEST CAME FROM A
      FORK**, so a plain fetch does not have the commit under review and the whole delivery ranks
      the wrong history. `refs/pull/<n>/head` is how the head becomes reachable.

      **AN EXPLICIT REFSPEC IS STRICT AND A WILDCARD IS NOT.** A pull head that does not exist
      fails the WHOLE fetch -- `fatal: couldn't find remote ref`, exit 128 -- where the wildcard
      quietly matched whatever was there. So `present()` asks before the fetch commits to a list.

      **PULL HEADS LAND IN `refs/remotes/pull/*`, NOT UNDER `refs/remotes/origin/`.** They used to
      map to `refs/remotes/origin/pr/*`, which collides with any branch actually named `pr/<x>`:
      git refuses the whole fetch with `fatal: Cannot fetch both refs/heads/pr/1 and
      refs/pull/1/head to refs/remotes/origin/pr/1`. It is not hypothetical -- discourse/discourse
      has such a branch, and the clone failed on it every time. A separate namespace cannot
      collide with a branch whatever the customer names it.

      **NARROWING IS NOT A ROUNDING ERROR.** grafana carries **83,202** pull-head refs and
      home-assistant/core 105,913; a review needs ONE. Fetching all of them timed out at 900s,
      then ran 25 minutes and exited 1 at 2700s. `None` keeps the wildcard so a caller that does
      not ask is unaffected; an empty sequence fetches branches only.
IMPORTS: stdlib only. The environment is passed in, because the credential is the caller's.
CONSUMED BY: `serve/working_clone.py`.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

from quantamind.types.deployment import Destination, permit


def refspecs(pull_refs: Sequence[int] | None) -> list[str]:
    """Refspecs for the pull heads asked for. None means every one, which is the old behaviour."""
    if pull_refs is None:
        return ["+refs/pull/*/head:refs/remotes/pull/*"]
    return [f"+refs/pull/{n}/head:refs/remotes/pull/{n}" for n in pull_refs]


def present(
    where: Path, pull_refs: Sequence[int], timeout_s: int, env: dict[str, str]
) -> list[int]:
    """The subset of `pull_refs` the remote actually has. Empty in, empty out.

    On a failed `ls-remote` this returns the list unchanged rather than guessing: the fetch that
    follows reports the real failure, where a silently emptied list would review the wrong commit.
    """
    if not pull_refs:
        return []
    # **ASK BEFORE GIT REACHES THE REMOTE.** D7f: air-gapped permits the clone and refuses
    # everything else, rather than attempting it and failing where only the customer sees.
    permit(Destination.GIT_REMOTE)
    done = subprocess.run(
        [
            "git",
            "-C",
            str(where),
            "ls-remote",
            "origin",
            *(f"refs/pull/{n}/head" for n in pull_refs),
        ],
        capture_output=True,
        text=True,
        timeout=timeout_s,
        env=env,
    )
    if done.returncode != 0:
        return list(pull_refs)
    have = {
        line.split("refs/pull/")[1].split("/")[0]
        for line in done.stdout.splitlines()
        if "refs/pull/" in line
    }
    return [n for n in pull_refs if str(n) in have]
