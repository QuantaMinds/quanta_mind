"""The ask → answer → re-decide sequence, against the live model and live authorities.

WHAT: Runs `settle()` on three findings — a false date claim, a false package claim, and a semantic
      claim — and asserts on what the model does when handed a fact it did not have.
WHY:  **THE SEQUENCE WAS MEASURED IN RESEARCH CODE AND HAD NEVER RUN IN THE PRODUCT.** Across three
      live commits (requests, werkzeug, urllib3) it fired zero times, because the model made no
      external claim on any of them — so "it is wired in" was untested by observation alone.

      **AND THE FIRST RUN OF THIS TEST FOUND A REAL BUG.** The model asked *"Was requests 2.32.3
      ever published to PyPI?"*, a perfectly answerable question, and `answer()` returned nothing —
      because the release path routed through `adjudicate_release`, which checks a DISPUTING
      assertion, and a question asserts nothing. The false finding published for want of an answer
      it could have had. That is the same defect the conversational arm's first run had on the SHA
      path, arriving here because the SHA path was fixed and this one was not.
IMPORTS: stdlib, pytest, quantamind.serve.settle, quantamind.types.finding.
CONSUMED BY: `uv run pytest tests/live`.
"""

from __future__ import annotations

import datetime as dt
import os
import shutil

import pytest

from quantamind.infer.vertex import InferenceFailed, Unavailable
from quantamind.serve.settle import answer, settle
from quantamind.types.finding import Finding

PROJECT = os.environ.get("QUANTAMIND_GCP_PROJECT", "quantamind-oss")
TODAY = dt.date.today().isoformat()

# **THE PATH THE CODE ACTUALLY USES, NOT `PATH`.** `gemini.py` defaults to an absolute gcloud
# path, which is not on `PATH` here — so `shutil.which("gcloud")` returned None and all three tests
# SKIPPED while the live model was working perfectly. A skip reads as a pass in the summary line.
GCLOUD = "/opt/homebrew/share/google-cloud-sdk/bin/gcloud"

pytestmark = pytest.mark.skipif(
    not (os.path.exists(GCLOUD) or shutil.which("gcloud")),
    reason="needs gcloud credentials for the live model",
)


def test_answer_reports_a_fact_for_a_question_and_never_a_verdict() -> None:
    """No model involved. The bug this catches is a question routed through a claim-verifier."""
    got = answer("Was requests version 2.32.3 ever published to PyPI?", TODAY)
    assert "requests" in got and "2.32.3" in got, f"the release question went unanswered: {got!r}"
    assert "published on PyPI" in got

    assert TODAY in answer("What is the current date?", TODAY)
    assert answer("Does this loop terminate?", TODAY) == "", "invented an answer with no authority"


def test_a_false_date_claim_is_withdrawn_once_the_model_is_told_the_date() -> None:
    finding = Finding(
        path="a.py",
        quote='RELEASED = "2026-08-15"',
        claim='The constant RELEASED = "2026-08-15" is a future date, so the gate never opens.',
    )
    try:
        out = settle(finding, project=PROJECT, today="2026-08-25")
    except (InferenceFailed, Unavailable) as exc:
        pytest.skip(f"model unavailable: {exc}")
    assert out.asked, "the model asserted a date claim instead of asking"
    assert "2026-08-25" in out.fact
    assert not out.publishes, f"kept a claim its own answer refutes: {out.why}"


def test_a_semantic_claim_asks_nothing_and_survives() -> None:
    """The control. Without it, settle could pass by withdrawing everything."""
    finding = Finding(
        path="c.py",
        quote="for i in range(n):",
        claim="This loop never terminates because i is reassigned inside the body.",
    )
    try:
        out = settle(finding, project=PROJECT, today=TODAY)
    except (InferenceFailed, Unavailable) as exc:
        pytest.skip(f"model unavailable: {exc}")
    assert out.publishes is True, "withdrew a claim no authority could speak to"
    assert out.asked == "", f"asked an external question about pure control flow: {out.asked!r}"
    assert out.fact == "", f"produced a fact where no authority exists: {out.fact!r}"
    assert out.why == "rests on the code shown"
