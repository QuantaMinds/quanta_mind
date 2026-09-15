"""What a pull request is told when we are not going to review it.

WHAT: `not_entitled(why)` returns the comment body for a delivery refused at the entitlement check.
WHY:  **A REFUSAL THAT POSTS NOTHING IS INDISTINGUISHABLE FROM A CLEAN REVIEW.**
      `serve/review/review_delivery.py` returned `Outcome.NOT_ENTITLED` and wrote nothing, so "we
      will not review this" and "we looked and found nothing" arrived on the pull request as the
      same blank space. That is the defect this product exists to refuse, committed by the product
      against its own customers.

      **AND IT IS THE CASE WHERE THE AUTHOR CAN ACTUALLY ACT.** An unreadable diff is our problem;
      an ineligible repository is a decision with a stated rule and a way past it. Telling them
      costs one comment and saves them wondering why the bot went quiet.

      **IT NAMES THE RULE, NEVER THE MECHANISM.** `docs/product/comment-golden-rules.md`: never
      mention our method. The reasons come from `verify/qualification.qualifies()` and are already
      written for a person -- "22 stars, and the free tier needs at least 1000" -- so they are
      quoted rather than re-described.

      **NO VERDICT ON THE CODE APPEARS HERE**, for the same reason `render/blocks/headline.BLIND`
      outranks everything: a review that did not happen must never open with an opinion about code
      nobody read.
IMPORTS: nothing. It is a string.
CONSUMED BY: `serve/review/review_delivery.py`.
"""

from __future__ import annotations

HEADER = "### QuantaMind"

BODY = """{header}

**Not reviewed.** {why}

Nothing below is a verdict on your code — there is nothing below, because this change was not read.

_If this repository should be covered, a paid plan removes the eligibility rules entirely; the free
tier is the one with conditions on it._"""


def not_entitled(why: str) -> str:
    """The comment for a delivery we declined to review, naming the reason it was declined.

    **`why` IS REQUIRED AND MAY NOT BE EMPTY.** A refusal with no reason is the silence this module
    exists to replace, wearing a comment's clothes.
    """
    if not why.strip():
        raise ValueError(
            "a refusal must carry its reason; an unexplained one is silence with a header"
        )
    return BODY.format(header=HEADER, why=why.strip())
