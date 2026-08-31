"""Place one pull request in a clone and render its shape block.

WHAT: `head_of` resolves a pull request's head and base and the files it changed; `commit_of`
      does the same for a bare commit URL; `context_for` renders the shape block for either.
WHY:  Split from `pulls.py`, which owns clone CUSTODY -- free space, one repository resident at
      a time, cleanup from `finally`. This owns RESOLUTION, and the two failed differently: this
      half read the clone's HEAD instead of the pull request, that half leaked a half-fetched
      repository. Separating them stops a fix to one being reviewed as a fix to the other, and
      `pulls.py` sat at exactly the 200-line cap until this moved out.

      **TWIN, EDIT BOTH:** `scripts/measure/pull_shape.py`
      → `scripts/measure/README.md` “Duplicated across the boundary”
IMPORTS: stdlib; the product's `ingest.change_shape` and `render.shape_line`.
CONSUMED BY: `pulls.py`.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[4] / "src"), str(HERE)]

from quantamind.ingest.change_shape import shape  # noqa: E402
from quantamind.render.blocks.shape_line import block  # noqa: E402

GIT_TIMEOUT_S = 300


class Unresolved(RuntimeError):
    """A pull request's head could not be placed in the clone. Counted, never silently skipped."""


def _git(clone: pathlib.Path, args: list[str]) -> str:
    done = subprocess.run(
        ["git", "-C", str(clone), *args], capture_output=True, text=True, timeout=GIT_TIMEOUT_S
    )
    return done.stdout.strip() if done.returncode == 0 else ""


def head_of(clone: pathlib.Path, number: int) -> tuple[str, str, list[str]]:
    """(head sha, base sha, changed paths) for pull request `number`, resolved in `clone`.

    **THE PULL REQUEST, NOT THE CLONE'S HEAD.** The first version read `git log -1` -- the tip of
    the default branch -- and handed the model the shape of whatever had merged most recently
    while asking it to review an unrelated diff. Both arms would have got noise, WITH_SHAPE would
    have scored like PLAIN, and the run would have been recorded as "shape does not help" with the
    instrument never pointed at the change. `ensure()` puts the head at
    `refs/remotes/pull/<number>`; nothing new is fetched here.
    """
    head = _git(clone, ["rev-parse", f"refs/remotes/pull/{number}"])
    if not head:
        raise Unresolved(f"refs/remotes/pull/{number} is not in the clone")
    base = _git(clone, ["merge-base", "origin/HEAD", head]) or _git(
        clone, ["rev-parse", f"{head}^"]
    )
    if not base:
        raise Unresolved(f"no merge-base for pull/{number}")
    changed = [x for x in _git(clone, ["diff", "--name-only", f"{base}...{head}"]).split() if x]
    if not changed:
        raise Unresolved(f"pull/{number} changed no files against its base")
    return head, base, changed


def commit_of(clone: pathlib.Path, sha: str) -> tuple[str, list[str]]:
    """(resolved sha, changed paths) for a corpus entry that names a COMMIT rather than a pull.

    **TEN OF THE FIFTY GOLDEN ENTRIES ARE COMMIT URLS, ALL DISCOURSE**, and assuming every entry
    was `/pull/<n>` crashed the run on `int('ffbaf8c5...')`. A commit is the single-commit case
    `change_shape.shape()` was built for, so it takes no `against` range -- passing one would
    measure the commit against its parent twice.
    """
    resolved = _git(clone, ["rev-parse", f"{sha}^{{commit}}"])
    if not resolved:
        raise Unresolved(f"commit {sha[:12]} is not in the clone")
    changed = [x for x in _git(clone, ["show", "--name-only", "--format=", resolved]).split() if x]
    if not changed:
        raise Unresolved(f"commit {sha[:12]} changed no files")
    return resolved, changed


def context_for(clone: pathlib.Path, url: str) -> str:
    """The shape block the product would send for `url`, byte for byte.

    **THE CORPUS MIXES PULL REQUESTS AND BARE COMMITS**, 40 and 10 of the 50, and the two are
    measured differently: a pull request is a RANGE against its merge-base, a commit is itself.
    An entry that is neither raises `Unresolved` and is counted -- it is not silently given an
    empty context, which would make its WITH_SHAPE arm identical to PLAIN and quietly dilute the
    result toward null.

    **IT CALLS `render/shape_line.block()` RATHER THAN REBUILDING THE SENTENCE.** This file used
    to compose its own prose, so a PASS here would have licensed a string the product does not
    send. The arm has to be the shipped artefact or the result does not transfer to it.
    """
    tail = url.rstrip("/").split("/")[-1]
    if "/pull/" in url:
        try:
            number = int(tail)
        except ValueError as exc:
            raise Unresolved(f"pull URL does not end in a number: {url}") from exc
        head, base, changed = head_of(clone, number)
        return block(shape(clone, head, changed, against=base))
    if "/commit/" in url:
        sha, changed = commit_of(clone, tail)
        return block(shape(clone, sha, changed))
    raise Unresolved(f"URL names neither a pull request nor a commit: {url}")
