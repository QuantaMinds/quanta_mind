"""Resolve each benchmark pull request in a clone and render the shape block for it.

WHAT: `gather(pulls, root)` returns `{key: context}` for every pull request, holding ONE clone at
      a time. `head_of` places a pull request's head and base; `context_for` renders it.
WHY:  The half that touches the disk, and the half that kept being wrong: it read the clone's
      HEAD not the pull request, kept every repository resident, and leaked a failed clone.

      **PEAK DISK IS ONE REPOSITORY, NOT THEIR SUM**, free space is checked BEFORE each clone
      rather than after, and the cleanup runs from `finally` so it does not depend on the clone
      succeeding -- that last one left 997 MB of a half-fetched discourse on a 2 GB machine.
      **TWIN, EDIT BOTH:** `research/phase0/bench/forensic/shape/pulls.py`
      → `scripts/measure/README.md` “Duplicated across the boundary”
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
sys.path[:0] = [str(HERE.parents[2] / "src"), str(HERE)]  # product, then siblings

from pull_shape import Unresolved, context_for  # noqa: E402
from tally import pull_numbers  # noqa: E402  -- sibling; see README

from quantamind.serve.working_clone import CloneFailed, ensure, path_for  # noqa: E402


class OutOfDisk(RuntimeError):
    """Refused to clone because the volume would not hold it. Never a partial run."""


GIT_TIMEOUT_S = 300

NEED_GB = 3.0
"""Free space required before each clone. grafana is ~2.3 GB with its pull refs; at 2.5 keycloak
started with nothing to spare."""

CLONE_TIMEOUT_S = FETCH_TIMEOUT_S = 2700
"""45 minutes each, and **THE FETCH NEEDS IT MORE THAN THE CLONE DOES**: `ensure()` clones, then
RECURSES, and the recursion takes the fetch branch -- where every `refs/pull/*` ref arrives, since
a plain clone does not fetch them. Raising only the clone timeout fixed nothing; grafana's clone
succeeded at 2.3 GB and the fetch behind it died on the 300s default."""


def _free_gb(path: pathlib.Path) -> float:
    """Free space where the clones go, in GB. Checked BEFORE each clone, never after."""
    stat = os.statvfs(path)
    return stat.f_bavail * stat.f_frsize / 1_000_000_000


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
            # Ask for the pull heads this group needs, not every one in the repository.
            clone = ensure(
                repo,
                root,
                clone_timeout_s=CLONE_TIMEOUT_S,
                fetch_timeout_s=FETCH_TIMEOUT_S,
                pull_refs=pull_numbers(group),
            )
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
        finally:
            # **REPORTED FROM `finally`, SO IT PRINTS ON EVERY PATH.** The first version of this
            # line sat in the `except` block and therefore announced coverage only when the clone
            # FAILED -- silent on success, which is the one case a reader watches for. Ask what a
            # check prints when the thing it checks is working: if the answer is "nothing", it is
            # not a check.
            got = sum(1 for pull in group if contexts.get(str(pull["key"])))
            print(f"    {repo}: {got}/{len(group)} context(s) resolved", flush=True)
            # Dropped before the next repository, not swept at some later high-water mark, and
            # dropped whether or not the clone succeeded.
            if where.is_dir():
                shutil.rmtree(where, ignore_errors=True)

    return contexts
