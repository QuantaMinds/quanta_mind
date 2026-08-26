"""Resolve each benchmark pull request in a clone and render the shape block for it.

WHAT: `gather(pulls, root)` returns `{key: context}` for every pull request, holding ONE clone at
      a time. `head_of` places a pull request's head and base; `context_for` renders it.
WHY:  **SPLIT OUT BECAUSE `shape_context.py` CROSSED THE 200-LINE CAP**, and because obtaining a
      pull request's shape and scoring an A/B are two concerns. This half is the one that touches
      the disk and the one that was wrong: it read the clone's HEAD instead of the pull request,
      kept every repository resident, and leaked a failed clone.

      **PEAK DISK IS ONE REPOSITORY, NOT THEIR SUM.** `ensure()` was called per PULL against a root
      swept once at the start, so all five repositories of this corpus stayed resident -- about
      4.5 GB. Grouping by repository and dropping each clone before the next makes the peak the
      largest single one. Free space is checked BEFORE each clone and the run refuses rather than
      filling the disk; this project has filled a 228 GB disk with clones once already.

      **THE CLEANUP PATH DOES NOT DEPEND ON THE CLONE SUCCEEDING.** Binding it to `ensure()`'s
      return value left 997 MB of a half-fetched discourse behind on a machine with 2 GB free.
IMPORTS: stdlib; the product's `ingest.change_shape`, `render.shape_line`, `serve.working_clone`.
CONSUMED BY: `bench/forensic/shape_context.py`.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[4] / "src"))

from quantamind.ingest.change_shape import shape  # noqa: E402
from quantamind.render.shape_line import block  # noqa: E402
from quantamind.serve.working_clone import CloneFailed, ensure, path_for  # noqa: E402


class OutOfDisk(RuntimeError):
    """Refused to clone because the volume would not hold it. Never a partial run."""


GIT_TIMEOUT_S = 300

NEED_GB = 3.0
"""Free space required before each clone. The largest single repository here is grafana at about
1.9 GB plus its pull refs; at 2.5 keycloak started with exactly nothing to spare."""

CLONE_TIMEOUT_S = 2700
"""45 minutes. grafana timed out at the product's 900s default mid-clone and cost that run its
ten pull requests. The bench has no user waiting on it, so it waits."""


def _free_gb(path: pathlib.Path) -> float:
    """Free space where the clones go, in GB. Checked BEFORE each clone, never after."""
    stat = os.statvfs(path)
    return stat.f_bavail * stat.f_frsize / 1_000_000_000


class Unresolved(RuntimeError):
    """A pull request's head could not be placed in the clone. Counted, never silently skipped."""


def _git(clone: pathlib.Path, args: list[str]) -> str:
    done = subprocess.run(
        ["git", "-C", str(clone), *args], capture_output=True, text=True, timeout=GIT_TIMEOUT_S
    )
    return done.stdout.strip() if done.returncode == 0 else ""


def head_of(clone: pathlib.Path, number: int) -> tuple[str, str, list[str]]:
    """(head sha, base sha, changed paths) for pull request `number`, resolved in `clone`.

    **THE PULL REQUEST, NOT THE CLONE'S HEAD.** The first version of this file read
    `git log -1` -- the tip of the default branch -- and handed the model the shape of whatever
    had merged most recently while asking it to review a completely unrelated diff. Both arms
    would have received noise, WITH_SHAPE would have scored like PLAIN, and the run would have
    been recorded as "shape does not help" with the instrument never having pointed at the change.
    `working_clone.ensure()` fetches `+refs/pull/*/head:refs/remotes/pull/*`, so the head is
    already on disk under `refs/remotes/pull/<number>`; nothing new is fetched here.
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


def gather(pulls: list[dict[str, object]], root: pathlib.Path) -> dict[str, str]:
    """`{key: shape block}` for every pull request, one clone resident at a time."""
    # **PHASE ONE IS THE ONLY PART THAT NEEDS DISK, AND IT HOLDS ONE CLONE AT A TIME.**
    # The corpus is cal.com, discourse, grafana, keycloak and sentry -- about 4.5 GB packed if
    # they are all resident, which they were: `ensure()` was called per PULL against a root swept
    # once at the start, so every repository the run touched stayed until the end. Grouping by
    # repository and dropping the clone before the next one makes peak disk the LARGEST SINGLE
    # repository (grafana, ~1.9 GB) instead of their sum. Model calls need no clone, so they are
    # phase two and run after the disk is given back.
    by_repo: dict[str, list[dict[str, object]]] = {}
    for pull in pulls:
        by_repo.setdefault("/".join(str(pull["original"]).split("/")[3:5]), []).append(pull)

    contexts: dict[str, str] = {}
    for repo, group in by_repo.items():
        free = _free_gb(root)
        if free < NEED_GB:
            # **REFUSE RATHER THAN FILL THE DISK.** This project has filled a 228 GB disk with
            # clones once already; a run that dies at 100% takes the machine with it.
            print(f"\n  ABORTING: {free:.1f} GB free, need {NEED_GB} GB for {repo}", flush=True)
            print("  Free space or set QUANTAMIND_BENCH_CLONES to a volume with room.")
            raise OutOfDisk(f"{free:.1f} GB free, need {NEED_GB} GB for {repo}")
        print(f"\n  {repo}: {len(group)} pull request(s), {free:.1f} GB free", flush=True)
        # **THE PATH IS COMPUTED BEFORE THE CLONE, NOT RETURNED BY IT.** Binding it to `ensure()`'s
        # return value means a raised `CloneFailed` leaves the variable unset and the `finally`
        # cleans up nothing -- which is exactly what happened on the first live run: discourse
        # failed mid-fetch and left 997 MB behind, on a machine with 2 GB free. A cleanup that
        # only runs on the success path is not a cleanup.
        where = path_for(repo, root)
        try:
            clone = ensure(repo, root, clone_timeout_s=CLONE_TIMEOUT_S)
            for pull in group:
                url = str(pull["original"])
                try:
                    contexts[str(pull["key"])] = context_for(clone, url)
                except (Unresolved, ValueError, subprocess.TimeoutExpired) as exc:
                    # Counted, never fatal: one unparseable entry must not discard the other 49.
                    print(f"    {url[-40:]}: NO CONTEXT — {type(exc).__name__}: {exc}", flush=True)
                    contexts[str(pull["key"])] = ""
        except (CloneFailed, subprocess.TimeoutExpired) as exc:
            print(f"    {repo}: NO CLONE — {type(exc).__name__}: {str(exc)[:70]}", flush=True)
            for pull in group:
                contexts.setdefault(str(pull["key"]), "")
            got = sum(1 for pull in group if contexts.get(str(pull["key"])))
            print(f"    {repo}: {got}/{len(group)} context(s) resolved", flush=True)
        finally:
            # Dropped before the next repository, not swept at some later high-water mark, and
            # dropped whether or not the clone succeeded.
            if where.is_dir():
                shutil.rmtree(where, ignore_errors=True)

    return contexts
