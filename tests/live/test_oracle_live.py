"""The oracle against the real GitHub API, both directions.

WHAT: Resolves a real action pin whose tag is fetched during the run, and requires the detector to
      fire on a genuinely wrong comment and stay silent on a correct one.
WHY:  **THE SILENT DIRECTION IS THE ONE THAT MATTERS.** A detector that fires on every pin would
      look identical to a correct one if only wrong pins were tested, and its noise would read as
      catches. The shipped reviewer scored -8.3% discrimination on exactly this pair of arms.

      **AND AN ORACLE THAT CANNOT REACH GITHUB FINDS NOTHING**, which is indistinguishable from a
      diff with nothing wrong -- so the unresolved count is asserted to be zero rather than assumed.
IMPORTS: stdlib, pytest, quantamind.verify.pin_mismatch.
CONSUMED BY: `uv run pytest tests/live`.
"""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from quantamind.verify.pin_mismatch import detect

REPO = "actions/checkout"


def _tags() -> list[tuple[str, str]]:
    done = subprocess.run(
        ["gh", "api", f"repos/{REPO}/tags?per_page=20"], capture_output=True, text=True, timeout=60
    )
    if done.returncode != 0:
        return []
    return [(t["name"], t["commit"]["sha"]) for t in json.loads(done.stdout)]


pytestmark = pytest.mark.skipif(
    shutil.which("gh") is None, reason="needs gh; this test reads the real GitHub API"
)


def _diff(sha: str, tag: str) -> str:
    return f"+      - uses: {REPO}@{sha} # {tag}\n"


def test_it_fires_on_a_wrong_comment_and_is_silent_on_a_right_one() -> None:
    tags = _tags()
    if len(tags) < 2:
        pytest.skip("GitHub did not return two tags to compare")
    real_tag, real_sha = tags[0]
    other = next(t for t, s in tags if s != real_sha and t != real_tag)

    right, unresolved_right = detect(_diff(real_sha, real_tag))
    assert unresolved_right == 0, "GitHub was unreachable; this run proves nothing"
    assert right == [], (
        f"fired on a CORRECT pin — every one of these would be a false claim: {right}"
    )

    wrong, unresolved_wrong = detect(_diff(real_sha, other))
    assert unresolved_wrong == 0
    assert len(wrong) == 1, f"missed a genuinely wrong pin comment ({real_sha[:8]} is {real_tag})"
    said = wrong[0].sentence()
    assert real_sha[:8] in said and other in said and real_tag in said, (
        f"the finding must name the pin, what was claimed and what GitHub says: {said}"
    )
