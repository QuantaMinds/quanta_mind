"""What counts as a commit reacting to breakage.

WHAT: The revert and fix-message patterns, and the word-boundary rules that stop
      them firing on innocent commits.
WHY:  Split from scan_outcome.py, which owns walking history. This module owns the
      one judgement call in the outcome variable, and it is worth isolating
      because the Day 2 gate (>=16/20 agreement with hand-labelling) is really a
      gate on these patterns.

      Word boundaries are not cosmetic. `PHASE0_PREREGISTRATION.md` “Outcome variable” writes the
      pattern as
      `fix|bug|broke|regress|hotfix|revert`, and matched as a bare substring that
      fires on "prefix", "suffix", "debug" and "prefixes" — none of which say
      anything about breakage. RUNBOOK section 2.3 expects a 5-20% base rate and
      calls >40% "counting routine follow-ups"; substring matching is one of the
      quickest ways to get there.

      `refactor` deliberately does not match. RUNBOOK section 1.3 pins it: a
      refactor landing the next day is not evidence the PR broke anything.
IMPORTS: stdlib re. Nothing from phase0.
CONSUMED BY: scan_outcome.py; tests/outcome/test_scan.py.
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


# A repair is aimed at the thing it repairs. A commit touching two hundred files that
# happens to include one of ours is a release, a reformat or a sweeping refactor -- it
# overlaps almost any PR by construction. Requiring the PR's files to be a real share of
# what the commit touched separates "aimed at this" from "passed over this".
#
# Chosen a priori at one quarter, not fitted: the pilot's admitted records have a median
# of two changed files, so a genuine follow-up fix is small. The direction is toward the
# null -- it can only remove BROKE verdicts, never add them.
MIN_COMMIT_FOCUS = 0.25


def subject(message: str) -> str:
    """The first line, which is the only part that describes the commit.

    A squash merge concatenates every constituent commit message into the body, so a
    feature branch containing one commit that began `fix:` produced a body matching
    FIX_PATTERN -- and the rule fired on large feature PRs as a class. Matching the
    subject alone is what the pattern always meant.
    """
    return message.splitlines()[0] if message else ""


def is_focused(touched: frozenset[str], changed: frozenset[str]) -> bool:
    """Whether a later commit is substantially about the PR's files.

    Takes filename sets rather than a Commit so the rules stay free of GitPython: what
    counts as a breakage signal is a decision, and decisions should be testable without
    a repository.
    """
    if not touched:
        return False
    overlap = touched & changed
    return bool(overlap) and len(overlap) / len(touched) >= MIN_COMMIT_FOCUS
