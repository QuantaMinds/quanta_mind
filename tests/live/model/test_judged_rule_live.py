"""D1c against the live model: does the judge discriminate, and does failure stay undecided.

WHAT: Runs `judge_all` with the REAL `serve/rule_judge.py` judge and a REAL Vertex call, over a
      known-answer pair and against a project that will refuse.
WHY:  **EVERY OTHER D1c TEST INJECTS A STUB JUDGE, AND A GREEN STUB PROVES THE PLUMBING ONLY.**
      `AGENTS.md`: a green test is not a verified test. Until this file existed, nothing in the
      repository had ever put a prose rule to a model — no live test declares a `model_judged`
      rule, so `just verify` was green over a path that had never run.

      **THE KNOWN-ANSWER PAIR IS THE POINT.** One file plants the exact failure `AGENTS.md` rule 14
      describes — "this is safe because the caller always holds the lock" — and one contains only
      WHY comments. A judge that answered BROKEN to everything would look identical to a working one
      on the first file alone, which is the shape this project keeps mistaking for a result.

      **AND THE REFUSAL PATH RUNS AGAINST THE REAL TRANSPORT.** A unit test can only prove that a
      raising callable becomes `UNDECIDED`; this proves that a real HTTP 403 does, which is the
      failure a deployment actually meets when a project or a quota goes away.
IMPORTS: stdlib, pytest, quantamind.serve.rule_judge, quantamind.types.{settings,standards.rule},
      quantamind.verify.judged_rule.
CONSUMED BY: `uv run pytest tests/live`.
"""

from __future__ import annotations

import os
import shutil

import pytest

from quantamind.serve.rule_judge import judge_with
from quantamind.types.settings import Settings
from quantamind.types.standards.judged import Verdict
from quantamind.types.standards.rule import CheckKind, Rule, Severity
from quantamind.verify.judged_rule import judge_all

PROJECT = os.environ.get("QUANTAMIND_GCP_PROJECT", "quantamind-oss")

# **THE PATH THE CODE ACTUALLY USES, NOT `PATH`.** `shutil.which("gcloud")` returns None here even
# when the live model works perfectly, and a skip reads as a pass in the summary line.
GCLOUD = "/opt/homebrew/share/google-cloud-sdk/bin/gcloud"

pytestmark = pytest.mark.skipif(
    not (os.path.exists(GCLOUD) or shutil.which("gcloud")),
    reason="needs gcloud credentials for the live model",
)

RULE = Rule(
    "comments-explain-why-not-whether",
    "AGENTS.md rule 14: a comment may explain WHY, never assert WHETHER. A safety claim -- "
    "'this is caught later', 'callers always hold the lock' -- belongs in an assertion, a test, "
    "or a returned value, because a comment cannot fail.",
    Severity.MEDIUM,
    CheckKind.MODEL_JUDGED,
)

# **THE PLANTED LINE IS THE ARTEFACT THE ORACLE MUST FIND**, named here so a passing test cannot
# mean "it said BROKEN for some other reason".
PLANTED = "# This is safe because the caller always holds the lock."

VIOLATING = f'''"""A module that breaks the rule on purpose."""


def sweep(paths):
    {PLANTED}
    for path in paths:
        # Any leftover here is caught on the next attempt, so we ignore failures.
        drop(path)
'''

# **THE NEGATIVE FIXTURE MUST NOT NAME THE RULE'S OWN VOCABULARY.** The first version opened
# `"""A module with only WHY comments."""` and the judge quoted THAT LINE as a violation in 3 of 6
# real trials — it was reacting to the label, not the code. A fixture that describes itself in the
# oracle's terms measures the fixture. Every comment below is an ordinary WHY and says nothing
# about comments.
CLEAN = '''"""Remove stale working clones."""


def sweep(paths):
    # Sorted so the output is stable across runs, which the golden file depends on.
    for path in sorted(paths):
        drop(path)
    return len(paths)
'''


def _judge():
    return judge_with(
        Settings(inference_enabled=True, inference_project=PROJECT, gcloud_path=GCLOUD)
    )


def test_the_planted_violation_is_found_and_quoted_from_the_file() -> None:
    """**NAMES THE ARTEFACT IT MUST FIND.** Not "a finding exists" — this exact line."""
    records = judge_all([RULE], "src/sweep.py", VIOLATING, _judge())

    assert len(records) == 1
    found = records[0]
    assert found.verdict is Verdict.BROKEN, f"missed the planted claim: {found.why}"
    # The quote must be in the file — `judge()` downgrades an unanchorable one to UNDECIDED, so
    # a BROKEN verdict reaching here has already been located in the source.
    assert found.quote in VIOLATING
    assert found.site.line > 0, "a violation the reader cannot navigate to"


def test_a_file_with_only_why_comments_is_not_reported() -> None:
    """**THE OTHER HALF OF THE KNOWN-ANSWER PAIR.**

    Without this, a judge that answered BROKEN to every file would pass the test above. This is the
    difference between an oracle and a rubber stamp.
    """
    records = judge_all([RULE], "src/sweep.py", CLEAN, _judge())

    assert len(records) == 1
    assert records[0].verdict is not Verdict.BROKEN, (
        f"reported a violation in a file with no whether-claim: {records[0].quote!r}"
    )


def test_a_refused_project_is_undecided_and_never_met() -> None:
    """**A REAL HTTP 403 MUST NOT READ AS COMPLIANCE.**

    The unit suite proves a raising callable becomes UNDECIDED. This proves the real transport's
    real failure does, which is what a deployment meets when a project or a quota disappears.
    """
    refused = judge_with(
        Settings(
            inference_enabled=True,
            inference_project="no-such-project-quantamind-xyz",
            gcloud_path=GCLOUD,
        )
    )
    records = judge_all([RULE], "src/sweep.py", VIOLATING, refused)

    assert len(records) == 1
    assert records[0].verdict is Verdict.UNDECIDED
    assert records[0].why, "an undecided record must say why it could not be decided"
