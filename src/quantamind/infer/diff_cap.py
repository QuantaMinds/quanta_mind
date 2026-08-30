"""Cut a diff to fit a prompt, and mark the cut so the reader knows it happened.

WHAT: `capped(diff, limit)` returns the diff unchanged when it fits, and the first `limit`
      characters followed by `TRUNCATED` when it does not.
WHY:  **A SLICED DIFF LOOKS EXACTLY LIKE A COMPLETE ONE.** Both prompt builders wrote
      `diff[:MAX_DIFF_CHARS]`, so the model read a change that stopped mid-hunk with no way to
      know it had, and answered as though it had seen everything. `change_summary` carried a
      comment claiming the truncation was "visible in the output"; nothing made it so. That is
      `AGENTS.md` rule 14 — a comment may explain why, never assert whether.

      **THE TWO LIMITS ARE DIFFERENT AND MUST STAY THAT WAY**, so the limit is an argument
      rather than a constant here: 30,000 for the summary, which shares its prompt with the
      conventions and fact blocks, and 120,000 for the review, which does not.

      **IT LIVES IN ITS OWN MODULE BECAUSE NEITHER CALLER CAN HOLD IT.** `change_summary`
      imports `gemini`, so `gemini` cannot import back, and `gemini` sits at the file-length cap
      with no room for a copy. Duplicating it would have been two implementations of one rule.
IMPORTS: stdlib only. The leftmost thing in `infer/`.
CONSUMED BY: `infer/change_summary.py`, `infer/gemini.py`.
"""

from __future__ import annotations

TRUNCATED = "\n\n[... truncated: this diff is longer than the review reads ...]"


def capped(diff: str, limit: int) -> str:
    """The diff, cut to `limit` characters with the cut MARKED. Unchanged when it fits.

    **THE BEGINNING IS KEPT, NOT THE END.** A reviewer reads the first files first, and a tail
    slice would drop exactly the part a summary is most likely to be about.
    """
    return diff if len(diff) <= limit else diff[:limit] + TRUNCATED
