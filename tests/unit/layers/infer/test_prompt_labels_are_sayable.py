"""No label in the reviewer's prompt may be an identifier, because the model repeats them.

WHAT: Asserts every `[BRACKETED]` block label in `infer.summary_prompt.PROMPT` is ordinary English,
      and that no internal identifier appears anywhere in the prompt body.
WHY:  **THIS IS A REGRESSION TEST FOR A REAL POSTED COMMENT.** On
      `QuantaMinds/quanta_mind#101` the model wrote *"The test files in STATIC_IMPORTERS will need
      to be updated"* onto a live pull request. The prompt had a block called `[STATIC_IMPORTERS]`
      and a task line reading "one sentence on the files in STATIC_IMPORTERS", so the model did
      exactly what it was asked and used our vocabulary.

      **A LABEL IS NOT PRIVATE JUST BECAUSE WE THINK OF IT AS STRUCTURE.** It is the only name the
      model has for that block, and `docs/product/comment-golden-rules.md` forbids our method
      reaching a developer's screen.

      **`tests/unit/layers/render/test_never_our_method.py` COULD NOT HAVE CAUGHT THIS.** That test
      renders through `render.comment.comment()` and asserts on strings WE write. This leak arrived
      inside a model's free text, which no renderer test can pin because it is not deterministic.
      **The only place it is checkable is the input**, which is what this file checks.

      **THE RULE IS SHAPE, NOT A DENYLIST.** Banning the four labels that leaked would pass the
      moment somebody adds a fifth. `UPPER_SNAKE` with an underscore is what an identifier looks
      like, and no sentence a customer should read contains one.
IMPORTS: quantamind.infer.summary_prompt.
"""

from __future__ import annotations

import re

from quantamind.infer.summary_prompt import PROMPT

LABEL = re.compile(r"\[([A-Z][^\]]*)\]")
IDENTIFIER = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")


def test_every_block_label_reads_as_english() -> None:
    """A label the model echoes must be a phrase, not a constant name."""
    labels = LABEL.findall(PROMPT)
    assert labels, "the prompt has no labelled blocks; this test is checking the wrong string"
    offenders = [label for label in labels if "_" in label]
    assert not offenders, (
        f"prompt block label(s) {offenders} look like identifiers. The model repeats labels — "
        "STATIC_IMPORTERS reached a real pull request this way. Word them as English."
    )


def test_no_identifier_anywhere_in_the_prompt() -> None:
    """Not just the labels. The task line referred to `STATIC_IMPORTERS` by name too."""
    found = sorted(set(IDENTIFIER.findall(PROMPT)))
    assert not found, (
        f"{found} appear in the prompt. Anything named there is vocabulary the model may use in a "
        "sentence a customer reads."
    )


def test_the_task_asks_for_importers_without_naming_a_constant() -> None:
    """**NAMES THE ARTEFACT IT MUST FIND**, per AGENTS.md rule 14 — not merely 'no identifier'."""
    assert "one sentence on the files that import the changed code" in PROMPT


def test_the_history_block_does_not_describe_the_ranking_signal() -> None:
    """`publishing-rules.md` puts what the ranking is built from first on the never-publish list.

    The block read `[PRIOR_FIXES] number of later commits that returned to each file`. Echoed, that
    is the mechanism. **Here the vaguer label is the safer one**, which is the opposite of this
    codebase's usual instinct and the reason this test says so out loud.
    """
    for phrase in ("later commits that returned", "prior fix", "PRIOR_FIXES"):
        assert phrase not in PROMPT, f"the prompt explains the ranking signal: {phrase!r}"
