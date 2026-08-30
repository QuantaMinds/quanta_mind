"""The one sentence a developer reads beside a blocked merge, asserted rather than hoped for.

WHAT: Drives `render/status_check.render` over gates built from real `Checked` rows and asserts the
      exact state and the content of the description.
WHY:  **THIS SENTENCE IS THE WHOLE EXPLANATION FOR A FAILING CHECK.** GitHub shows one line. If it
      omits what could not be checked, a status reading "3 rule check(s) passed" while nine files
      were unparseable reads as compliance and is a proxy for it -- the shape rule 14 names.
IMPORTS: pytest, quantamind.types.{checked,verdict}, quantamind.verify.blocking,
      quantamind.render.status_check.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.render.status_check import NothingDeclared, render
from quantamind.types.checked import Checked, Outcome
from quantamind.types.verdict import Reason, Site
from quantamind.verify.blocking import decide


def _violated() -> Checked:
    return Checked("no-pickle", Site("app/loader.py", 5), Outcome.VIOLATED, evidence="pickle.loads")


def _unparseable() -> Checked:
    return Checked("no-pickle", Site("b.py"), Outcome.UNCHECKABLE, why=Reason.UNPARSEABLE_SYNTAX)


def test_a_violation_fails_the_check_and_the_sentence_names_rule_and_file() -> None:
    shown = render(decide([_violated()]))

    assert shown.state == "failure"
    assert "no-pickle" in shown.description, f"the rule was not named: {shown.description!r}"
    assert "app/loader.py" in shown.description, f"the file was not named: {shown.description!r}"


def test_a_clean_change_passes_and_says_how_many_checks_ran() -> None:
    rows = [Checked("r", Site("a.py"), Outcome.PASSED) for _ in range(3)]

    shown = render(decide(rows))

    assert shown.state == "success"
    assert "3" in shown.description, f"the denominator is missing: {shown.description!r}"


def test_what_could_not_be_checked_is_in_the_sentence_not_only_in_the_trail() -> None:
    """A pass quoted without its unchecked count is a proxy for compliance, not compliance."""
    rows = [Checked("r", Site("a.py"), Outcome.PASSED), _unparseable()]

    shown = render(decide(rows))

    assert shown.state == "success"
    assert "could not be checked" in shown.description, (
        f"nine unparseable files would read as a clean pass: {shown.description!r}"
    )


def test_a_deferred_row_is_named_so_a_pass_does_not_look_complete() -> None:
    rows = [
        Checked("r", Site("a.py"), Outcome.PASSED),
        Checked("m", Site("a.py"), Outcome.DEFERRED),
    ]

    shown = render(decide(rows))

    assert "left to a reviewer" in shown.description, (
        f"'a model still has to look at this' read as a clean pass: {shown.description!r}"
    )


def test_a_change_no_rule_governed_has_no_sentence_at_all() -> None:
    with pytest.raises(NothingDeclared):
        render(decide([]))
