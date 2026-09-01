"""D1e: a switched-off standard must reach the reader, or the record was pointless.

WHAT: `render/blocks/inheritance_block.py`, and its path through the whole comment.
WHY:  **"A STANDARD THAT CAN BE DISABLED INVISIBLY IS NOT A STANDARD."** `combine` can compute a
      perfect `Dropped` record and it changes nothing if the record never reaches a reader. D1c's
      sabotage found exactly that shape twice — a block with its own tests and no test on the CALL
      — so the wiring is asserted here too.
IMPORTS: quantamind.ingest.standards.inherited, quantamind.rank.order, quantamind.render.*.
CONSUMED BY: `just test-unit`.
"""

from __future__ import annotations

from quantamind.ingest.standards.inherited import Dropped, Inheritance, Refused, Tightened
from quantamind.rank.order import rank
from quantamind.render.blocks.inheritance_block import inheritance
from quantamind.render.comment import comment
from quantamind.types.standards.rule import Severity

DROPPED = Inheritance(dropped=(Dropped("no-eval", Severity.HIGH),))


def test_nothing_renders_when_the_repository_follows_its_organisation() -> None:
    """**THE COMMON CASE MUST BE SILENT.** A section always printing is one nobody reads."""
    assert inheritance(Inheritance()) == ""
    assert inheritance(None) == ""


def test_a_dropped_rule_is_named_with_what_was_given_up() -> None:
    """The reader needs the rule id and the severity, not a count."""
    text = inheritance(DROPPED)

    assert "no-eval" in text
    assert "high" in text
    assert "Switched off here" in text


def test_an_unreadable_organisation_file_says_nothing_inherited_was_checked() -> None:
    """**LOUDER THAN A DROP.** A drop is a decision; this is enforcement stopping by accident."""
    text = inheritance(Inheritance(org_read=False))

    assert "could not be read" in text
    assert "none of the standards" in text
    assert "still ran" in text, "the repository's own rules did run, and the reader must know"


def test_a_tightening_and_a_refusal_each_render_distinctly() -> None:
    """Three outcomes, three sentences — a reader must not have to infer which happened."""
    text = inheritance(
        Inheritance(
            tightened=(Tightened("no-print", Severity.LOW, Severity.HIGH),),
            refused=(Refused("no-eval", "the stricter one applies"),),
        )
    )

    assert "Stricter here than required" in text
    assert "Not applied as written" in text


def test_a_dropped_rule_reaches_the_posted_comment() -> None:
    """**THE WIRING, NOT THE BLOCK.** A section built correctly and never called is D1c's lesson."""
    body = comment(rank({"a.py": 4, "b.py": 1}), inherited=DROPPED)

    assert "no-eval" in body
    assert "Switched off here" in body


def test_no_inheritance_record_adds_nothing_to_the_comment() -> None:
    """The default path must cost the reader nothing."""
    body = comment(rank({"a.py": 4, "b.py": 1}))
    assert "Organisation standards" not in body
