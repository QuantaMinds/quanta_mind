"""The shapes a sentence uses to dispute that a package release exists.

WHAT: The patterns `verify/releases.py` matches against a finding — what counts as disputing a
      release, what a version looks like, and which forms actually BIND a distribution name to one.
WHY:  **`BOUND` IS A SAFETY PROPERTY AND NOT A TIDY-UP.** PyPI has packages called `pin`, `Some`
      and `dependency`. Scanning near a version number for a name-shaped token finds them, and the
      oracle then CONFIRMS — publishing a finding on a name collision, which is the direction
      `docs/engineering/CORRECTIONS.md` entry 8 records a verifier shipping. Only these three
      forms are read as a sentence naming the distribution it is talking about.

      **`NOT_A_PACKAGE` IS A SECOND LAYER AND CANNOT BE THE FIRST.** It is a stop-list of English
      words, and a stop-list against PyPI's namespace is a race that cannot be won — which is why
      the real constraint is that the name must also appear in the diff.
IMPORTS: stdlib re only. The leftmost thing in this layer.
CONSUMED BY: `verify/releases.py`.
"""

from __future__ import annotations

import re

# A finding disputing that a release exists: "awscli 1.45.34 is not on PyPI", "isort 9.0.0b2
# does not exist". Three of 45 real wrong findings are this claim, and all three were false.
DISPUTES_RELEASE = re.compile(
    r"does ?n[o']?t exist|is not (?:on|available|published)|was never (?:released|published)", re.I
)
VERSION = re.compile(r"\b(\d+\.\d+(?:\.\d+)?(?:[abrc]+\d+)?)\b")
# **A NAME BOUND TO THE VERSION BY SYNTAX, NOT BY PROXIMITY.** PyPI has a package called `pin`, and
# one called `Some`. Scanning near the version for a name-shaped token found both and CONFIRMED on
# them -- publishing a finding on the strength of a package nobody was talking about. These are the
# forms in which a sentence actually binds a distribution to a release.
BOUND = re.compile(
    r"([A-Za-z][\w.-]{1,40})\s*={2,3}\s*(\d[\w.!+-]*)"  # name==1.2.3
    r"|([A-Za-z][\w.-]{1,40})\s+(?:version\s+)?v?(\d+\.\d+[\w.!+-]*)"  # name 1.2.3
    r"|version\s+v?(\d+\.\d+[\w.!+-]*)\s+of\s+([A-Za-z][\w.-]{1,40})"  # version 1.2.3 of name
)
# A plausible distribution name. English words are excluded by a stop list rather than by shape,
# because `requests`, `attrs` and `click` are all ordinary words AND real packages.
NAMEISH = re.compile(r"[A-Za-z][\w.-]{1,40}")
NOT_A_PACKAGE = frozenset(
    [
        "the",
        "a",
        "an",
        "this",
        "that",
        "it",
        "is",
        "are",
        "was",
        "were",
        "not",
        "does",
        "doesn",
        "exist",
        "version",
        "package",
        "pinned",
        "on",
        "in",
        "of",
        "and",
        "or",
        "but",
        "pypi",
        "npm",
        "registry",
        "release",
        "released",
        "published",
        "available",
        "never",
        "latest",
        "new",
        "old",
        "to",
        "for",
        "with",
        "from",
        "at",
        "by",
        "as",
        "be",
        "been",
        "being",
        "has",
        "have",
        "had",
        "will",
        "would",
        "should",
        "could",
    ]
)
