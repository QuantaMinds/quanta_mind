"""The standards section must print its denominator, or it misreports coverage as compliance.

WHAT: Renders real `Checked` rows through `render/rule_block.block()` and asserts on the text a
      customer would read.
WHY:  **"1 VIOLATION" INVITES THE READER TO ASSUME EVERYTHING ELSE WAS CHECKED.** It usually was
      not: only Python is parsed, so a repository of TypeScript produces rows we could not decide.
      A reader who cannot see that count reads OUR parser coverage as THEIR compliance — and the
      less of their code we can read, the better the section looks.
IMPORTS: render.rule_block, types.{checked,verdict}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.render.rule_block import block
from quantamind.types.checked import Checked, Outcome
from quantamind.types.verdict import Reason, Site

PASSED = Checked("no-pickle", Site("a.py"), Outcome.PASSED)
VIOLATED = Checked("no-print", Site("a.py", 12), Outcome.VIOLATED, evidence="print at line 12")
UNCHECKED = Checked(
    "no-print", Site("app.ts"), Outcome.UNCHECKABLE, why=Reason.LANGUAGE_UNSUPPORTED
)
DEFERRED = Checked("async-error-handling", Site("a.py"), Outcome.DEFERRED)


def test_no_rules_declared_renders_nothing() -> None:
    """A repository that declared no standards gets no section, not an empty one."""
    assert block(()) == ""


def test_a_violation_names_the_rule_the_file_and_the_line() -> None:
    text = block([VIOLATED, PASSED])

    assert "no-print" in text and "a.py:12" in text
    assert "print at line 12" in text, "a violation the developer cannot locate is an accusation"


def test_the_undecided_count_is_printed_beside_the_result() -> None:
    """**THE ONE THAT MATTERS.** Two of the four rows here were never decided."""
    text = block([PASSED, VIOLATED, UNCHECKED, DEFERRED])

    assert "2 check(s) decided" in text, f"the denominator is missing: {text!r}"
    assert "2 not decided" in text
    assert "language_unsupported" in text, "the reason must be named, not summarised away"
    assert "are not passes" in text, (
        "the section reported undecided rows without saying they are not passes — which is how "
        "a repository we cannot parse reads as fully compliant"
    )


def test_a_clean_run_says_every_rule_was_decided() -> None:
    text = block([PASSED, PASSED])

    assert "No violation" in text
    assert "Every declared rule was decided" in text
    assert "not decided" not in text


def test_a_deferred_rule_is_shown_rather_than_hidden() -> None:
    """A model-judged rule the customer declared and we did not enforce is still their standard."""
    text = block([PASSED, DEFERRED])

    assert "await a model and were not enforced here" in text
