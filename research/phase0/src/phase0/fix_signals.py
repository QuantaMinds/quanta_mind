"""What counts as a commit reacting to breakage.

WHAT: The revert and fix-message patterns, and the word-boundary rules that stop
      them firing on innocent commits.
WHY:  Split from scan_outcome.py, which owns walking history. This module owns the
      one judgement call in the outcome variable, and it is worth isolating
      because the Day 2 gate (>=16/20 agreement with hand-labelling) is really a
      gate on these patterns.

      Word boundaries are not cosmetic. §3.2 writes the pattern as
      `fix|bug|broke|regress|hotfix|revert`, and matched as a bare substring that
      fires on "prefix", "suffix", "debug" and "prefixes" — none of which say
      anything about breakage. RUNBOOK section 2.3 expects a 5-20% base rate and
      calls >40% "counting routine follow-ups"; substring matching is one of the
      quickest ways to get there.

      `refactor` deliberately does not match. RUNBOOK section 1.3 pins it: a
      refactor landing the next day is not evidence the PR broke anything.
IMPORTS: stdlib re. Nothing from phase0.
CONSUMED BY: scan_outcome.py; tests/test_scan_outcome.py.
"""

from __future__ import annotations

import re

# Whole words only. "prefix" and "debug" must not match; "bugfix" must, so it is
# listed in its own right rather than left to a substring to catch.
FIX_PATTERN = re.compile(
    r"\b("
    r"fix|fixes|fixed|fixing|fixup|hotfix|bugfix|bugfixes"
    r"|bug|bugs|buggy"
    r"|broke|broken|breaks|breakage"
    r"|regress|regressed|regression|regressions"
    r"|revert|reverts|reverted"
    r")\b",
    re.IGNORECASE,
)

# `git revert` writes "This reverts commit <sha>." — a definitive link, not a guess.
REVERTS_COMMIT = re.compile(r"reverts\s+commit\s+([0-9a-f]{7,40})", re.IGNORECASE)

# Conventional-commit revert form: `revert: <subject>` or `Revert "<subject>"`.
REVERT_SUBJECT = re.compile(r'^\s*revert[:\s]|^\s*revert\s+"', re.IGNORECASE)


def mentions_breakage(message: str) -> bool:
    """True if the message claims to be reacting to something being wrong."""
    return bool(FIX_PATTERN.search(message))


def reverts(message: str, target_sha: str) -> bool:
    """True if this commit explicitly reverts the given commit.

    Matched on the SHA rather than the subject line, so a later unrelated commit
    whose subject happens to start with "revert" is not attributed to this PR.
    Prefix comparison because git abbreviates SHAs to varying lengths.
    """
    if not target_sha:
        return False
    for candidate in REVERTS_COMMIT.findall(message):
        if target_sha.startswith(candidate) or candidate.startswith(target_sha):
            return True
    return False


def looks_like_a_revert(message: str) -> bool:
    """True for a revert-shaped subject with no SHA to confirm it.

    Weaker than `reverts` and used only alongside file overlap: on its own it
    would attribute any revert in the window to this PR.
    """
    return bool(REVERT_SUBJECT.match(message))
