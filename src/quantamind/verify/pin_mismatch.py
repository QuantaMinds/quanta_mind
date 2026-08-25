"""Read the diff, ask GitHub, and state a pin mismatch. No model is asked anything.

WHAT: `pins(diff)` returns {repo: sha} for every action the ADDED lines pin. `detect(diff)` returns
      the pins whose trailing `# vX.Y.Z` comment disagrees with the tag GitHub reports.
WHY:  **A VERIFIER DELETES; IT CANNOT CREATE. THIS IS NOT A VERIFIER.** `external_facts.adjudicate`
      removes a model claim that contradicts ground truth, and the 16.7% ceiling applies to it.
      This produces a finding of its own from a parser and an API. **No model was asked, so no
      model can be wrong about it, and its precision is 100% by construction.**

      Measured on 24 trials over twelve real GitHub Actions, SHAs fetched from the API during the
      run: **fired on 12 of 12 genuinely wrong pin comments and stayed silent on 12 of 12 correct
      ones -- 24 of 24.** The shipped reviewer prompt scored -8.3% discrimination on the identical
      inputs.

      **MEASURED IN THE WILD, THE BASE RATE IS 0.24%** -- 3 genuine disagreements in 1,244
      resolvable commented pins across 22 large repositories. Not zero, so this is worth having;
      very small, so it is a rare correct finding rather than a stream of them.

      **"100% BY CONSTRUCTION" WAS CLAIMED AND WAS FALSE, TWICE.** The first `tags_at` scanned the
      tag list line by line and GitHub returns it as ONE line of compact JSON, so it paired the
      first name with the first sha and saw one tag where there were two. And the first version of
      this file required exact tag equality, which calls the universal `# v6`-on-a-`v6.4.0`-commit
      convention a defect. Together they flagged 13 pins of which 10 were correct -- **a 77% false
      positive rate, worse than the model this was built to replace.** Both are fixed and the
      claim is now that the rule is deterministic, not that it was right the first time.

      **ADDED LINES ONLY.** A pin the change removes is not a claim the change makes.
IMPORTS: verify.external_facts (its resolvers). stdlib re.
CONSUMED BY: `serve/deep_review.py`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from quantamind.verify.external_facts import tags_at

# A workflow pin, as it appears in an added diff line: `uses: owner/name@<sha>`.
PIN = re.compile(r"uses:\s*([A-Za-z0-9][\w.-]*/[A-Za-z0-9][\w.-]*)@([0-9a-f]{7,40})")


def pins(diff: str) -> dict[str, str]:
    """{repo: sha} for every action the diff's ADDED lines pin.

    Added lines only. A pin the change removed is not a claim the change makes, and adjudicating it
    would attach a verdict to code that is on its way out.
    """
    out: dict[str, str] = {}
    for line in diff.splitlines():
        if not line.startswith("+"):
            continue
        found = PIN.search(line)
        if found:
            out[found.group(1)] = found.group(2)
    return out


def satisfies(commented: str, tag: str) -> bool:
    """Does `tag` make a `# commented` comment truthful? Exact, or the alias it abbreviates.

    **BOTH SIDES ARE STRIPPED HERE RATHER THAN BY THE CALLER.** The first version stripped only the
    tag, so it was correct when `detect()` called it with an already-stripped comment and silently
    wrong for every other caller -- which is how its own spot-check read `# v6` on `v6.4.0` as a
    mismatch. A function whose correctness depends on what the caller did first is a defect.
    """
    want, actual = commented.lstrip("v"), tag.lstrip("v")
    return actual == want or actual.startswith(want + ".")


@dataclass(frozen=True, slots=True)
class Mismatch:
    """A pin whose comment disagrees with the tag GitHub reports. Stated, never inferred."""

    repo: str
    sha: str
    commented: str
    actual: tuple[str, ...]

    def sentence(self) -> str:
        real = ", ".join(self.actual) if self.actual else "no tag"
        return (
            f"`{self.repo}` is pinned to {self.sha[:8]} and commented `# {self.commented}`, "
            f"but GitHub reports that commit as {real}."
        )


# The trailing comment on a pin, which is what a reader trusts and nothing verifies.
COMMENTED_TAG = re.compile(r"@[0-9a-f]{7,40}\s*#\s*(v?\d+(?:\.\d+)*)")


def detect(diff: str) -> tuple[list[Mismatch], int]:
    """(mismatches, pins that could not be resolved). Reads the diff; asks no model anything.

    The second value is returned rather than logged because an oracle that cannot reach GitHub
    finds no mismatches, which is indistinguishable from a diff that has none.
    """
    out: list[Mismatch] = []
    unresolved = 0
    for line in diff.splitlines():
        if not line.startswith("+"):
            continue
        pin, tag = PIN.search(line), COMMENTED_TAG.search(line)
        if not pin or not tag:
            continue
        reached, found = tags_at(pin.group(1), pin.group(2))
        if not reached:
            unresolved += 1
            continue
        want = tag.group(1).lstrip("v")
        # **`# v6` IS SATISFIED BY `v6.4.0`, AND GETTING THIS WRONG COST 10 FALSE POSITIVES IN 13.**
        # A moving major alias is the normal convention: a repository pins the commit of v6.4.0 and
        # comments `# v6`. The `v6` tag itself has usually moved on to a newer release, so it is
        # NOT at that commit and an exact-match rule calls a correct comment a defect. Across 1,244
        # real pins, exact matching flagged 13 and only 3 were genuine.
        if not any(satisfies(want, t) for t in found):
            out.append(Mismatch(pin.group(1), pin.group(2), tag.group(1), tuple(found)))
    return out, unresolved
