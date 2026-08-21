"""The review: rank a pull request's changed files against history, and render what to say.

WHAT: `review(clone, repo, number, store_path, as_of)` reads the pull request's changed files,
      scores each against the repository's own history STRICTLY BEFORE the change, ranks them, and
      returns the comment body — or `None` when the change is not worth speaking on.
WHY:  Every layer this needs was already built and nothing joined them. `quantamind review` exited
      2 and the webhook's work callback logged and returned, so a delivery was authenticated,
      acknowledged and dropped. This is the join.

      **THE BOUND IS THE WHOLE CORRECTNESS ARGUMENT.** Scores come from `as_of`, the pull request's
      base commit time, and `touches.counts` reads a window ending strictly before it. **A
      retrospective that scores a change against history containing that change looks brilliant and
      means nothing**, and it is the leakage the retrospective's own gate exists to catch. The same
      bound applies here for the same reason: at review time the future does not exist yet, so a
      run that used it would be measuring something the product can never do live.

      **NO MODEL RUNS HERE.** This is rank and render. `infer/` and `verify/` are separate layers to
      the right and this file must keep working whether or not they are wired in — the deterministic
      product is what replicated and it does not depend on them.

      **A COMMENT IS `None`, NEVER AN EMPTY STRING.** "Nothing to say" and "something went wrong"
      must not be the same value on the wire.
IMPORTS: ingest.history, rank.order, render.comment, store.{schema,touches}, types. Left
      only; nothing from infer or verify.
CONSUMED BY: `serve/cli.py` and the webhook's work callback in `serve/run_endpoint.py`.
NAMED: `run_review`, not `review`. `types/review.py` already defines `Review`, the webhook's
      decision object, and two modules called `review` in one package is the collision
      `check_module_identity.py` refuses -- a caller cannot tell which one it imported.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from quantamind.ingest.history import read_touches
from quantamind.rank.order import NothingToRank, rank
from quantamind.render.comment import comment
from quantamind.store import schema
from quantamind.store import touches as touch_store
from quantamind.types.change import REVIEWABLE_SUFFIXES, Language, language_of
from quantamind.types.ranking import Ranking

PATHSPEC: tuple[str, ...] = tuple(f"*{s}" for s in REVIEWABLE_SUFFIXES)


class NoHistory(RuntimeError):
    """The clone has no history in any language we read. Distinct from 'nothing to say'."""


@dataclass(frozen=True, slots=True)
class Reviewed:
    """What one review produced. `body` is None when the change is not worth speaking on."""

    body: str | None
    ranking: Ranking
    considered: tuple[str, ...]
    """The changed paths we scored."""

    skipped: tuple[str, ...]
    """Changed paths in a language we do not read. **Named, not dropped** — this is what the
    coverage line reports, and a file that vanishes from both lists is the silence this product
    exists to refuse."""


def _index(clone: Path, repo: str, store_path: Path) -> tuple[sqlite3.Connection, int]:
    """Build the touch index for this repository. The index is derived, never durable."""
    touches = read_touches(clone, pathspec=PATHSPEC)
    if not touches:
        raise NoHistory(
            f"{clone}: no history in any language we read ({', '.join(REVIEWABLE_SUFFIXES)}). "
            f"A ranking needs prior commits; a repository with none is a real answer, not an error."
        )
    conn = schema.open_store(store_path)
    repo_id = touch_store.ensure_repo(conn, "github.com", repo)
    touch_store.index(conn, repo_id, touches)
    return conn, repo_id


def review(
    clone: Path,
    repo: str,
    changed: list[str],
    store_path: Path,
    *,
    as_of: int,
) -> Reviewed:
    """Rank `changed` against `clone`'s history before `as_of`, and render the comment.

    `changed` comes from the caller because at review time it is a GitHub API answer, and in a
    retrospective it is a diff against the base — the same ranking, two sources of the file list.
    """
    if as_of <= 0:
        raise ValueError(f"as_of must be the base commit's timestamp, got {as_of}")

    considered = [p for p in changed if language_of(p) is not Language.UNSUPPORTED]
    skipped = [p for p in changed if language_of(p) is Language.UNSUPPORTED]

    conn, repo_id = _index(clone, repo, store_path)
    try:
        if not considered:
            # Every changed file is in a language we do not read. NOT an error and NOT silence:
            # the caller still gets the skipped list so the coverage line can name them.
            return Reviewed(None, Ranking(), (), tuple(skipped))
        scores = touch_store.counts(conn, repo_id, considered, as_of=as_of)
        # **THE REPOSITORY'S OWN TOP DECILE, NOT THIS CHANGE'S.** Without it `fires()` falls back to
        # the absolute threshold the research rejected, which fired on 198 of 200 real changes.
        floor = touch_store.baseline(conn, repo_id, as_of=as_of)
    finally:
        conn.close()

    try:
        ranking = rank(scores, baseline=floor)
    except NothingToRank:
        return Reviewed(None, Ranking(), tuple(considered), tuple(skipped))

    return Reviewed(comment(ranking), ranking, tuple(considered), tuple(skipped))


def review_commit(clone: Path, repo: str, sha: str, *, deep_project: str = "") -> int:
    """`quantamind review` — rank one commit's files against history strictly before it.

    Prints the comment body, or says plainly that the change is not worth speaking on. **It posts
    nothing**: this is the command a sceptic runs before granting any access, so it reads a clone
    and writes to stdout.
    """
    from tempfile import TemporaryDirectory

    if not (clone / ".git").exists():
        print(f"{clone} is not a git clone; a review reads history and nothing else")
        return 1
    stamp = _timestamp(clone, sha)
    if stamp is None:
        print(f"{sha[:12]} is not in {clone}, or has no reviewable files")
        return 1
    changed, as_of = stamp
    with TemporaryDirectory() as scratch:
        out = review(clone, repo, changed, Path(scratch) / "review.db", as_of=as_of)
    print(
        f"[review] {len(out.considered)} file(s) ranked, {len(out.skipped)} skipped as unsupported"
    )
    if out.body is None:
        print("[review] not worth speaking on — no comment would be posted")
        return 0
    print(out.body)
    if deep_project:
        _deep(clone, sha, out, deep_project)
    return 0


def _deep(clone: Path, sha: str, out: Reviewed, project: str) -> None:
    """The reviewer pass, printed with its discards. Never raises into the ranking's result."""
    from quantamind.infer.gemini import InferenceFailed, Unavailable
    from quantamind.serve.deep_review import deep

    ranked = [u.unit.site.path for u in out.ranking.units if u.allocation.value != "cold"]
    try:
        result = deep(clone, sha, ranked, project=project)
    except (Unavailable, InferenceFailed) as exc:
        # The ranking already printed and is not retracted by an inference failure.
        print(f"\n[deep] NOT RUN: {type(exc).__name__}: {exc}")
        return
    print(f"\n[deep] read {len(result.read)} ranked file(s)")
    print(
        f"[deep] {result.raw} raw finding(s); {result.unanchored} dropped — quote not in the diff"
    )
    for f in result.anchored:
        print(f"  {f.path}:{f.line}  {f.claim}")
    if not result.anchored:
        print("  (nothing survived the anchor check)")
    print("[deep] RAW FINDINGS MEASURE 66.7-82.1% WRONG. Anchored is not verified true.")


def _timestamp(clone: Path, sha: str) -> tuple[list[str], int] | None:
    """The reviewable files a commit changed, and its time. None when the commit is unknown."""
    import subprocess

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
