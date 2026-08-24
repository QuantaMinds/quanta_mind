"""The table a customer reads, and the two ways it could mislead them.

WHAT: Renders a board and asserts the caveat precedes the rows, and that a change nobody observed
      in production renders as `-` rather than as anything resembling good news.
WHY:  **A CAVEAT UNDER A TABLE IS READ SECOND OR NOT AT ALL.** "2 of 3 failing" invites a
      conclusion three observations cannot carry, so the instrument's own limit is rendered first
      and this asserts the ORDER, not merely the presence.

      **AN EMPTY CELL THAT READS AS HEALTHY IS THE SILENCE THIS CODEBASE REFUSES.** "We did not
      look" and "we looked and it was fine" must not print the same character.
IMPORTS: stdlib, quantamind.render.dashboard, quantamind.store.lifecycle.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.render.dashboard import table
from quantamind.store.lifecycle import Board, MergeState, ProdState, Row


def row(n: int, prod: ProdState, seen: int | None) -> Row:
    return Row(
        review_id=n,
        pr_number=n,
        head_sha=f"sha{n}aaaaaa",
        fired=True,
        units=9,
        read=3,
        posted_at=1,
        merge_state=MergeState.MERGED,
        merged_at=2,
        prod_state=prod,
        prod_observed_at=seen,
    )


def test_the_caveat_is_rendered_before_the_rows() -> None:
    out = table(Board((row(1, ProdState.FAILING, 5),)), "a/b")
    assert "NOT YET READABLE AS A RATE" in out
    assert out.index("NOT YET READABLE") < out.index("PR"), (
        "the limit must precede the table; a caveat below it is read second or not at all"
    )


def test_never_observed_renders_as_a_dash_and_not_as_healthy() -> None:
    out = table(Board((row(1, ProdState.UNKNOWN, None),)), "a/b")
    assert "running" not in out.split("`-` means")[0], "never-observed must not read as running"
    assert "-" in out
    assert "`-` means never observed. It does not mean healthy." in out


def test_an_empty_board_is_a_complete_report_not_a_blank() -> None:
    out = table(Board(()), "a/b")
    assert "No reviews recorded yet" in out
    assert "a/b" in out


def test_a_readable_board_drops_the_caveat_and_keeps_the_counts() -> None:
    """The control. Without it the renderer could pass by always printing the caveat."""
    rows = tuple(row(n, ProdState.HEALTHY, 5) for n in range(1, 25))
    out = table(Board(rows), "a/b")
    assert "NOT YET READABLE" not in out
    assert "24 reviewed change(s), 24 merged, 0 with production reporting a failure." in out
