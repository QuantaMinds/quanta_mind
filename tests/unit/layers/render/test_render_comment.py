"""The comment body: what a developer is told, and what they are not.

WHAT: Renders real rankings through `render/comment.comment()` and asserts on the text posted to a
      pull request.
WHY:  **SPLIT OUT OF `test_render_coverage.py` AT THE 200-LINE CAP, AND IT IS A REAL SEAM.** That
      file tests `coverage_line()`, which is an internal report; this tests what a customer's
      developer actually reads. They moved apart when the comment stopped explaining the product.

      **THESE TESTS HAVE ASSERTED THREE DIFFERENT PRODUCT DECISIONS**, each recorded in place
      rather than deleted: silence below the decile, then a salience sentence on every change, and
      now neither — because a developer waiting to merge does not act on our firing rate.
IMPORTS: render.comment, rank.order, types.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.rank.order import rank
from quantamind.render.comment import LOOK, comment

CASES = {
    "ordered": {"a.py": 40, "b.py": 12, "c.py": 3, "d.py": 1},
    "no_history": {"src/new/mod.py": 0, "src/new/__init__.py": 0, "tests/test_new.py": 0},
}


def test_a_change_below_the_threshold_is_still_commented_on() -> None:
    """**THIS TEST HAS NOW ASSERTED THREE DIFFERENT PRODUCT DECISIONS, AND THAT IS RECORDED.**

    First it required `None` below the decile, when the product spoke on about a tenth of changes.
    Then it required a salience sentence, when every change got a comment and the loud ones had to
    stay distinguishable. Now it requires neither: the comment says where to look and what was not
    reviewed, and says nothing about deciles, because a developer waiting to merge does not act on
    our firing rate. The signal still exists on `Ranking.fired` and still reaches the dashboard.
    """
    ranking = rank(CASES["no_history"])
    body = comment(ranking)

    assert body, "a change below the decile must still be commented on"
    assert "decile" not in body and "%" not in body, (
        f"the comment is explaining the product to a reviewer again: {body!r}"
    )
    assert "reviewed" in body, "the reader must still learn how much of their change was read"


def test_a_change_the_budget_cannot_help_with_is_not_spoken_on() -> None:
    """**A one-file change is spoken on again, and the reason is a different product.**

    `read = min(budget, files)`, so at or below the budget an ORDERING tells the reader to read
    everything they already have — effort saved is zero by construction, which is why
    `roi-preregistration.md` failed B1 at 28.9% when 66.0% of changes are like this one. That
    argument is about the ordering and it still holds; `fired` is still False here.

    What changed is that a one-file change is the CHEAPEST possible deep read — the whole diff
    fits in one prompt — so the old rule muted exactly the reviews we can most afford. The comment
    now appears and says it is not in the top decile, and `allocate.depth` reads such a change in
    full rather than ranking it.
    """
    ranking = rank({"src/only.py": 11})
    assert not ranking.fired, (
        "the salience signal itself survives on the value; only the prose went"
    )

    body = comment(ranking)
    assert body and "alarm" not in body and "top decile" not in body

    # And the ordering is untouched where the budget DOES bind: four files still speak.
    wide = rank({"a.py": 11, "b.py": 7, "c.py": 3, "d.py": 1})
    assert wide.fired
    assert comment(wide) is not None


def test_what_to_look_at_comes_before_how_much_was_reviewed() -> None:
    """**THE ORDERING ARGUMENT SURVIVED THE REDESIGN; THE PARAGRAPH DID NOT.**

    This asserted a coverage PARAGRAPH above a table, on the reasoning that a reader who sees a
    list first weighs it against nothing. The reasoning still holds and the paragraph does not:
    it explained the method, and a developer waiting to merge does not act on the method. What
    remains is a count, and it sits after the list because the list is what they do something
    about while the count is what qualifies it.
    """
    body = comment(rank(CASES["ordered"]))

    assert body.startswith("###"), "the header is first"
    assert LOOK in body
    assert body.index(LOOK) < body.index("reviewed"), (
        f"the count came before the list of files to read: {body!r}"
    )
    assert "Ranked" not in body and "prior-fix" not in body, (
        f"the method crept back into the comment: {body!r}"
    )


def test_the_comment_makes_no_claim_about_correctness() -> None:
    body = comment(rank(CASES["ordered"]))
    assert body is not None
    for forbidden in ("bug", "vulnerabilit", "you should fix", "incorrect", "error in"):
        assert forbidden not in body.lower(), (
            f"the comment claimed something about correctness ({forbidden!r}); infer/ is closed "
            "and we publish no findings"
        )
