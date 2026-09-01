"""The line that says what we did not look at, and why. It comes first in every comment.

WHAT: `coverage_line()` turns a `Ranking` and its unresolved records into one paragraph naming what
      was ranked, what was read, what was not, and the reason.
WHY:  **The residual is the product.** Every competitor publishes what it found; none publishes what
      it could not see. A reviewer that goes quiet on a file is indistinguishable from one that read
      it and found nothing, and that ambiguity is what this line exists to remove.

      **It differs per case, and that is gate 2c.** A discriminating change, a flat-history change
      and a no-history change each produce a materially different line, because a line that reads
      the same whatever happened is decoration — it would be equally convincing if the ranker had
      not run at all.

      **It names the actual files and the actual constructs**, never a count alone. "1 file not
      read" is unfalsifiable; "not read: src/pay/ledger.py" can be checked against the diff by the
      person reading it.

      **A no-history change says so in the first clause.** That slice misses most — 4.46% against
      1.21% overall — and it is the one where a silent comment would most mislead.
IMPORTS: types (Discrimination, Ranking, Unresolved). Nothing to its right.
CONSUMED BY: render.comment, which puts it first.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.types.ranking import Discrimination, Ranking
from quantamind.types.verdict import Unresolved

MAX_NAMED = 5


class NothingToReport(ValueError):
    """`coverage_line()` was given a ranking with no units at all.

    Raised rather than returning a bland sentence. A coverage line over zero files would claim we
    looked at a change and found nothing to say, which is exactly the false reassurance this line
    exists to prevent. A change with no rankable files is recorded by the caller as its own outcome.
    """


def _names(paths: Sequence[str]) -> str:
    """The paths themselves, truncated with an honest remainder rather than a bare count."""
    shown = list(paths[:MAX_NAMED])
    rest = len(paths) - len(shown)
    joined = ", ".join(f"`{p}`" for p in shown)
    return f"{joined} and {rest} more" if rest else joined


def coverage_line(ranking: Ranking, unresolved: Sequence[Unresolved] = ()) -> str:
    """One paragraph: what was ranked, what was read, what was not, and why."""
    if not ranking.units:
        raise NothingToReport(
            "coverage_line() received a ranking with no units. A change with no rankable files "
            "must be recorded as its own outcome, not rendered as a review that found nothing"
        )

    all_paths = [u.unit.qualified_name for u in ranking.units]
    funded = [u.unit.qualified_name for u in ranking.funded()]
    unread = [p for p in all_paths if p not in set(funded)]
    total = len(all_paths)

    if total == 1 and ranking.discrimination is not Discrimination.NO_HISTORY:
        # A single file is not a failed ranking. Real output said "All 1 file(s) have the same
        # prior-fix history, so the ranking could not separate them and the order below is
        # alphabetical" -- there is nothing to separate, and the sentence reads as a malfunction.
        unit = ranking.units[0]
        head = (
            f"This change touches one file, `{unit.unit.qualified_name}`, which a later fix has "
            f"returned to {int(unit.score.value)} time(s) in the year before it. There is nothing "
            f"to rank."
        )
    elif ranking.discrimination is Discrimination.NO_HISTORY:
        head = (
            f"**No file in this change has prior history in this repository**, so nothing was "
            f"ranked and nothing was prioritised. All {total} file(s) are unread by us: "
            f"{_names(unread)}. Changes like this are where a later fix returns most often "
            f"(4.46% against 1.21% overall), so read them yourself."
        )
    elif ranking.discrimination is Discrimination.FLAT_NONZERO:
        touches = int(ranking.units[0].score.value)
        head = (
            f"All {total} file(s) have the same prior-fix history ({touches} touch(es) each), so "
            f"the ranking could not separate them and the order below is alphabetical. "
            f"Read: {_names(funded)}."
        )
        if unread:
            head += f" Not read: {_names(unread)}."
    else:
        head = (
            f"Ranked {total} file(s) by prior-fix history and read the top {len(funded)}: "
            f"{_names(funded)}."
        )
        head += f" Not read: {_names(unread)}." if unread else " Nothing was left unread."

    # Only news when the ranking DID separate things. A flat-history change has already said its
    # order is alphabetical, and repeating it reads as a stutter rather than a disclosure.
    tied = ranking.boundary_tie() if ranking.discrimination is Discrimination.ORDERED else ()
    if tied:
        names = _names([u.unit.qualified_name for u in tied])
        head += (
            f" **The budget cut through a tie**: {names} scored the same as the last file we read, "
            f"and which of them we read was decided alphabetically, not by history."
        )

    # **THIS SENTENCE USED TO SAY "below the threshold TO COMMENT ON", WHILE COMMENTING.** It was
    # written when `render/comment.py` returned None below the decile, so the reader never saw it
    # in that state; once every change got a comment it became a contradiction printed on real
    # output. `render/comment._salience()` now states the decile, so this says only what is left
    # to say -- that the positions are ordering rather than a claim about risk.
    if not ranking.fired:
        head += " The positions below are an ordering; no risk claim is made about any of them."

    if unresolved:
        head += (
            f" {len(unresolved)} construct(s) could not be parsed and are outside everything "
            f"above: " + "; ".join(u.render() for u in unresolved[:MAX_NAMED])
        )
    return head
