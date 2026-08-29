"""Resolve the external facts a finding asserts, so the model is never the one deciding them.

WHAT: `adjudicate(finding, repo_hint, pinned)` resolves the commit-SHA claim in a finding against
      GitHub and returns `REFUTED`, `CONFIRMED` or `UNRESOLVABLE`. `sha_exists` and `tags_at` are
      the resolvers it and `verify/pin_mismatch.py` share.
WHY:  **THE MODEL CANNOT CHECK AND DOES NOT DECLINE.** Measured live on 2026-08-24 over twelve real
      GitHub Actions whose SHAs were fetched from the API during the run: the reviewer objected to
      6 of 12 CORRECT pin/tag pairings and 5 of 12 WRONG ones -- discrimination -8.3%, which is a
      coin flip. In 7 of 24 trials it stated the commit SHA does not exist; every one had just been
      fetched from GitHub. This class is 14 of 45 real wrong findings, the single largest.

      **A 40-CHARACTER HEX STRING CARRIES NO INFORMATION ABOUT A VERSION NUMBER.** That mapping
      lives in a repository's tag list and nothing in a diff contains it. So the fix is not a better
      prompt -- five have moved nothing -- it is to stop asking. The code looks it up.

      **THE SHA COMES FROM THE DIFF, NOT FROM THE MODEL'S PROSE.** Measured on the same 24 trials:
      resolving only SHAs the finding quotes left 7 of 15 pin-related findings unadjudicated,
      because the model writes "the new commit SHA for `actions/checkout` does not correspond to a
      known commit" and never states which. **The subject of the claim is in the diff**, and taking
      it from there is what moves this oracle from adjudicating 8 of 15 to adjudicating nearly all.

      **`UNRESOLVABLE` IS A THIRD VALUE AND IT DROPS THE FINDING.** A claim we could not check is
      not one we publish. Collapsing it into `CONFIRMED` is exactly how the present failure
      happens: an unanswerable question answered confidently.

      **AN ORACLE THAT CANNOT REACH GITHUB RETURNS `UNRESOLVABLE` FOR EVERYTHING, WHICH LOOKS
      IDENTICAL TO A GATE WORKING PERFECTLY.** `Adjudicated.reachable` is False in that case so a
      caller can count it, and a run whose unresolvable rate is high is a failed run, not a clean
      one -- the same defect as a filter that admits nothing across a whole pass.
IMPORTS: types.verdict. stdlib subprocess/re. Nothing to its right -- `verify/` may not see
      `infer/`, and this needs nothing from it: a claim is text, and GitHub is the authority.
CONSUMED BY: `serve/deep_review.py`. `verify/pin_mismatch.py` and `verify/releases.py`
            share its resolvers and its `Verdict`.
"""

from __future__ import annotations

import enum
import json
import re
import subprocess
from dataclasses import dataclass

GH_TIMEOUT_S = 30

# A SHA claim looks like a 7-to-40 character hex run that is not an ordinary English word. Seven is
# git's own abbreviation floor; below it a match is noise.
SHA = re.compile(r"\b([0-9a-f]{7,40})\b")
# `owner/name`, as it appears in a workflow pin or in prose about one.
REPO = re.compile(r"\b([A-Za-z0-9][\w.-]*/[A-Za-z0-9][\w.-]*)\b")
# The claim shapes this oracle can adjudicate. Anything else about a SHA is left alone.
DENIES_EXISTENCE = re.compile(
    r"does ?n[o']?t (exist|correspond|belong|point)|is not a (valid|known)|no such commit", re.I
)
ASSERTS_TAG = re.compile(r"\b(?:is |as |carries |tagged )v?(\d+(?:\.\d+)*)", re.I)


class Verdict(enum.Enum):
    """What the oracle found. Three values; `UNRESOLVABLE` is not a soft `CONFIRMED`."""

    REFUTED = "refuted"
    CONFIRMED = "confirmed"
    UNRESOLVABLE = "unresolvable"
    NO_CLAIM = "no external claim to check"


@dataclass(frozen=True, slots=True)
class Adjudicated:
    """The verdict, what was checked, and whether the oracle could reach its authority."""

    verdict: Verdict
    detail: str
    reachable: bool = True

    def publishable(self) -> bool:
        """**Only a CONFIRMED or claim-free finding may publish.** UNRESOLVABLE does not."""
        return self.verdict in (Verdict.CONFIRMED, Verdict.NO_CLAIM)


def _gh(path: str) -> tuple[bool, str]:
    """(reached, body). False means GitHub did not answer -- distinct from answering 'no'."""
    done = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=GH_TIMEOUT_S)
    if done.returncode == 0:
        return True, done.stdout
    # **A 404 OR A 422 IS AN ANSWER: the object is not there. Anything else is a failure to
    # reach.** GitHub returns 422 "No commit found for SHA", not 404, when a commit does not
    # exist -- so treating only 404 as an answer meant `sha_exists` reported reached=False for
    # every absent commit, and the one verdict this oracle can never reach is the one it exists to
    # confirm. Caught by a named-artefact test asking it to deny a fabricated SHA; "does it return
    # something" would have passed. -> tests/live/test_oracles_name_their_artefact.py
    if any(code in done.stderr for code in ("404", "422")) or "Not Found" in done.stderr:
        return True, ""
    return False, done.stderr[:160]


