"""The table a business asks for: what we commented on, whether it merged, what production said.

WHAT: `table(board, repo)` renders a `store.lifecycle.Board` as text, newest first, with a header
      stating what the numbers are and a line stating when they cannot yet be read as a rate.
      `costs(spend, repo)` renders a `store.costs.Costs` — the same `review` rows read for what
      they SPENT rather than for what became of them. Two views of one population, which is why
      they are one module: a repository's reviews are the subject of both.
WHY:  **THE HONEST HEADLINE IS AN OUTCOME COUNT, NOT A QUALITY SCORE.** This product's findings
      measure 66.7-82.1% wrong across four blind pools, and no dashboard changes that. What this
      table reports instead is what happened: we ranked here, it merged, production said this. That
      is true whether the comment was sharp or banal, and nobody has to grade anything.

      **`thin()` IS RENDERED BEFORE THE ROWS, NOT AFTER.** A dashboard showing "2 of 3 failing"
      invites a conclusion three observations cannot carry, and a caveat under a table is read
      second or not at all. The instrument's own limit goes first.

      **A NEVER-OBSERVED CHANGE RENDERS AS `-`, NOT AS HEALTHY.** An empty cell that reads like
      good news is the silence this codebase exists to refuse: "we did not look" and "we looked and
      it was fine" must not print the same character.
      **THE COST VIEW HAS THREE STATES AND PRINTS THREE SENTENCES.** No reviews, reviews that
      consulted no model, and reviews that spent. The first two both total zero and mean opposite
      things — nothing has run here, versus the ranker ran and deliberately read nothing. A single
      "0" would say the product is free when it has never run.

IMPORTS: store.lifecycle, store.costs. Left of serve, right of store.
CONSUMED BY: `serve/cli.py` behind `quantamind dashboard` and `quantamind cost`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from quantamind.store.costs import Costs, NothingRecorded
from quantamind.store.lifecycle import Board, MergeState, ProdState

MERGE_MARK = {
    MergeState.MERGED: "merged",
    MergeState.OPEN: "open",
    MergeState.CLOSED: "closed",
    MergeState.UNKNOWN: "?",
}
PROD_MARK = {ProdState.HEALTHY: "running", ProdState.FAILING: "FAILING", ProdState.UNKNOWN: "?"}


def _day(stamp: int | None) -> str:
    """A date, or `-` for never observed. **Never a blank that reads as good news.**"""
    if stamp is None:
        return "-"
    return datetime.fromtimestamp(stamp, tz=UTC).strftime("%Y-%m-%d")


def table(board: Board, repo: str) -> str:
    """The dashboard as text. Returns a complete report even when there is nothing in it."""
    lines = [f"QuantaMind — {repo}", ""]
    if not board.rows:
        lines.append("No reviews recorded yet. Nothing has been ranked for this repository.")
        return "\n".join(lines)

    caveat = board.thin()
    if caveat:
        lines += [f"NOT YET READABLE AS A RATE: {caveat}", ""]

    lines.append(
        f"{'PR':>7}  {'commit':<9} {'spoke':<6} {'read':>6}  "
        f"{'merged':<7} {'when':<11} {'production':<10} {'seen'}"
    )
    lines.append("-" * 78)
    for row in board.rows:
        lines.append(
            f"{row.pr_number:>7}  {row.head_sha[:8]:<9} "
            f"{('yes' if row.fired else 'no'):<6} "
            f"{f'{row.read}/{row.units}':>6}  "
            f"{MERGE_MARK[row.merge_state]:<7} {_day(row.merged_at):<11} "
            f"{PROD_MARK[row.prod_state]:<10} {_day(row.prod_observed_at)}"
        )

    lines += [
        "",
        f"{len(board.rows)} reviewed change(s), {board.merged} merged, "
        f"{board.failing} with production reporting a failure.",
        "",
        "`spoke` is whether the ranking fired. `read` is units read of units ranked — the rest",
        "were ranked and deliberately not read, which is a decision and not an oversight.",
        "`-` means never observed. It does not mean healthy.",
    ]
    return "\n".join(lines)


def costs(spend: Costs, repo: str) -> str:
    """What this repository's reviews cost. A complete report even when nothing has spent anything.

    **THE THREE STATES ARE PRINTED AS THREE DIFFERENT SENTENCES.** No reviews at all, reviews that
    consulted no model, and reviews that spent — a single "0" for the first two would say the
    ranker is free when in fact it has never run. `Costs.per_review` raises rather than dividing by
    zero, and that refusal is rendered rather than caught and hidden.

    **THE MEAN IS OVER BILLED REVIEWS AND THE LINE SAYS SO**, because a mean over reviews that
    never called a model understates the cost of the ones that did, and a price has to cover those.
    """
    lines = [f"QuantaMind — cost, {repo}", ""]
    if spend.reviews == 0:
        lines.append("No reviews recorded. Nothing has been ranked for this repository.")
        return "\n".join(lines)
    try:
        per_requests, per_tokens = spend.per_review
    except NothingRecorded:
        lines += [
            f"{spend.reviews} review(s) recorded, none consulted a model.",
            "",
            "There is no cost per review yet. That is not a cost of zero: the ranker ran and",
            "deliberately read nothing, which is a decision the allocator made.",
        ]
        return "\n".join(lines)

    lines += [
        f"{'reviews':>9}  {'billed':>7}  {'requests':>9}  {'tokens in':>10}  {'tokens out':>11}",
        "-" * 54,
        f"{spend.reviews:>9}  {spend.billed:>7}  {spend.requests:>9}  "
        f"{spend.tokens_in:>10}  {spend.tokens_out:>11}",
        "",
        f"Per BILLED review: {per_requests:.2f} request(s), {per_tokens:,.0f} output token(s).",
        f"{spend.reviews - spend.billed} review(s) consulted no model and are excluded from that",
        "mean — including them would understate what a paid review costs.",
    ]
    return "\n".join(lines)
