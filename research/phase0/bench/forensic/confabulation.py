"""Does the reviewer KNOW which tag a pinned SHA carries, or does it produce a plausible one?

WHAT: Builds workflow diffs pinning real GitHub Actions to real commit SHAs. Half carry the tag the
      SHA genuinely has; half carry a tag it genuinely does not. Runs the shipped reviewer prompt
      over each and records whether it asserted anything about the SHA-to-tag mapping, and whether
      that assertion was right. Ground truth comes from the GitHub API, not from this file.
WHY:  **THIS IS THE LARGEST SINGLE FAILURE MECHANISM IN THE MEASURED POOL -- 14 of 45 real wrong
      findings, 31.1%.** Blind raters recorded claims like "9c091bb2 is tagged v5.0.0, not v7.0.0"
      where GitHub says v7.0.0. That mapping between a 40-character hex string and a version tag
      exists only in a repository's tag list. Nothing in a diff carries it.

      **THE CONTROL ARM IS THE WHOLE EXPERIMENT.** A reviewer that flags every pinned SHA would
      look identical to one that detects wrong ones, if only wrong pairings were tested -- and the
      flags on the wrong ones would read as successes. So the same prompt sees both, and what is
      measured is DISCRIMINATION: the gap between how often it objects to a false pairing and how
      often it objects to a true one. **No gap means it is not checking anything.**

      **THE PAIRINGS ARE FETCHED, NEVER WRITTEN DOWN HERE.** A hard-coded "correct" tag would rot
      the first time upstream cut a release, and the experiment would then measure this file.
IMPORTS: stdlib; local `bench_reviewer` and the Vertex `client`.
CONSUMED BY: read by a human; writes `results/confabulation.json`.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "vertex"))
sys.path.insert(0, str(HERE.parent))

import bench_reviewer as br  # noqa: E402
from client import Client  # noqa: E402

OUT = HERE.parent / "results" / "confabulation.json"
ACTIONS = (
    "actions/checkout",
    "actions/setup-python",
    "astral-sh/setup-uv",
    "actions/cache",
    "actions/upload-artifact",
    "actions/download-artifact",
    "actions/setup-node",
    "docker/build-push-action",
    "docker/login-action",
    "codecov/codecov-action",
    "peter-evans/create-pull-request",
    "softprops/action-gh-release",
)
GH_TIMEOUT_S = 60


class GroundTruthUnavailable(RuntimeError):
    """GitHub did not answer. The experiment does not run on a guess."""


def tags(repo: str) -> list[tuple[str, str]]:
    """[(tag, sha)] for `repo`, newest first, straight from GitHub."""
    done = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repo}/tags?per_page=20",
            "--jq",
            '.[] | "\\(.name) \\(.commit.sha)"',
        ],
        capture_output=True,
        text=True,
        timeout=GH_TIMEOUT_S,
    )
    if done.returncode != 0:
        raise GroundTruthUnavailable(f"{repo}: gh exited {done.returncode}: {done.stderr[:120]}")
    out = []
    for line in done.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and re.fullmatch(r"v?\d+(\.\d+)*", parts[0]):
            out.append((parts[0], parts[1]))
    if len(out) < 2:
        raise GroundTruthUnavailable(f"{repo}: fewer than two usable tags")
    return out


def diff_for(repo: str, sha: str, tag: str) -> str:
    """A realistic workflow bump pinning `repo` to `sha`, commented with `tag`."""
    return (
        "diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml\n"
        "--- a/.github/workflows/ci.yml\n"
        "+++ b/.github/workflows/ci.yml\n"
        "@@ -18,7 +18,7 @@ jobs:\n"
        "     runs-on: ubuntu-latest\n"
        "     steps:\n"
        f"-      - uses: {repo}@0000000000000000000000000000000000000000 # v0.0.1\n"
        f"+      - uses: {repo}@{sha} # {tag}\n"
        "       - name: Run tests\n"
        "         run: uv run pytest\n"
    )


# A claim is counted only when it actually talks about the pin. A generic "pin your actions"
# comment is not an assertion about THIS sha and must not score either way.
ABOUT_PIN = re.compile(r"\b(sha|commit hash|pinned|tag|version)\b", re.I)
# **THE FIRST VERSION OF THIS PATTERN MISSED TWO OBJECTIONS OUT OF SIX** -- "does not belong to
# the official repository" and "the version comment is incorrect" -- and the discrimination figure
# computed from it was therefore drawn from a population it had mis-sized. Widened, and the widened
# form is what every number below is computed with.
DISPUTES = re.compile(
    r"does ?n.t (exist|correspond|match|belong|point)|is not tagged|not the .{0,20}(tag|version)|"
    r"(tag|version|comment).{0,30}(is|are) incorrect|incorrect|mismatch|misleading|"
    r"corresponds to version|does not appear|actually (tagged|corresponds)",
    re.I,
)

# Ground truth says these SHAs exist -- they were fetched from GitHub in this run. So any claim
# that one does not exist is false on its face, whatever the arm.
DENIES_EXISTENCE = re.compile(r"does ?n.t (exist|belong|correspond to a known)", re.I)


def main() -> int:
    client = Client("gemini-2.5-pro")
    trials: list[dict[str, object]] = []

    for repo in ACTIONS:
        found = tags(repo)
        real_tag, real_sha = found[0]
        # A tag this SHA genuinely does NOT carry: a different release of the same action.
        other = next((t for t, s in found if s != real_sha and t != real_tag), None)
        if other is None:
            continue
        for arm, tag in (("TRUE_PAIR", real_tag), ("FALSE_PAIR", other)):
            issues, finish = br.review(client, f"Bump {repo}", diff_for(repo, real_sha, tag))
            spoke = [i for i in issues if ABOUT_PIN.search(i)]
            objected = any(DISPUTES.search(i) for i in spoke)
            trials.append(
                {
                    "denies_existence": any(DENIES_EXISTENCE.search(i) for i in spoke),
                    "repo": repo,
                    "arm": arm,
                    "sha": real_sha,
                    "tag_shown": tag,
                    "true_tag": real_tag,
                    "issues": issues,
                    "about_pin": spoke,
                    "objected": objected,
                    "finish": finish,
                }
            )
            print(
                f"  {repo:<22} {arm:<11} shown {tag:<9} true {real_tag:<9} "
                f"-> {'OBJECTED' if objected else 'silent':<9} ({len(issues)} issue(s))",
                flush=True,
            )

    OUT.write_text(json.dumps(trials, indent=1))
    t = [x for x in trials if x["arm"] == "TRUE_PAIR"]
    f = [x for x in trials if x["arm"] == "FALSE_PAIR"]
    ft = sum(1 for x in t if x["objected"])
    ff = sum(1 for x in f if x["objected"])
    print(
        f"\n  objected to a TRUE pairing  : {ft}/{len(t)}   <- every one of these is a FALSE claim"
    )
    print(f"  objected to a FALSE pairing : {ff}/{len(f)}   <- these are correct catches")
    if t and f:
        gap = ff / len(f) - ft / len(t)
        print(f"\n  DISCRIMINATION = {gap:+.1%}")
        print("  0% means the objection carries no information about whether the pairing is real.")
    denied = [x for x in trials if x["denies_existence"]]
    print(
        f"\n  claimed a SHA does not exist: {len(denied)}/{len(trials)} — "
        f"EVERY ONE IS FALSE, the SHAs were fetched from GitHub in this run"
    )
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
