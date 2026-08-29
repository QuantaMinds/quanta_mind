"""The oracle side of the conversation: answer the model's question, then let it re-decide.

WHAT: `answer(question, repo)` returns the FACT an authority holds. `redecide(client, ...)` hands
      that fact back and asks only whether the finding still stands. `settle()` is the fallback
      verifier for questions the answerer cannot turn into a fact.
WHY:  **AN ANSWERER IS NOT A VERIFIER, AND CONFLATING THEM MADE THE FIRST RUN MEASURE NOTHING.**
      `verify.external_facts.adjudicate()` checks an ASSERTION against ground truth. A question
      asserts nothing, so it returned UNRESOLVABLE for every question the model asked and the arm
      reported a 2% settle rate that described the harness. Stages one and two of a three-stage
      loop, called the loop.

      **THE ANSWERER NEVER SAYS WHETHER THE FINDING IS RIGHT.** It reports what GitHub or PyPI
      holds and stops. A tool that returns "this looks wrong" is a second model wearing a parser's
      clothes, and five of those have been measured failing.

      **AND THE RE-DECIDE STEP DOES NOT ASK THE MODEL TO GRADE ITSELF.** It supplies a fact the
      model did not have and asks only whether the finding stands on it. Asking a model to assess
      its own output is the lever measured five times at 8.5-16.8% retained discrimination.
IMPORTS: stdlib; the product's `verify` oracles; the Vertex `client` type only for typing.
CONSUMED BY: `conversational_arm.py`.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from quantamind.verify.external_facts import (
    Verdict,
    adjudicate,
    sha_exists,
    tags_at,
)
from quantamind.verify.releases import adjudicate_release

# `owner/name` and a commit hash, as they appear inside the model's question.
NAMES_REPO = re.compile(r"\b([A-Za-z0-9][\w.-]*/[A-Za-z0-9][\w.-]*)\b")
NAMES_SHA = re.compile(r"\b([0-9a-f]{7,40})\b")

# **THE MODEL RE-DECIDES GIVEN THE FACT. IT IS NOT ASKED WHETHER IT WAS RIGHT.** Asking a model to
# grade its own finding is the lever measured five times at 8.5-16.8% retained discrimination. This
# gives it something it did not have and asks only whether the finding still stands on it.
REDECIDE = """You wrote this code-review finding:

{claim}

You asked: {question}

The answer, from the authoritative source, is:

{fact}

Given that answer, does the finding still stand? Answer with ONLY a JSON object:
{{"stands": true or false, "why": "one short sentence"}}"""


# "What is today's date?" was asked five times and answered zero times. It is the cheapest oracle
# there is and it was simply not wired in — the arm reported those as unanswerable, which reads as
# a limit of the architecture rather than of the harness.
ASKS_DATE = re.compile(
    r"\b(today'?s? date|current date|what is today|date .*(now|current))\b", re.I
)


def answer(question: str, repo_fallback: str, sha_fallback: str = "") -> tuple[str, bool]:
    """(a FACT stating what the authority says, whether it could be established).

    **THIS IS AN ANSWERER, NOT A VERIFIER, AND THE DISTINCTION IS WHY THE FIRST RUN MEASURED
    NOTHING.** `adjudicate()` checks an assertion against ground truth; a QUESTION asserts nothing,
    so there is nothing for it to check and it returned UNRESOLVABLE for every question the model
    asked. The conversational architecture needs the fact itself.

    **It never says whether the finding is right.** It reports what GitHub or PyPI holds and stops.
    """
    if ASKS_DATE.search(question):
        return f"Today's date is {dt.date.today().isoformat()}.", True

    # **"the given commit hash" names no hash, and eight questions were phrased that way.** The
    # subject is in the finding's own text, exactly as it was for `pin_mismatch`, so it is passed
    # in rather than required of the question.
    shas = [x for x in NAMES_SHA.findall(question) if not x.isdigit()]
    if not shas and sha_fallback:
        shas = [sha_fallback]
    repos = [r for r in NAMES_REPO.findall(question) if "/" in r]
    for repo in [*repos, repo_fallback]:
        if not repo or not shas:
            break
        reached, exists = sha_exists(repo, shas[0])
        if not reached:
            continue
        if not exists:
            return f"{shas[0][:8]} is not a commit in {repo}.", True
        reached, found = tags_at(repo, shas[0])
        if reached:
            tags = ", ".join(found) if found else "no tag"
            return f"{shas[0][:8]} in {repo} carries: {tags}.", True

    release = adjudicate_release(question)
    if release.verdict is not Verdict.NO_CLAIM:
        return release.detail, release.reachable
    return "", False


def settle(question: str, claim: str, repo: str) -> tuple[str, str]:
    """(verdict name, detail) from the oracles, resolved against the MODEL'S QUESTION.

    **THE FIRST VERSION PASSED THE CLAIM AND THE FINDING'S OWN REPOSITORY, AND MEASURED ITS OWN
    ROUTING.** The model asked "in `actions/setup-python`, what tag corresponds to 5fda3b95?" -- a
    perfectly answerable question -- and the harness looked up `aws/aws-cli@5fda3b95`, because
    `repo` is the repository the FINDING was about, not the one the QUESTION names. GitHub
    answered "no", the oracle said UNRESOLVABLE, and the arm reported a 2% settle rate that
    described this function rather than the architecture.

    **Building a conversational arm and then not using the conversation is the defect**, and it is
    the one this experiment exists to avoid: the question is the artefact, so the question is what
    gets resolved. The claim is still passed as a fallback for the release oracle, whose subject is
    a package name that the question may phrase differently.
    """
    named = NAMES_REPO.findall(question)
    for hint in [*named, repo]:
        sha = adjudicate(question, repo_hint=hint)
        if sha.verdict is not Verdict.NO_CLAIM:
            return sha.verdict.name, sha.detail
    for text in (question, claim):
        rel = adjudicate_release(text)
        if rel.verdict is not Verdict.NO_CLAIM:
            return rel.verdict.name, rel.detail
    return Verdict.NO_CLAIM.name, "neither oracle recognised a claim it can resolve"


def redecide(client: Any, claim: str, question: str, fact: str) -> bool | None:
    """Does the finding still stand given the fact? None when the model did not answer cleanly."""
    reply = client.generate(
        {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": REDECIDE.format(claim=claim, question=question, fact=fact)}],
                }
            ],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 2048},
        }
    )
    text = str(reply.get("text") or "")
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        return bool(json.loads(text[start : end + 1]).get("stands"))
    except json.JSONDecodeError:
        return None
