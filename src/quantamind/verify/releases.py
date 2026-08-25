"""Refute the reviewer's claim that a package release does not exist. It usually does.

WHAT: `adjudicate_release(finding)` checks an "X does not exist" claim against PyPI and returns
      `REFUTED`, `CONFIRMED`, `UNRESOLVABLE` or `NO_CLAIM`. `released(name, version)` is the lookup.
WHY:  **THREE OF 45 REAL WRONG FINDINGS ASSERT THAT A RELEASE IS MISSING, AND ALL THREE WERE
      FALSE** -- `awscli 1.45.34`, `isort 9.0.0b2`, a `mirrors-mypy` tag. One HTTP request settles
      each, and the model cannot: a package index is not in a diff.

      **THE DETECTOR FOR THIS CLASS IS A CLOSED ROAD AND THIS IS DELIBERATELY NOT IT.** 176 distinct
      pinned versions across ten real requirement files: every single one exists. A pinned version
      that does not exist fails CI on the first install, so almost none survive on a main branch,
      and a checker hunting them would be correct and would never fire.
      -> `research/phase0/bench/forensic/registry_prevalence.py`

      **THE VERIFIER IS WORTH IT ANYWAY, AND THE DIRECTION OF THE CLAIM IS THE DIFFERENCE.** It does
      not look for missing releases. It refutes an assertion that one is missing, and that does not
      depend on the base rate at all.

      **ITS DEFAULT IS `UNRESOLVABLE`, AND THE FIRST VERSION DEFAULTED THE OTHER WAY.** It took the
      first name-shaped token before the version -- `The`, in "The version 1.45.34 of awscli does
      not exist" -- asked PyPI for `The/1.45.34`, got a 404, and **CONFIRMED every false claim it
      was built to refute.** A verifier whose failure mode is confirming is worse than none: the
      confabulation acquires a fact behind it, and a well-grounded false finding has none of
      confabulation's tell.
IMPORTS: verify.external_facts (its `Verdict` and `Adjudicated`). stdlib re, urllib.
CONSUMED BY: `serve/deep_review.py`.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request

from quantamind.verify.external_facts import Adjudicated, Verdict

PYPI_TIMEOUT_S = 20

# A finding disputing that a release exists: "awscli 1.45.34 is not on PyPI", "isort 9.0.0b2
# does not exist". Three of 45 real wrong findings are this claim, and all three were false.
DISPUTES_RELEASE = re.compile(
    r"does ?n[o']?t exist|is not (?:on|available|published)|was never (?:released|published)", re.I
)
VERSION = re.compile(r"\b(\d+\.\d+(?:\.\d+)?(?:[abrc]+\d+)?)\b")
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


def released(name: str, version: str) -> tuple[bool, bool]:
    """(reached, exists) for one PyPI release. A 404 IS an answer; a timeout is not.

    **THE DETECTOR FOR THIS CLASS IS A CLOSED ROAD AND THIS IS NOT IT.** 176 distinct pinned
    versions across ten real requirement files: every one exists. A pinned version that does not
    exist fails CI on the first install, so almost none survive on a main branch, and a checker
    hunting them would be correct and never fire. -> `bench/forensic/registry_prevalence.py`

    **THE VERIFIER IS WORTH IT ANYWAY, AND THE DIFFERENCE IS THE DIRECTION OF THE CLAIM.** It does
    not look for missing releases; it refutes the reviewer's assertion that a release is missing,
    which is 3 of 45 real wrong findings and does not depend on that base rate at all.
    """
    try:
        with urllib.request.urlopen(
            f"https://pypi.org/pypi/{name}/{version}/json", timeout=PYPI_TIMEOUT_S
        ) as r:
            return True, r.status == 200
    except urllib.error.HTTPError as e:
        return True, e.code != 404
    except (urllib.error.URLError, TimeoutError, OSError):
        return False, False


def adjudicate_release(finding: str) -> Adjudicated:
    """Check an "X does not exist" claim about a package release against PyPI.

    **THE DEFAULT IS `UNRESOLVABLE`, AND THE FIRST VERSION DEFAULTED THE OTHER WAY.** It took the
    first name-shaped token before the version, which is `The` in "The version 1.45.34 of awscli
    does not exist" -- so it asked PyPI for `The/1.45.34`, got a 404, and returned **CONFIRMED for
    every false claim it was built to refute.** A verifier whose failure mode is confirming is
    worse than no verifier: the reviewer's confabulation acquires a fact behind it, and a
    well-grounded false finding has none of confabulation's tell.

    So every name-shaped token in the sentence is tried, and a claim whose subject cannot be
    identified is UNRESOLVABLE -- which drops the finding rather than publishing it.
    """
    if not DISPUTES_RELEASE.search(finding):
        return Adjudicated(Verdict.NO_CLAIM, "no release-absence claim")
    version = VERSION.search(finding)
    if not version:
        return Adjudicated(Verdict.UNRESOLVABLE, "disputes a release but names no version")

    want = version.group(1)
    candidates = [
        t
        for t in NAMEISH.findall(finding)
        if t.lower() not in NOT_A_PACKAGE and not VERSION.fullmatch(t)
    ]
    any_reached = False
    for name in candidates:
        reached, exists = released(name, want)
        any_reached = any_reached or reached
        if reached and exists:
            return Adjudicated(
                Verdict.REFUTED, f"the finding says {name} {want} does not exist; PyPI serves it"
            )
    if not any_reached:
        return Adjudicated(Verdict.UNRESOLVABLE, "PyPI did not answer", reachable=False)
    return Adjudicated(
        Verdict.UNRESOLVABLE,
        f"no package named in the finding has a release {want}; the subject is not identifiable",
    )
