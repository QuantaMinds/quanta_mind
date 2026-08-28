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

      **BOUNDED, BECAUSE A CONVENTION FILE CAN BE ENORMOUS.** A 4,000-line handbook would crowd out
      the diff in the prompt and cost more than the review. The cap is per file and the truncation
      is stated, so a reader is never told the whole document was considered when half of it was.

      **READ FROM GIT AT THE COMMIT UNDER REVIEW.** The clone has no working tree, and a change that
      EDITS the conventions must be judged against the version it proposes.
IMPORTS: stdlib, `ingest.blob`. Nothing to its right.
CONSUMED BY: `infer/change_review.py`.
"""

from __future__ import annotations

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
TRUNCATED = "\n\n[... truncated: this document is longer than the review reads ...]"


def written(clone: Path, sha: str) -> tuple[tuple[str, str], ...]:
    """Every convention document this repository carries at `sha`, in order of directness.

    **AN UNREADABLE CLONE YIELDS NOTHING RATHER THAN RAISING.** Conventions are context: a review
    without them is weaker, and a review that failed because a git call did is worse. The caller
    already learns a clone is broken from every other read that needs it.
    """
    found: list[tuple[str, str]] = []
    for name in KNOWN:
        try:
            text = at(clone, sha, name)
        except BlobUnreadable:
            continue
        if not text or not text.strip():
            continue
        found.append((name, text[:MAX_CHARS] + TRUNCATED if len(text) > MAX_CHARS else text))
    return tuple(found)
