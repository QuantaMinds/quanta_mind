"""The refusal a private repository gets, which is the first thing every paying customer sees.

WHAT: `render/not_entitled.not_entitled`, asserting it explains, offers a way forward, and says
      nothing about how the product works.
WHY:  **THIS IS NOW THE PRODUCT'S MAIN SALES SURFACE, NOT AN ERROR PAGE.** The free tier covers
      public repositories, so every customer who could ever pay arrives here first. It used to say
      "a paid plan removes the eligibility rules entirely; the free tier is the one with conditions
      on it" — accurate, unlinked, and written for whoever wrote the rule rather than the developer
      reading it on their pull request.

      **AND IT IS STILL A CUSTOMER-FACING COMMENT**, so `docs/product/comment-golden-rules.md`
      applies to it exactly as it applies to a review: never mention our method. A refusal that
      leaked "ranked" or "history" would leak it to the population most likely to be evaluating us
      against a competitor.
IMPORTS: quantamind.render.not_entitled.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.render.not_entitled import PRICING, not_entitled

WHY = "installed on the free tier, NOT eligible: the repository is private"


def test_it_says_what_happened_and_why() -> None:
    body = not_entitled(WHY)

    assert "was not reviewed" in body
    assert "private" in body


def test_it_carries_a_way_forward() -> None:
    """A refusal with no next step is a dead end, and this one is reached by every buyer."""
    body = not_entitled(WHY)

    assert PRICING in body
    assert "14-day trial" in body


def test_it_does_not_claim_the_code_is_fine() -> None:
    """Silence and approval must never look alike — the defect this product exists to refuse."""
    body = not_entitled(WHY)

    assert "nothing was read" in body


@pytest.mark.parametrize("leak", ["rank", "history", "budget", "decile", "percentile", "top three"])
def test_it_never_mentions_our_method(leak: str) -> None:
    assert leak not in not_entitled(WHY).lower()


def test_an_empty_reason_is_refused() -> None:
    """A refusal that does not say why is the thing this module exists to prevent."""
    with pytest.raises(ValueError):
        not_entitled("   ")
