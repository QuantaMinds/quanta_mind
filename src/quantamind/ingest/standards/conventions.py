"""The standards a team already wrote down, wherever they happen to keep them.

WHAT: `written(clone, sha)` returns the convention documents present at that commit, as
      `(path, text)` pairs, bounded in size. Empty when the repository keeps none.
WHY:  **A TEAM THAT WROTE ITS RULES DOWN SHOULD NOT HAVE TO WRITE THEM AGAIN FOR US.**
      `.quantamind/rules.toml` asks a customer to restate standards they have already documented,
      in a format only this product reads, and every restatement is a chance for the two to drift.
      Most repositories already carry the real thing: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`,
      `.cursorrules`. Those are the standards the team actually agreed to.

      **THIS IS CONTEXT, NOT ENFORCEMENT, AND THE DIFFERENCE IS THE WHOLE POINT.** Prose cannot be
      re-run on a commit and shown to produce the same verdict, so nothing read here becomes a
      `Checked` row or enters the audit trail — that remains the parser's territory. What it does
      is let a review say "this contradicts the convention you wrote in AGENTS.md", which is a
      claim the reader can check against their own document in one click.

      **THE RULES ARE EXTRACTED, NOT THE PROSE TRUNCATED.** A convention file must be bounded — at
      12,000 characters the two documents in this repository alone pushed a real review to
      MAX_TOKENS. But cutting at a character count drops whatever is at the bottom, and in a
      numbered document that is rules 9 through 15: the review then silently enforces the first
      half of a standard. So the rule-shaped lines are kept and the surrounding argument is
      dropped, which fits several times as many actual rules in the same budget. A document with
      no list structure falls back to its opening, truncated and said so.

      **READ FROM GIT AT THE COMMIT UNDER REVIEW.** The clone has no working tree, and a change that
      EDITS the conventions must be judged against the version it proposes.

      **AND FROM DISK WHEN THERE IS A DISK, LABELLED AS UNCOMMITTED.** A developer running this on
      their own checkout may keep a `CLAUDE.md` that is gitignored or simply not committed yet, and
      on that machine it is a real standard they work to. It is read, and its name carries
      `(uncommitted)` — because a rule living on one laptop binds nobody else, and a review that
      presented it as the team's standard would be inventing consensus. The endpoint sees none of
      this: its clones have no working tree, which is exactly the honest outcome there.
IMPORTS: stdlib, `ingest.blob`. Nothing to its right.
CONSUMED BY: `infer/change_review.py`.
"""

from __future__ import annotations

import re
from pathlib import Path

from quantamind.ingest.blob import BlobUnreadable, at

# Ordered by how specifically each is about how to WRITE code here. An agent-instruction file is
# the most direct statement of a team's conventions; a contributing guide is often about process.
KNOWN = (
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    ".github/copilot-instructions.md",
    "CONVENTIONS.md",
    "CONTRIBUTING.md",
)
# **6,000 CHARACTERS EACH, WHICH IS ABOUT 1,500 WORDS.** At 12,000 the two documents in this
# repository alone pushed a real review to MAX_TOKENS: a convention file competes with the
# diff for the same budget, and the diff is the thing being reviewed.
MAX_CHARS = 6_000
# A rule is almost always a list item, a numbered item, or a bolded imperative. Prose between them
# is the argument FOR the rule, which a reviewer checking compliance does not need.
RULE_SHAPED = re.compile(r"^\s*(?:[-*+]\s|\d+[.)]\s|#{1,6}\s|\*\*)")
MIN_RULES = 3
TRUNCATED = "\n\n[... truncated: this document is longer than the review reads ...]"


def _rules_only(text: str) -> str:
    """The rule-shaped lines of a convention document, or the whole thing when it has no shape.

    **A CHARACTER CAP DROPS THE END OF A NUMBERED LIST, WHICH IS RULES 9 THROUGH 15.** Enforcing
    the first half of a standard and reporting it as the standard is worse than reading none of it,
    because nobody can see which half was applied. Keeping the list items and discarding the
    argument between them fits several times as many rules in the same budget.

    Below `MIN_RULES` matches the document is prose rather than a list, and the original is
    returned for the caller to bound however it bounds anything else.
    """
    kept = [line for line in text.splitlines() if RULE_SHAPED.match(line)]
    return "\n".join(kept) if len(kept) >= MIN_RULES else text


def written(clone: Path, sha: str) -> tuple[tuple[str, str], ...]:
    """Every convention document this repository carries at `sha`, in order of directness.

    **AN UNREADABLE CLONE YIELDS NOTHING RATHER THAN RAISING.** Conventions are context: a review
    without them is weaker, and a review that failed because a git call did is worse. The caller
    already learns a clone is broken from every other read that needs it.
    """
    found: list[tuple[str, str]] = []
    for name in KNOWN:
        try:
            committed = at(clone, sha, name)
        except BlobUnreadable:
            committed = None
        label, text = name, committed
        if committed is None:
            # Only a working checkout has one of these, and only some of those. On the endpoint
            # this never fires, because `working_clone` clones with `--no-checkout`.
            local = clone / name
            if local.is_file():
                label, text = (
                    f"{name} (uncommitted)",
                    local.read_text(encoding="utf-8", errors="replace"),
                )
        if not text or not text.strip():
            continue
        rules = _rules_only(text)
        found.append((label, rules[:MAX_CHARS] + TRUNCATED if len(rules) > MAX_CHARS else rules))
    return tuple(found)
