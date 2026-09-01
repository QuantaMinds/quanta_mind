"""What the declared rules said about each file — the honest answer to "should I fear this one".

WHAT: Drives `render.blocks.scope_block.coverage()` with `Checked` rows and asserts what lands
      beside each path.
WHY:  **A PER-FILE CONFIDENCE OR IMPORTANCE WAS ASKED FOR AND REFUSED.** `render/comment.py` states
      the rule it would break: *no severity we cannot calibrate, no confidence we have not
      measured*. We have measured neither. Any label invented would be the ranking wearing a
      friendlier word, and `publishing-rules.md` never-publishes the ranking.

      **WHAT IS TRUE AND REASSURING IS WHAT ACTUALLY RAN.** A count of the customer's OWN rules,
      checked and passed on their file, is a fact they can re-run on the same commit themselves —
      which is the difference between reassurance and a soothing number.

      **`UNCHECKABLE` IS NOT A PASS AND MUST NOT PRINT LIKE SILENCE.** A JavaScript file under a
      Python-only rule set gets neither a tick nor nothing at all, because nothing at all reads as
      "fine". It is also excluded from the headline count, which counts DECIDED files only.
IMPORTS: quantamind.rank.order, quantamind.render.blocks.scope_block, quantamind.types.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.rank.order import rank
from quantamind.render.blocks.scope_block import coverage
from quantamind.types.standards.checked import Checked, Outcome
from quantamind.types.verdict import Reason, Site

SCORES = {f"src/mod{n}.py": 20 - n for n in range(8)}


def _block(scores: dict[str, int], checks: tuple[Checked, ...] = ()) -> str:
    return "\n".join(coverage(rank(scores), (), None, checks))


def test_the_rules_a_file_passed_are_counted_beside_it() -> None:
    """**THE ANSWER TO "DO I NEED TO FEAR THIS FILE".** Not a score we invented — a count of the
    customer's own declared rules, which they can re-run on the same commit themselves."""
    checks = (
        Checked("no-print", Site("src/mod0.py", 1), Outcome.PASSED),
        Checked("no-eval", Site("src/mod0.py", 1), Outcome.PASSED),
        Checked("no-print", Site("src/mod1.py", 9), Outcome.VIOLATED, evidence="print at line 9"),
    )
    block = _block(SCORES, checks=checks)

    assert "2 rules passed" in block
    assert "**1 rule violated**" in block
    assert "checked against the rules you declared" in block
    assert "**2** were checked" in block, "the headline counts files, not checks"


def test_a_file_no_rule_could_decide_says_so() -> None:
    """`UNCHECKABLE` is not a pass. A JavaScript file with a Python-only rule set gets neither a
    tick nor silence — silence would read as "fine"."""
    checks = (
        Checked(
            "no-print", Site("src/mod0.py", 1), Outcome.UNCHECKABLE, why=Reason.LANGUAGE_UNSUPPORTED
        ),
    )
    block = _block(SCORES, checks=checks)

    assert "no rule could be checked here" in block
    assert "checked against the rules you declared" not in block, (
        "an undecided check must not be counted as a decided one in the headline"
    )


def test_no_declared_rules_means_no_claim_about_rules() -> None:
    """A repository with no `.quantamind/rules.toml` must not read as one whose rules all passed."""
    block = _block(SCORES)

    assert "rules you declared" not in block
    assert "rules passed" not in block
