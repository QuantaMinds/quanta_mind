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
import time
from dataclasses import dataclass
from pathlib import Path

from quantamind.ingest import reachability
from quantamind.ingest.history import read_touches
from quantamind.rank import firing
from quantamind.rank.order import NothingToRank, rank
from quantamind.render.comment import comment
from quantamind.store import calibration, reviews, schema
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

    forecast: firing.Estimate | None = None
    """How often this repository would be spoken on AT ALL, from its own history.

    **The firing rate is a property of the customer's repository, not of the product** — measured
    6.3% to 31.0% across five repositories. None when nothing was indexed."""


LANGUAGES = ",".join(sorted(REVIEWABLE_SUFFIXES))


def index_repository(clone: Path, repo: str, store_path: Path) -> tuple[sqlite3.Connection, int]:
    """Bring the touch index up to HEAD, extending it when that is provably safe.

    **THE INDEX IS DERIVED, AND EXTENDING IT IS AN OPTIMISATION THAT MUST NOT CHANGE THE ANSWER.**
    Reading the whole history cost 32.1 seconds and 338,907 touches on a 115,776-commit repository,
    on EVERY review, into a store that already held it. The CLI throws its store away so re-reading
    was honest there; the webhook does not.

    **THE CORRECTNESS CONDITION IS ONE-SIDED.** `touches.counts()` filters by `as_of`, so an index
    that reaches further than needed is harmless and one that stops short is invisible — the
    ranking looks entirely normal and is computed against a history that ended early. Every branch
    below therefore prefers a full read when it cannot prove the short one is complete.

    Three outcomes, all reported rather than inferred:

    - no watermark, or the language set changed -> full read. **A suffix added to the product
      leaves every existing index blind to it, and an incremental read would never backfill.**
    - the watermark is no longer an ancestor of HEAD -> full read, history was rewritten.
    - otherwise -> read `<watermark>..HEAD` and append.
    """
    conn = schema.open_store(store_path)
    repo_id = touch_store.ensure_repo(conn, "github.com", repo)
    head = reachability.head_sha(clone)
    mark = touch_store.watermark(conn, repo_id)

    fresh = mark is None or mark[1] != LANGUAGES or not reachability.is_ancestor(clone, mark[0])
    since = "" if fresh else mark[0] if mark else ""
    touches = read_touches(clone, pathspec=PATHSPEC, since=since)

    if fresh:
        if not touches:
            raise NoHistory(
                f"{clone}: no history in any language we read ({', '.join(REVIEWABLE_SUFFIXES)}). "
                f"A ranking needs prior commits; a repository with none is a real answer, "
                f"not an error."
            )
        touch_store.index(conn, repo_id, touches)
        if head:
            touch_store.extend(
                conn, repo_id, (), head_sha=head, languages=LANGUAGES, stamped_at=int(time.time())
            )
    elif head:
        # An empty range is the common case -- nothing new since the last review -- and it still
        # moves the watermark, so a no-op review does not re-read the world next time.
        touch_store.extend(
            conn, repo_id, touches, head_sha=head, languages=LANGUAGES, stamped_at=int(time.time())
        )
    return conn, repo_id


def _coverage(ranking: Ranking) -> float | None:
    """Share of ranked units that were read. None when nothing was ranked.

    None rather than 0.0: "we ranked nothing" and "we ranked things and read none of them" are
    different facts, and storing both as zero would make the second invisible in any average.
    """
    if not ranking.units:
        return None
    return 1.0 - len(ranking.cold()) / len(ranking.units)


def review(
    clone: Path,
    repo: str,
    changed: list[str],
    store_path: Path,
    *,
    as_of: int,
    pr_number: int | None = None,
    head_sha: str = "",
) -> Reviewed:
    """Rank `changed` against `clone`'s history before `as_of`, and render the comment.

    `changed` comes from the caller because at review time it is a GitHub API answer, and in a
    retrospective it is a diff against the base — the same ranking, two sources of the file list.
    """
    if as_of <= 0:
        raise ValueError(f"as_of must be the base commit's timestamp, got {as_of}")

    considered = [p for p in changed if language_of(p) is not Language.UNSUPPORTED]
    skipped = [p for p in changed if language_of(p) is Language.UNSUPPORTED]

    conn, repo_id = index_repository(clone, repo, store_path)
    try:
        if not considered:
            # Every changed file is in a language we do not read. NOT an error and NOT silence:
            # the caller still gets the skipped list so the coverage line can name them.
            return Reviewed(None, Ranking(), (), tuple(skipped))
        scores = touch_store.counts(conn, repo_id, considered, as_of=as_of)
        # **THE REPOSITORY'S OWN TOP DECILE, NOT THIS CHANGE'S.** Without it `fires()` falls back to
        # the absolute threshold the research rejected, which fired on 198 of 200 real changes.
        floor = calibration.baseline(conn, repo_id, as_of=as_of)
        # **WHAT THIS REPOSITORY WOULD ACTUALLY GET.** The firing rate is a property of the
        # customer's history, not of the product: measured 6.3-31.0% across five repositories. A
        # rate quoted from a document is an average nobody receives, so it is computed here.
        forecast = firing.estimate(conn, repo_id, as_of=as_of)

        try:
            ranking = rank(scores, baseline=floor)
        except NothingToRank:
            return Reviewed(None, Ranking(), tuple(considered), tuple(skipped), forecast)

        # **RECORDED BEFORE IT IS RENDERED, AND RECORDED EVEN WHEN WE DO NOT SPEAK.** `review` and
        # `ranked_unit` sat in the schema with zero writers, so the product ranked, posted and kept
        # no record that any of it happened -- which is why "what did it say, and did any of it
        # matter" has never had an answer. A row exists for a silent review too: a ranking that
        # chose not to fire is a decision, and a table holding only the loud ones cannot be asked
        # whether the quiet ones were right.
        if pr_number is not None:
            reviews.record(
                conn,
                repo_id,
                pr_number,
                head_sha,
                ranking,
                at=int(time.time()),
                coverage_pct=_coverage(ranking),
            )
    finally:
        conn.close()

    return Reviewed(comment(ranking), ranking, tuple(considered), tuple(skipped), forecast)
