"""Ask whether a claim can be settled from the diff alone, and drop it when it cannot.

WHAT: `judge_one()` sends a surviving finding and its diff to the model and returns YES/NO plus the
      stated dependency. `keyword_flag()` is the free mechanical approximation, run alongside for
      comparison.
WHY:  87% of design nine's remaining wrong findings -- 13 of 15 -- rest on facts a diff cannot
      supply. That a package version exists on a registry. That today is not 2026. That a merged
      pull request's passing test is nonetheless broken. That a commit hash exists in someone
      else's repository.

      OUR EXISTING GATE CANNOT CATCH THESE. `G-outer` fires only when a claim quotes an identifier
      absent from the diff, which is 7.4% of findings. These claims quote nothing absent; they
      assert facts about the world.

      SO THIS IS WHERE A MODEL IS ALLOWED TO RUN. This project's rule is that a parser must answer
      anything a parser can. No parser decides "does this version exist on PyPI", so the rule does
      not apply and the judgement is delegated -- narrowly, to one question with a yes/no answer.

      SEVERITY IS NOT ASKED. Our own rejection filter moved nothing and Greptile published that LLM
      severity rating is "nearly random". Two measurements, same conclusion.
IMPORTS: stdlib only (json, re). Local: the Vertex `client`.
CONSUMED BY: `run10.py` in this package.
"""

from __future__ import annotations

import json
import re

# The free approximation, scored alongside the model so the model's value is measurable rather
# than assumed. If this catches as much, the model call is not earning its cost.
KEYWORD = re.compile(
    r"does not exist|non-existent|no such version|never been released|is invalid because|"
    r"not a valid|no version of|future date|incorrect year|actually uploaded|"
    r"will fail|will cause .* to fail|assertion is incorrect|test .*(will fail|is incorrect)",
    re.I,
)

PROMPT = """You are checking whether a code-review claim can be SETTLED using only the diff below.

Answer NO if deciding the claim would require any of:
- what versions or files exist in a package registry, container registry or remote repository
- today's date, or whether a timestamp is in the future
- the result of running a test, a build, or CI
- the contents of a file that is not in the diff
- the behaviour of a library whose source is not in the diff

Answer YES only if a careful reader could settle the claim by reading the diff alone.

This is NOT a question about whether the claim is important, or severe, or well written.
It is only about whether the diff contains enough to decide it.

CLAIM: {claim}

QUOTED CODE: {quote}

DIFF:
```
{diff}
```

Respond with ONLY a JSON object:
{{"decidable": true or false, "needs": "the one fact outside the diff that would be
required, or empty if decidable"}}"""


class GateFailed(RuntimeError):
    """The gate did not return a decision. Never silently a pass."""


def keyword_flag(claim: str) -> bool:
    """True when the free regex thinks the claim reaches outside the diff."""
    return bool(KEYWORD.search(claim))


def judge_one(client: object, claim: str, quote: str, diff: str) -> tuple[bool, str]:
    """(decidable, what it needs). Raises rather than defaulting to publish.

    Qodo's equivalent handler sets score = 7 on exception, which publishes on error. This raises,
    because a gate that fails open is a gate that reports its own failures as approvals.
    """
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": PROMPT.format(claim=claim, quote=quote, diff=diff[:100_000])}],
            }
        ],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 8192},
    }
    resp = client.generate(body)  # type: ignore[attr-defined]
    text = str(resp.get("text") or "")
    if not text.strip():
        raise GateFailed(f"empty reply, finish={resp.get('finish')}")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise GateFailed(f"no JSON in reply: {text[:120]!r}")
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        raise GateFailed(f"reply is not JSON: {exc}") from None
    return bool(obj.get("decidable")), str(obj.get("needs") or "")
