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

import pytest

from quantamind.infer.change_summary import Summary
from quantamind.ingest.context.tickets import Context
from quantamind.ingest.diff import Stated
from quantamind.rank.order import rank
from quantamind.render.comment import comment
from quantamind.render.verdict_block import SECTIONS
from quantamind.types.finding import Finding

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


def test_the_verdict_comes_before_everything_else() -> None:
    """**THIS TEST HAS NOW ASSERTED FOUR PRODUCT DECISIONS, EACH RECORDED IN PLACE.**

    A coverage paragraph above a table; then a list of files to look at; then that list before the
    reviewed count; and now a verdict before all of it. The reasoning never changed — the reader
    must meet the thing they act on first — only what that thing is. It is a verdict now because a
    developer waiting to merge wants to know whether this is good, needs a human, or has a bug.
    """
    body = comment(
        rank(CASES["ordered"]),
        summary=FULL,
        context=Context(stated=Stated("feat(store): the audit trail", "")),
    )
    lines = [ln for ln in body.splitlines() if ln.strip()]

    assert lines[0].startswith("### QuantaMind")
    assert lines[1].startswith(("✅", "⚠️", "🐛")), f"the verdict is not first: {lines[1]!r}"
    # **THE HEADING MOVED MODULES AND THE ORDERING IS THE SAME DECISION.** It was
    # `verdict_block`'s "**Goal — from the PR description**"; the deterministic block carries the
    # quote now, and it still sits under the verdict rather than above it.
    assert body.index(lines[1]) < body.index("**What this change says it is for**"), (
        "the verdict came after the goal"
    )


def test_the_comment_makes_no_claim_about_correctness() -> None:
    body = comment(rank(CASES["ordered"]))
    assert body is not None
    for forbidden in ("bug", "vulnerabilit", "you should fix", "incorrect", "error in"):
        assert forbidden not in body.lower(), (
            f"the comment claimed something about correctness ({forbidden!r}); infer/ is closed "
            "and we publish no findings"
        )


FULL = Summary(
    what_changed="Adds a table and records every rule against every changed file.",
    achieves_goal=True,
    reasoning="The table, the writer and the migration are present.",
    goal="feat(store): the audit trail",
    impact="Callers are unaffected; the table is additive.",
    breaks=False,
    breaks_why="The migration only adds a table.",
    convention="",
    dependents=("a.py",),
)


@pytest.mark.parametrize("section", SECTIONS)
def test_every_mandatory_section_is_present(section: str) -> None:
    """**THE GOLDEN RULE IS THE PRODUCT'S ANSWER TO ITS OWN QUESTION, SO IT IS NOT OPTIONAL.**

    A redesign collapsed the goal and both verdicts into a single headline, and the review became
    an opinion with no stated basis. It lasted about an hour, because nothing checked it. This is
    what checks it: removing a heading now fails the build instead of being noticed weeks later on
    somebody's pull request.
    """
    body = comment(rank(CASES["ordered"]), summary=FULL)

    assert section in body, (
        f"the mandatory section {section!r} is missing. Every one of them is half of "
        '"did this change do what it said, without disturbing anything else"'
    )


def test_a_review_that_could_not_run_says_so_and_offers_no_verdict() -> None:
    """**THE DEFECT THIS WAS BUILT FOR.** A real delivery hit MAX_TOKENS, the summary was dropped,
    and the comment degraded into a file list — indistinguishable from a clean review."""
    # **A SUMMARY IS PASSED ON PURPOSE.** Without one the assertion is vacuous: `summary is None`
    # already suppresses the verdicts, so removing the `blind` guard changed nothing and the
    # sabotage passed. A stale summary from a partial run is exactly what must NOT be shown.
    body = comment(
        rank(CASES["ordered"]), summary=FULL, blind="the diff was too large for one pass"
    )

    assert "could not review" in body
    assert "the diff was too large for one pass" in body
    assert "Does it do what the PR says?" not in body, (
        "a review that never ran presented a verdict anyway"
    )
    assert FULL.what_changed not in body, "a summary from a failed run was rendered as fact"


def test_the_headline_counts_what_there_is_to_fix() -> None:
    """A count, not a mood. "Found things" tells a reader nothing about whether to stop."""
    body = comment(
        rank(CASES["ordered"]),
        summary=FULL,
        findings=[Finding(path="a.py", quote="x", claim="This leaks.", line=3)],
    )
    headline = [ln for ln in body.splitlines() if ln.strip()][1]

    assert headline == "🐛 **Found 1 thing(s) worth fixing.**", f"headline reads {headline!r}"


def test_a_clean_change_says_so_in_the_headline() -> None:
    body = comment(rank(CASES["ordered"]), summary=FULL)
    headline = [ln for ln in body.splitlines() if ln.strip()][1]

    assert headline.startswith("✅"), f"a change that does what it says read as {headline!r}"
    assert "nothing that imports it breaks" in headline


def test_our_own_fix_history_is_not_in_the_comment() -> None:
    """It decides the ordering and reaches the dashboard. A developer does not act on it."""
    body = comment(rank(CASES["ordered"]), summary=FULL)

    assert "later fix" not in body and "prior fixes" not in body
