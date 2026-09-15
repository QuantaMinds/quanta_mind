"""The pin detector's path, including the delivery where it is the only thing to say.

WHAT: `pins_for(clone, head_sha, every_file)` renders the pin-mismatch block. `only(...)` is the
      delivery for a change with no reviewable file, which may still carry that block.
WHY:  **THE PIN DETECTOR RUNS BEFORE THE EARLY RETURN, NOT AFTER IT.** It needs no ranking and no
      model, and a pull request that changes ONLY a workflow is the most common shape carrying a
      pin change. Returning `NO_FILES` first left it unreachable on exactly those changes even
      after it was given the unfiltered list -- found by firing at a real pull request rather than
      by any test. → `docs/findings/oracles/WHY_THE_ORACLES_NEVER_FIRE_2026-08.md`

      **SPLIT OUT OF `serve/review_delivery.py` WHEN THAT FILE HIT THE 200-LINE CAP**, and split
      here rather than anywhere else because the ordering above is the whole reason both halves
      exist: detecting the mismatch and deciding that a workflow-only change still deserves a
      comment are one decision, and they were eleven lines apart in a function doing nine other
      things. `check_structure.py` says split by concern rather than raise the cap; this is the
      concern.

      **THREE OUTCOMES, NOT A BOOLEAN.** `NO_FILES` (nothing to say), `REHEARSED` (posting off) and
      `POSTED`/`DUPLICATE` are four different results, and a caller must be able to tell a change
      we declined to comment on from one we commented on twice.
IMPORTS: ingest.publish.github_reviews, render.pin_block, types.review, verify.pin_check.
      Rightmost layer.
CONSUMED BY: `serve/review_delivery.py`.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from quantamind.ingest.publish.github_reviews import publish
from quantamind.render.blocks.pin_block import block
from quantamind.serve.blocking_status import announce
from quantamind.types.review import Delivered, Outcome
from quantamind.verify import pin_check


def pins_for(clone: Path, head_sha: str, every_file: Sequence[str]) -> str:
    """The pin block for this change, or an empty string when nothing mismatched.

    **`every_file`, NOT THE RANKER'S FILTERED LIST.** The ranker drops anything it does not read,
    which includes the workflow files this detector exists for.
    """
    mismatched, _unresolved = pin_check.check(clone, head_sha, list(every_file))
    return block(mismatched)


def only(repo: str, number: int, head_sha: str, pins: str, *, enabled: bool) -> Delivered:
    """The delivery for a change carrying no reviewable file. `pins` may still be worth posting.

    **THE GATE IS ANNOUNCED FIRST, AND THAT IS THE WHOLE OF ISSUE #106.** This path returned before
    any status was posted, so a documentation-only pull request left `quantamind/declared-rules`
    permanently `pending` -- and `main` requires it. Every CI job on `QuantaMinds/quanta_mind#104`
    was green and it could not merge. **A gate that sometimes declines to speak cannot be a required
    check**, so the no-governed-file case is announced through the same `announce()` every other
    delivery uses rather than a second path that has to be remembered.

    `checks=()` folds to `Standing.NOT_DECLARED`, which now posts a success whose description says
    no rule governed the change. **Naming the state is not asserting a pass.**
    """
    announce(repo, head_sha, (), enabled=enabled)
    if not pins:
        return Delivered(Outcome.NO_FILES, (), (), None)
    if not enabled:
        return Delivered(Outcome.REHEARSED, (), (), pins)
    wrote = publish(repo, number, head_sha, pins, ())
    return Delivered(Outcome.POSTED if wrote else Outcome.DUPLICATE, (), (), pins)
