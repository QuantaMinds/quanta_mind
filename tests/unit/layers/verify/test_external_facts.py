"""The oracle's decisions, and the case where it must refuse rather than guess.

WHAT: Exercises claim extraction, the pin reader, and the three-way verdict on text alone, with no
      network. The live behaviour against GitHub is covered by `tests/live/test_oracle_live.py`.
WHY:  **`UNRESOLVABLE` COLLAPSING INTO `CONFIRMED` WOULD REPRODUCE THE EXACT FAILURE THIS ORACLE
      EXISTS TO FIX** -- an unanswerable question answered confidently -- so `publishable()` is
      asserted per verdict rather than assumed from the enum's shape.

      **AND `pins()` READS ADDED LINES ONLY.** A pin the change REMOVES is not a claim the change
      makes; adjudicating it attaches a verdict to code on its way out, and the finding would name
      a commit nobody is proposing to use.
IMPORTS: stdlib, quantamind.verify.external_facts.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.verify.external_facts import Adjudicated, Verdict, adjudicate
from quantamind.verify.pin_mismatch import pins

DIFF = (
    "--- a/.github/workflows/ci.yml\n"
    "+++ b/.github/workflows/ci.yml\n"
    "-      - uses: actions/checkout@1111111111111111111111111111111111111111 # v1.0.0\n"
    "+      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0\n"
    "+      - uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0\n"
)


def test_pins_reads_added_lines_and_ignores_removed_ones() -> None:
    found = pins(DIFF)
    assert set(found) == {"actions/checkout", "actions/setup-python"}
    assert found["actions/checkout"].startswith("9c091bb2")
    assert "1111111111111111111111111111111111111111" not in found.values(), (
        "a pin the change removes is not a claim the change makes"
    )


def test_a_finding_with_no_external_claim_is_left_alone() -> None:
    got = adjudicate("This function should handle a null argument.")
    assert got.verdict is Verdict.NO_CLAIM
    assert got.publishable(), "a finding making no external claim must not be gated by this oracle"


def test_a_sha_with_no_repository_is_unresolvable_not_confirmed() -> None:
    got = adjudicate("The commit 9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 does not exist.")
    assert got.verdict is Verdict.UNRESOLVABLE
    assert not got.publishable(), "a claim we cannot check is not one we publish"


def test_unresolvable_is_not_a_soft_confirmed() -> None:
    """The whole design rests on this, so it is asserted rather than read off the enum."""
    assert Adjudicated(Verdict.CONFIRMED, "").publishable()
    assert Adjudicated(Verdict.NO_CLAIM, "").publishable()
    assert not Adjudicated(Verdict.UNRESOLVABLE, "").publishable()
    assert not Adjudicated(Verdict.REFUTED, "").publishable()


def test_an_unreachable_oracle_is_recorded_as_unreachable() -> None:
    """A gate that drops everything because the network is down looks like a gate working."""
    assert not Adjudicated(Verdict.UNRESOLVABLE, "no answer", reachable=False).reachable
    assert Adjudicated(Verdict.CONFIRMED, "ok").reachable


def test_a_major_alias_comment_is_satisfied_by_the_release_it_abbreviates() -> None:
    """`# v6` on a commit tagged v6.4.0 is the normal convention, not a defect.

    **AN EXACT-MATCH RULE FLAGGED 13 REAL PINS AND ONLY 3 WERE GENUINE — a 77% false positive
    rate, worse than the model this replaces.** The `v6` alias has usually moved on to a newer
    release, so it is not at the pinned commit, and requiring it to be there manufactures
    disagreements for a living.
    """
    from quantamind.verify.pin_mismatch import satisfies

    assert satisfies("v6", "v6.4.0")
    assert satisfies("v6", "v6")
    assert satisfies("v4", "v4.0.3")
    assert satisfies("v7", "v7.0.1")
    # And the genuine disagreements must survive it, or the fix has deleted the detector.
    assert not satisfies("v5", "v7.0.0")
    assert not satisfies("v4", "v5.3.0")
    assert not satisfies("v1.1.4", "v1.2.0")


def test_satisfies_does_not_depend_on_the_caller_stripping_first() -> None:
    """It stripped only the tag, so it was right for one caller and silently wrong for the rest."""
    from quantamind.verify.pin_mismatch import satisfies

    assert satisfies("v6", "v6.4.0") == satisfies("6", "6.4.0") is True