def sha_exists(repo: str, sha: str) -> tuple[bool, bool]:
    """(reached, exists). Asks GitHub for the commit rather than inferring from a name."""
    reached, body = _gh(f"repos/{repo}/commits/{sha}")
    return reached, bool(body.strip())


def tags_at(repo: str, sha: str) -> tuple[bool, list[str]]:
    """(reached, every tag pointing at `sha`). Empty with reached=True means genuinely untagged.

    **PARSED AS JSON, NOT SCANNED LINE BY LINE.** The first version matched `"name"` and `"sha"`
    per line, and GitHub returns this endpoint as ONE line of compact JSON -- so it paired the
    first name with the first sha and returned a single tag where there were two. Every moving
    major alias (`v7` beside `v7.0.1`, pointing at the same commit) was therefore invisible, and a
    correct `# v7` comment was reported as a mismatch. It inflated a base-rate scan before anyone
    read a result from it.

    **ALL tags are returned, not the first**, because `# v7` and `# v7.0.1` are both truthful
    comments on a commit carrying both, and a checker that knows only one of them manufactures
    disagreements for a living.
    """
    reached, body = _gh(f"repos/{repo}/tags?per_page=100")
    if not reached or not body.strip():
        return reached, []
    try:
        listing = json.loads(body)
    except json.JSONDecodeError:
        return False, []
    return True, [
        str(t["name"])
        for t in listing
        if isinstance(t, dict) and str(t.get("commit", {}).get("sha", "")).startswith(sha[:7])
    ]


def adjudicate(
    finding: str, repo_hint: str = "", pinned: dict[str, str] | None = None
) -> Adjudicated:
    """Check the SHA claim in `finding` against GitHub. See the module docstring for the rules."""
    shas = [s for s in SHA.findall(finding) if not s.isdigit()]
    repos = [r for r in REPO.findall(finding) if "/" in r]
    repo = repo_hint or (repos[0] if repos else "")

    # **The finding names a repository and disputes its pin without quoting the SHA.** That is the
    # common shape, not an edge case, and the diff knows which commit is meant.
    if (
        not shas
        and pinned
        and repo in pinned
        and (DENIES_EXISTENCE.search(finding) or ASSERTS_TAG.search(finding))
    ):
        shas = [pinned[repo]]

    if not shas:
        return Adjudicated(
            Verdict.NO_CLAIM, "no commit SHA is named and the diff pins none it disputes"
        )

    # **A HEX TOKEN IS NOT A CLAIM ABOUT A COMMIT.** A cache key or a colour constant reached
    # here and `publishable.gate` DROPPED the finding -- its only demonstrated behaviour over 38
    # real findings. An external claim we cannot settle still drops.
    # → `docs/findings/WHY_THE_ORACLES_NEVER_FIRE_2026-08.md`
    disputes = bool(DENIES_EXISTENCE.search(finding) or ASSERTS_TAG.search(finding))
    if not repo and not disputes:
        return Adjudicated(
            Verdict.NO_CLAIM,
            f"names {shas[0][:8]}, but disputes nothing about it -- a hex token is not a claim",
        )

    if not repo:
        return Adjudicated(
            Verdict.UNRESOLVABLE, f"names {shas[0][:8]} but no repository to resolve it in"
        )

    sha = shas[0]
    reached, exists = sha_exists(repo, sha)
    if not reached:
        return Adjudicated(
            Verdict.UNRESOLVABLE, f"GitHub did not answer for {repo}@{sha[:8]}", reachable=False
        )

    if DENIES_EXISTENCE.search(finding):
        if exists:
            return Adjudicated(
                Verdict.REFUTED,
                f"the finding says {sha[:8]} does not exist; GitHub returns it in {repo}",
            )
        return Adjudicated(Verdict.CONFIRMED, f"{sha[:8]} is genuinely absent from {repo}")

    claimed = ASSERTS_TAG.search(finding)
    if claimed and exists:
        reached, tags = tags_at(repo, sha)
        if not reached:
            return Adjudicated(
                Verdict.UNRESOLVABLE, f"could not read tags for {repo}", reachable=False
            )
        want = claimed.group(1)
        if any(t.lstrip("v") == want for t in tags):
            return Adjudicated(Verdict.CONFIRMED, f"{sha[:8]} is tagged v{want}")
        return Adjudicated(
            Verdict.REFUTED,
            f"the finding says {sha[:8]} is v{want}; GitHub reports "
            f"{', '.join(tags) if tags else 'no tag at that commit'}",
        )

    return Adjudicated(Verdict.UNRESOLVABLE, f"a claim about {sha[:8]} this oracle cannot decide")
