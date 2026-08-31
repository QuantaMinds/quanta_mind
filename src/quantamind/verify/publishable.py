"""Apply every oracle to one finding and decide whether it may be published.

WHAT: `gate(finding, diff)` runs the external-fact oracles over a finding's claim and returns a
      `Ruling` saying whether it publishes, which oracle spoke, and what the authority said.
WHY:  **THE ORACLES WERE BUILT AND MEASURED AND FOR A WHILE NOT WIRED IN.** `serve/deep_review.py`
      kept a finding when a parser could locate its quote in the diff and nothing else, so a
      finding whose quote was real and whose CLAIM was false about a fact GitHub or PyPI holds
      still published. It has called `gate()` since `978bbda`; this paragraph went on describing
      the gap for several commits after it closed, which is the same defect in prose — a docstring
      asserting a state of the world that a reader has no way to check.
      Measured live: shown twelve real actions pinned to SHAs fetched from the API during the run,
      the reviewer objected to 6 of 12 CORRECT pin/tag pairings -- discrimination -8.3%, a coin
      flip -- and in 7 of 24 trials said a SHA did not exist that had just been fetched.

      **THE ORDER IS ANCHOR FIRST, THEN ORACLE, AND IT IS NOT ARBITRARY.** Anchoring is free and
      local; the oracles cost a network call each. A finding whose quote is not in the diff is
      dropped before anything is asked of GitHub.

      **`UNRESOLVABLE` DROPS THE FINDING.** A claim we could not check is not one we publish, and
      collapsing it into "fine" is exactly the failure being fixed -- an unanswerable question
      answered confidently. → `docs/engineering/CORRECTIONS.md` entry 8, where a verifier
      that defaulted the other way confirmed every false claim it was built to refute.
IMPORTS: types.finding, verify.{external_facts,pin_mismatch,releases}. Nothing to its right.
CONSUMED BY: `serve/deep_review.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from quantamind.types.finding import Finding
from quantamind.verify.external_facts import Verdict, adjudicate
from quantamind.verify.pin_mismatch import pins
from quantamind.verify.releases import adjudicate_release


@dataclass(frozen=True, slots=True)
class Ruling:
    """Whether the finding publishes, and the authority's own words for why not."""

    publishes: bool
    oracle: str
    detail: str
    # **WHY IT WAS DROPPED, AS A VALUE.** A caller that had to match "unresolvable" inside
    # `detail` would be reading prose to decide a count, and the prose is written for a human.
    # False means an authority contradicted the claim; True means nobody could settle it.
    unresolvable: bool = False

    def sentence(self) -> str:
        return f"{'kept' if self.publishes else 'dropped'} by {self.oracle}: {self.detail}"


def gate(finding: Finding, diff: str) -> Ruling:
    """Check every external claim this finding makes. Silence from the oracles means publish.

    A finding making no checkable external claim is returned as publishable. **That is not a
    statement that it is true** -- most wrong findings are semantic and no oracle reaches them.
    It says only that nothing here refuted it.
    """
    claim = finding.claim
    sha = adjudicate(claim, repo_hint="", pinned=pins(diff))
    if sha.verdict is Verdict.REFUTED:
        return Ruling(False, "sha-oracle", sha.detail)
    if sha.verdict is Verdict.UNRESOLVABLE:
        return Ruling(False, "sha-oracle", f"unresolvable, so not published — {sha.detail}", True)

    release = adjudicate_release(claim, context=diff)
    if release.verdict is Verdict.REFUTED:
        return Ruling(False, "release-oracle", release.detail)
    if release.verdict is Verdict.UNRESOLVABLE:
        return Ruling(
            False, "release-oracle", f"unresolvable, so not published — {release.detail}", True
        )

    return Ruling(True, "no-oracle-applies", "no external claim an oracle can settle")
