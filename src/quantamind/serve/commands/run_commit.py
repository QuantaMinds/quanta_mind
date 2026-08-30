"""`quantamind review` — rank one commit from a local clone and print what we would say.

WHAT: `review_commit(clone, repo, sha)` resolves the commit's changed files and timestamp, runs the
      ranking against history strictly before it, and writes the comment to stdout.
WHY:  **THIS IS THE COMMAND A SCEPTIC RUNS BEFORE GRANTING ANY ACCESS.** It reads a clone they
      already have and writes to stdout. No token, no webhook, no network, and nothing posted.

      **IT IS SPLIT FROM `run_review.py` BECAUSE THEY ARE DIFFERENT CONCERNS**, and because that
      file crossed the 200-line cap when reviews began being recorded. `review()` is a library
      function returning a value; this is an entry point that prints and returns an exit code.
      Rule 6: if you need "and" to describe what a file does, split it.
IMPORTS: rank.firing, serve.{deep_review,run_review}, types.change. Rightmost layer.
CONSUMED BY: `serve/cli.py`.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from quantamind.infer.vertex import InferenceFailed, Unavailable
from quantamind.ingest.worktree import NothingPending, pending
from quantamind.rank import firing
from quantamind.render.deep_report import lines

# **ALIASED, BECAUSE `report` IS ALREADY TAKEN IN THIS MODULE.** `deep_review.report` prints the
# model pass; this renders the whole review as data. Two functions of one name in one file is the
# collision rule 13 is about, and here it shadowed silently until the call failed at runtime.
from quantamind.render.json_report import report as json_review
from quantamind.render.json_report import unreviewed
from quantamind.serve.commands.run_review import Reviewed, review
from quantamind.serve.deep_review import deep
from quantamind.types.change import REVIEWABLE_SUFFIXES
from quantamind.types.review import NotReviewed
from quantamind.types.settings import load


def review_commit(
    clone: Path, repo: str, sha: str = "", *, deep_project: str = "", as_json: bool = False
) -> int:
    """`quantamind review` — rank one commit's files against history strictly before it.

    Prints the comment body, or says plainly that the change is not worth speaking on. **It posts
    nothing**: this is the command a sceptic runs before granting any access, so it reads a clone
    and writes to stdout.
    """
    if not (clone / ".git").exists():
        print(f"{clone} is not a git clone; a review reads history and nothing else")
        return 1
    origin = f"commit {sha[:12]}" if sha else ""
    if sha:
        stamp = _timestamp(clone, sha)
        if stamp is None:
            print(f"{sha[:12]} is not in {clone}, or has no reviewable files")
            return 1
        changed, as_of = stamp
    else:
        # **NO COMMIT MEANS THE REVIEW WORTH HAVING: WHAT IS NOT COMMITTED, OR NOT PUSHED.** By the
        # time a pull request exists the developer has stopped and asked other people to look. The
        # cheapest place to be wrong is the machine that made the change.
        try:
            work = pending(clone)
        except NothingPending as why:
            # **JSON EVEN HERE.** A tool asked for JSON; prose plus exit 0 gave it a decode
            # error indistinguishable from a broken install. The reason travels as a value.
            if as_json:
                print(unreviewed(NotReviewed.NOTHING_PENDING, origin=str(why)))
            else:
                print(f"[review] nothing to review — {why}")
            return 0
        origin = work.origin
        if not as_json:
            print(f"[review] reviewing {origin}")
        changed = [p for p in work.paths if p.endswith(REVIEWABLE_SUFFIXES)]
        if not changed:
            if as_json:
                print(
                    unreviewed(NotReviewed.NO_SUPPORTED_LANGUAGE, changed=work.paths, origin=origin)
                )
            else:
                print(
                    f"[review] {len(work.paths)} file(s) changed, "
                    f"{NotReviewed.NO_SUPPORTED_LANGUAGE.sentence()}"
                )
            return 0
        # Scored against history up to now: the change has no commit, so there is no committer
        # date to bound it by, and the honest bound is the moment the review runs.
        as_of = int(time.time())
    with TemporaryDirectory() as scratch:
        out = review(clone, repo, changed, Path(scratch) / "review.db", as_of=as_of)
    if as_json:
        # **ONE OBJECT ON STDOUT AND NOTHING ELSE.** A tool parsing this must not have to strip
        # progress lines out of it first, so the human-facing prints are skipped entirely rather
        # than sent to stderr and hoped about.
        print(json_review(out.ranking, origin=origin))
        return 0
    print(
        f"[review] {len(out.considered)} file(s) ranked, {len(out.skipped)} skipped as unsupported"
    )
    if out.forecast is not None:
        print(f"[review] {out.forecast.sentence()}")
        if out.forecast.selectivity is not firing.Selectivity.SELECTIVE:
            print(f"[review] SELECTIVITY: {out.forecast.selectivity.value.upper()}")
    if out.body is None:
        print("[review] not worth speaking on — no comment would be posted")
        return 0
    print(out.body)
    if deep_project:
        report(clone, sha, out, deep_project, load().gcloud_path)
    return 0


def _timestamp(clone: Path, sha: str) -> tuple[list[str], int] | None:
    """The reviewable files a commit changed, and its time. None when the commit is unknown."""
    done = subprocess.run(
        ["git", "-C", str(clone), "show", "--name-only", "--format=%ct", sha],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if done.returncode != 0:
        return None
    lines = [x for x in done.stdout.splitlines() if x.strip()]
    if not lines:
        return None
    changed = [p for p in lines[1:] if p.endswith(REVIEWABLE_SUFFIXES)]
    return changed, int(lines[0])


def report(clone: Path, sha: str, out: Reviewed, project: str, gcloud: str = "gcloud") -> None:
    """The reviewer pass, printed with its discards. Never raises into the ranking's result.

    **LIVES HERE, NOT IN `deep_review`, BECAUSE IT IS THE CLI'S PRESENTATION.** `deep()` produces
    a reviewer pass; this prints one for a person at a terminal, and the only caller is below.

    **`gcloud` IS THREADED HERE BECAUSE IT WAS THREADED EVERYWHERE ELSE AND MISSED HERE.**
    `examine()` took it from settings for the webhook; this path kept the bare default, so a
    developer whose SDK is not on PATH got "no access token" from the CLI while the endpoint
    worked. Found by running it, and only because the failure named both sources it tried.
    """
    ranked = [u.unit.site.path for u in out.ranking.units if u.allocation.value != "cold"]
    # `considered` are the paths we scored and `skipped` the ones in a language we do not read.
    # Together they are the whole change, which is the population the shape figures describe.
    changed = list(out.considered) + list(out.skipped)
    try:
        result = deep(clone, sha, ranked, project=project, changed=changed, gcloud=gcloud)
    except (Unavailable, InferenceFailed) as exc:
        # The ranking already printed and is not retracted by an inference failure.
        print(f"\n[deep] NOT RUN: {type(exc).__name__}: {exc}")
        return
    print("")
    for line in lines(result):
        print(line)
