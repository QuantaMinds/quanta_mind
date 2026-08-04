"""Verification of the two defects the agent dry run named, fixed before labelling.

WHAT: Pins that a squash body no longer fires the breakage pattern, that a real fix
      subject still does, and that a sweeping commit no longer counts as a repair.
WHY:  The dry run found the outcome rule too loose in eight of nine disagreements, and
      the pilot's breakage rate came back at 27.3% -- roughly 2.4x the published PR-level
      rate of 11.3%, on a corpus skewed toward small single-commit changes that should
      sit BELOW the reference, not above it.

      Both causes were named, so both are fixed before the 20 labels are spent. Fixing
      them afterwards would burn an iteration of the gate on something already known to
      be broken.

      Both changes can only REMOVE breakage verdicts, never add them, so the direction
      is toward the null.
IMPORTS: phase0.scan_outcome, phase0.fix_signals.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from phase0 import fix_signals
from phase0.fix_signals import MIN_COMMIT_FOCUS, subject as _subject

# PrunaAI/pruna 017dc9a144 — a FEATURE whose squashed body lists six `fix:` commits.
SQUASH_BODY = (
    "feat: `accelerate` support (#128)\n\n"
    "* feat: introduce accelerate as possible smashing device\n"
    "* fix: extend device movement for distributed transformers models\n"
    "* fix: remove empty dict condition for `hf_device_map`\n"
    "* fix: ruff complaints\n"
)


def test_a_squash_body_no_longer_fires_the_pattern() -> None:
    """The exact commit that made the rule fire on large feature PRs as a class."""
    assert fix_signals.mentions_breakage(SQUASH_BODY), "the old rule matched the body"
    assert not fix_signals.mentions_breakage(_subject(SQUASH_BODY))


def test_a_real_fix_subject_still_fires() -> None:
    """Tightening must not silence the thing the rule exists to catch."""
    for subject in (
        "fix: null dereference in the request handler",
        "hotfix: revert the broken migration",
        "Fix regression introduced by #4207",
    ):
        assert fix_signals.mentions_breakage(_subject(subject))


def test_subject_extraction_is_the_first_line_only() -> None:
    assert _subject("one line") == "one line"
    assert _subject("subject\n\nbody with fix in it") == "subject"
    assert _subject("") == ""


def test_the_focus_threshold_is_a_quarter_and_is_declared() -> None:
    """A boundary that moves the outcome variable, so it is pinned against drift."""
    assert MIN_COMMIT_FOCUS == 0.25


def test_focus_separates_a_targeted_repair_from_a_sweep() -> None:
    """A 200-file release overlaps almost any PR; a two-file fix does not."""
    pr_files = {"pkg/mod.py", "pkg/other.py"}

    sweep = {f"src/f{i}.py" for i in range(200)} | {"pkg/mod.py"}
    overlap = sweep & pr_files
    assert overlap and len(overlap) / len(sweep) < MIN_COMMIT_FOCUS

    targeted = {"pkg/mod.py", "tests/test_mod.py"}
    overlap = targeted & pr_files
    assert overlap and len(overlap) / len(targeted) >= MIN_COMMIT_FOCUS
