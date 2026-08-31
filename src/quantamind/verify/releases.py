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
CONSUMED BY: `verify/publishable.py`. Its patterns live in `verify/release_claims.py`.
"""

from __future__ import annotations

import urllib.error
import urllib.request

from quantamind.verify.external_facts import Adjudicated, Verdict
from quantamind.verify.release_claims import (
    BOUND,
    DISPUTES_RELEASE,
    NAMEISH,
    NOT_A_PACKAGE,
    VERSION,
)

PYPI_TIMEOUT_S = 20


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


def package_exists(name: str) -> tuple[bool, bool]:
    """(reached, the package exists at all). Distinct from whether a given RELEASE exists.

    **THIS IS WHAT SEPARATES A TRUE ABSENCE-CLAIM FROM AN UNIDENTIFIABLE SUBJECT.** Without it,
    "flask 99.99.99 does not exist" and "wibble 99.99.99 does not exist" look identical: no package
    in the sentence has that release, so both come back UNRESOLVABLE and both findings drop. The
    first is TRUE and was being thrown away.
    """
    try:
        with urllib.request.urlopen(
            f"https://pypi.org/pypi/{name}/json", timeout=PYPI_TIMEOUT_S
        ) as r:
            return True, r.status == 200
    except urllib.error.HTTPError as e:
        return True, e.code != 404
    except (urllib.error.URLError, TimeoutError, OSError):
        return False, False


def adjudicate_release(finding: str, context: str = "") -> Adjudicated:
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

    # **REFUTING AND CONFIRMING GET DIFFERENT EVIDENCE BARS, BECAUSE THEY HAVE OPPOSITE RISKS.**
    # A wrong REFUTED costs one true finding: bad, bounded, and the finding simply does not publish.
    # A wrong CONFIRMED publishes a false claim with an authority behind it, which is the failure
    # `docs/engineering/CORRECTIONS.md` entry 8 records. So refuting accepts any nearby
    # candidate; confirming accepts only a name the sentence syntactically BINDS to the version.
    around = finding[max(0, version.start() - 40) : version.end() + 40]
    nearby = [
        t
        for t in NAMEISH.findall(around)
        if t.lower() not in NOT_A_PACKAGE and not VERSION.fullmatch(t)
    ]
    bound = [
        g
        for m in BOUND.finditer(finding)
        for g in (m.group(1), m.group(3), m.group(6))
        if g and g.lower() not in NOT_A_PACKAGE
    ]

    reached_any = False
    for name in nearby:
        reached, has_release = released(name, want)
        reached_any = reached_any or reached
        if reached and has_release:
            return Adjudicated(
                Verdict.REFUTED, f"the finding says {name} {want} does not exist; PyPI serves it"
            )

    # **AND THE BOUND NAME MUST APPEAR IN THE DIFF, or nothing is confirmed.** PyPI has packages
    # called `pin`, `Some` and `dependency`, so a stop-list of English words is a race that cannot
    # be won -- "Some dependency 91.7.3 does not exist" confirmed on `dependency` until this check
    # existed. A finding about a package the reviewed change never mentions is not one to publish
    # on the strength of a name collision. With no context supplied, CONFIRMED is unavailable and
    # the finding drops, which is the safe direction.
    for name in bound:
        if not context or name not in context:
            continue
        reached, is_package = package_exists(name)
        if reached and is_package:
            return Adjudicated(
                Verdict.CONFIRMED,
                f"{name} is on PyPI, appears in the diff, and has no release {want}",
            )

    if not reached_any:
        return Adjudicated(Verdict.UNRESOLVABLE, "PyPI did not answer", reachable=False)
    return Adjudicated(
        Verdict.UNRESOLVABLE,
        f"nothing the sentence binds to {want} is a package the diff mentions; not identifiable",
    )
