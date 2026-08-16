"""Our reviewer, run over a whole diff, emitting one candidate issue per finding.

WHAT: `review()` sends a unified diff to the model and returns a list of issue descriptions in the
      shape Martian's judge expects -- one sentence per issue, no line anchors.
WHY:  Every other tool on this benchmark reviews a whole diff and is scored on the text of what it
      says. Ours reviews one Python function at a time and is scored on whether the claim is true
      AND anchored to the line it cites. Those are different jobs, so this is a NEW ARM and its
      result is not a re-measurement of the 5.80%.

      THE ANCHOR IS DELIBERATELY NOT ASKED FOR. 87.3% of our claims quote code absent from the
      line they cite, and this benchmark never checks anchors -- it matches issue descriptions
      semantically. Asking for a line number we know to be wrong would add a field the judge
      ignores and let us pretend the defect was tested here. It was not.
IMPORTS: stdlib only (json, re).
CONSUMED BY: `run.py` in this package.
"""

from __future__ import annotations

import json
import re

MAX_ISSUES = 12

PROMPT = """You are reviewing a pull request. Report only defects a maintainer would need to fix
before merging: logic errors, missing error handling, concurrency hazards, security problems,
API contract violations, data-handling mistakes.

Do not report style, formatting, naming, test coverage or documentation unless the change is
actually incorrect. Do not restate what the diff does. Do not speculate about code you cannot
see in the diff.

Report at most {max_issues} issues. If the change looks correct, return an empty list -- that is
a valid and useful answer.

Pull request title: {title}

Unified diff:
```
{diff}
```

Respond with ONLY a JSON array of objects, each: {{"issue": "one sentence naming the specific
defect and why it is wrong"}}"""


class ReviewFailed(RuntimeError):
    """The model returned nothing parseable. Distinct from an empty, deliberate review."""


def _parse(text: str) -> list[str]:
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        raise ReviewFailed(f"no JSON array in reply: {text[:160]!r}")
    try:
        arr = json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        raise ReviewFailed(f"reply is not JSON: {exc}") from None
    out: list[str] = []
    for item in arr:
        s = str(item.get("issue") or "").strip() if isinstance(item, dict) else str(item).strip()
        if s:
            out.append(s)
    return out[:MAX_ISSUES]


def review(client: object, title: str, diff: str) -> tuple[list[str], str]:
    """(issues, finish reason). Raises rather than returning [] when the model did not answer.

    The finish reason is returned and never inferred: a MAX_TOKENS truncation and a deliberate
    empty review print the same thing downstream, and this project has already published a number
    that was really eleven truncations.
    """
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": PROMPT.format(max_issues=MAX_ISSUES, title=title, diff=diff)}],
            }
        ],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 8192},
    }
    resp = client.generate(body)  # type: ignore[attr-defined]
    finish = str(resp.get("finish", "?"))
    text = str(resp.get("text") or "")
    if not text.strip():
        # A truncation and a deliberate empty review are different results and must not collapse.
        raise ReviewFailed(f"empty reply, finish={finish}, thoughts={resp.get('thoughts')}")
    return _parse(text), finish
