"""What a declared link says in the comment, and the silence it makes typed.

WHAT: Drives `render.blocks.linked_block.linked()` over the three states a declaration can be in.
WHY:  **D3a SHIPS BEFORE D3b AND THIS BLOCK IS THE WHOLE REASON IT IS WORTH SHIPPING ALONE.**
      Reading the linked repository is gated on a design partner with more than one that matters.
      `render/comment.py` already prints one static sentence — *cross-repository impact is not
      checked at all* — and a reader has no way to tell whether that means **there is nothing
      across the boundary** or **we did not look**. Naming the repositories makes it the second,
      which is the true one.

      **A DECLARATION WE COULD NOT READ IS NOT AN ABSENT ONE.** Both leave the list empty and they
      print differently, because "this business declares no links" is a claim about somebody's
      architecture and we would be making it out of our own failed read.

      **AND THE BLOCK PROMISES NOTHING IT DID NOT DO.** It says what was NOT checked. A test below
      fails if it ever starts implying the linked repositories were looked at.
IMPORTS: quantamind.ingest.standards.links_file, quantamind.render.blocks.linked_block.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.ingest.standards.links_file import Link
from quantamind.render.blocks.linked_block import linked


def test_no_declaration_prints_nothing() -> None:
    """The common case. A line saying "you declared no links" is furniture on every review."""
    assert linked((), False) == []


def test_a_declared_link_is_named_and_said_to_be_unchecked() -> None:
    """The reader learns the boundary exists AND that we did not cross it, in one sentence."""
    block = "\n".join(linked((Link("acme/billing", "consumes our Invoice schema"),), False))

    assert "`acme/billing`" in block
    assert "consumes our Invoice schema" in block
    assert "Nothing in it was checked" in block


def test_several_links_read_as_plural() -> None:
    """Trivial, and the kind of thing that reaches a customer's pull request unnoticed."""
    block = "\n".join(linked((Link("acme/billing"), Link("acme/mobile")), False))

    assert "declares 2 linked repositories" in block
    assert "Nothing in them was checked" in block


def test_one_link_reads_as_singular() -> None:
    assert "declares 1 linked repository" in "\n".join(linked((Link("acme/billing"),), False))


def test_an_unreadable_declaration_never_reads_as_no_links() -> None:
    """**THE ONE THAT WOULD MAKE A CLAIM ABOUT SOMEBODY'S ARCHITECTURE OUT OF OUR OWN OUTAGE.**"""
    block = "\n".join(linked((), True))

    assert "could not be read" in block
    assert "not established as none" in block
    # **THE ASSERTION IS THE AFFIRMATIVE CLAIM, NOT THE WORD.** A first draft forbade "declares"
    # outright and failed on the sentence's own "whether this repository declares links ... is
    # unknown" — a check that fires on correct output is one somebody deletes.
    assert "declares 0" not in block
    assert "linked repositor" not in block, "an unreadable file must not report a count"


def test_the_block_never_implies_the_linked_repository_was_looked_at() -> None:
    """D3b is not built. A sentence hinting otherwise would be the clean bill of health for a
    check that never ran that this product exists to refuse."""
    block = "\n".join(linked((Link("acme/billing"),), False)).lower()

    for word in ("checked against", "verified", "no issues", "safe", "compatible"):
        assert word not in block, f"the block implied it looked across the boundary: {word!r}"
