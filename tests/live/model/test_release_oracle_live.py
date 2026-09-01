"""The release verifier against the real PyPI, including the direction that must NOT fire.

WHAT: Refutes the reviewer's "this release does not exist" claims about releases that do exist,
      and requires a genuinely absent release to stay unrefuted.
WHY:  **THE FIRST VERSION OF THIS VERIFIER CONFIRMED EVERY FALSE CLAIM IT WAS BUILT TO REFUTE.** It
      took the first name-shaped token before the version -- `The`, in "The version 1.45.34 of
      awscli does not exist" -- asked PyPI for `The/1.45.34`, got a 404, and read that as the claim
      being true. **A verifier whose failure mode is confirming is worse than no verifier**: the
      reviewer's confabulation acquires a fact behind it, and a well-grounded false finding has
      none of confabulation's tell.

      So the absent direction is asserted here too. Without it the verifier could pass by refuting
      everything, which is the same defect wearing the opposite sign.
IMPORTS: stdlib, pytest, quantamind.verify.external_facts.
CONSUMED BY: `uv run pytest tests/live`.
"""

from __future__ import annotations

import pytest

from quantamind.verify.external_facts import Verdict
from quantamind.verify.releases import adjudicate_release, released


def test_a_release_that_exists_refutes_the_claim_it_does_not() -> None:
    reached, exists = released("requests", "2.32.3")
    if not reached:
        pytest.skip("PyPI unreachable; this test proves nothing when it cannot ask")
    assert exists, "requests 2.32.3 is on PyPI; the fixture has rotted if this fails"

    got = adjudicate_release("The package requests 2.32.3 is not on PyPI.")
    assert got.verdict is Verdict.REFUTED
    assert not got.publishable(), "a refuted claim must not publish"


def test_a_genuinely_absent_release_is_not_refuted() -> None:
    """The control. Without it the verifier could pass by refuting everything."""
    reached, exists = released("flask", "99.99.99")
    if not reached:
        pytest.skip("PyPI unreachable")
    assert not exists, "flask 99.99.99 must not exist, or this control is meaningless"

    got = adjudicate_release("The version flask 99.99.99 does not exist on PyPI.")
    assert got.verdict is not Verdict.REFUTED, "refuted a claim that is actually true"


def test_an_unidentifiable_subject_is_unresolvable_not_confirmed() -> None:
    """The exact shape of the bug: no package in the sentence has that release."""
    got = adjudicate_release("Some dependency 91.7.3 does not exist anywhere.")
    assert got.verdict is Verdict.UNRESOLVABLE
    assert not got.publishable()


def test_a_true_absence_claim_is_CONFIRMED_when_the_diff_names_the_package() -> None:
    """The direction the first version threw away: a real package with an absent release.

    **`flask==99.99.99` is a TRUE finding and it was being dropped as UNRESOLVABLE**, because the
    oracle could not tell "the subject is unidentifiable" from "the package is real and this
    release is not". Version existence alone cannot separate those; package existence can.
    """
    got = adjudicate_release(
        "The pin flask==99.99.99 is broken because that version does not exist on PyPI.",
        context="+    flask==99.99.99\n",
    )
    if not got.reachable:
        pytest.skip("PyPI unreachable")
    assert got.verdict is Verdict.CONFIRMED, f"a true absence-claim was not confirmed: {got.detail}"
    assert got.publishable(), "a confirmed true finding must publish"


def test_a_package_the_diff_never_mentions_cannot_be_CONFIRMED() -> None:
    """PyPI has packages called `pin`, `Some` and `dependency`. A stop-list cannot win that race.

    **This exact sentence CONFIRMED on `dependency` before the diff check existed** — publishing a
    finding on the strength of a name collision, which is the direction
    `docs/engineering/CORRECTIONS.md` entry 8 records.
    """
    got = adjudicate_release(
        "Some dependency 91.7.3 does not exist anywhere.",
        context="+    flask==1.0\n",
    )
    assert got.verdict is not Verdict.CONFIRMED, f"confirmed on a name collision: {got.detail}"
    assert not got.publishable()


def test_without_a_diff_confirming_is_unavailable() -> None:
    """No context means no way to bind the name to the change, so the safe direction is to drop."""
    got = adjudicate_release("The pin flask==99.99.99 does not exist on PyPI.", context="")
    assert got.verdict is not Verdict.CONFIRMED
