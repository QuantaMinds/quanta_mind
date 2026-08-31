"""The cost report's three states, which must read as three different answers.

WHAT: Drives `render/dashboard.costs` over `Costs` values and asserts what an operator reads.
WHY:  **A REPORT OVER AN EMPTY TABLE LOOKS EXACTLY LIKE A REPORT OVER A BROKEN QUERY.** Both print
      zero. This product's own store root currently holds an owner directory with no database in
      it, so the empty case is the one an operator will actually meet first, and it has to say
      which of the two it is.
IMPORTS: pytest, quantamind.store.costs, quantamind.render.dashboard.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.render.dashboard import costs as table
from quantamind.store.costs import Costs


def test_no_reviews_says_nothing_has_run_not_that_it_was_free() -> None:
    said = table(Costs(reviews=0, billed=0, requests=0, tokens_in=0, tokens_out=0), "acme/widgets")

    assert "No reviews recorded" in said
    assert "0.00 request" not in said, "an empty repository was quoted a cost per review"


def test_reviews_with_no_model_call_are_distinguished_from_no_reviews() -> None:
    """The two zeros. Both total nothing; they mean opposite things."""
    said = table(Costs(reviews=2, billed=0, requests=0, tokens_in=0, tokens_out=0), "acme/widgets")

    assert "2 review(s) recorded, none consulted a model" in said
    assert "not a cost of zero" in said
    assert "No reviews recorded" not in said, "reviews that ran were reported as no reviews at all"


def test_the_mean_shown_is_over_billed_reviews_and_the_line_says_so() -> None:
    said = table(
        Costs(reviews=4, billed=2, requests=4, tokens_in=1000, tokens_out=8000), "acme/widgets"
    )

    assert "Per BILLED review: 2.00 request(s), 4,000 output token(s)." in said, said
    assert "2 review(s) consulted no model and are excluded" in said, (
        "the excluded reviews must be named, or the mean looks like it covers everything"
    )
