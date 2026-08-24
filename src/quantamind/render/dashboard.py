"""The table a business asks for: what we commented on, whether it merged, what production said.

WHAT: `table(board, repo)` renders a `store.lifecycle.Board` as text, newest first, with a header
      stating what the numbers are and a line stating when they cannot yet be read as a rate.
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
IMPORTS: store.lifecycle. Left of serve, right of store.
CONSUMED BY: `serve/cli.py` behind `quantamind dashboard`.
"""

from __future__ import annotations

from datetime import UTC, datetime

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
