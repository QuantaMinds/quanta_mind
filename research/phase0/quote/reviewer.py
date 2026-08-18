"""Ask for a quote and a fix. Never ask for a line number.

WHAT: `review()` sends a numbered diff and returns findings of the shape {quote, claim, fix}.
WHY:  Five designs repaired the model's line number and all five failed. This one removes the
      field. The model copies code out of the diff; `gate.py` computes the line from where that
      copy sits, so the prose and the anchor cannot disagree -- one is a function of the other.

      THE PROMPT IS DERIVED FROM QODO'S, the top tool of 49 on Martian's offline layer at 67.9%
      precision. Their `existing_code` field is this `quote`; their `improved_code` is this `fix`.
      Their reflection pass validates the snippet against the diff; here that is a string search in
      `gate.py` with no model in it, because a parser can decide it.

      THE ZERO-SCORE LIST IS IN THE PROMPT *AND* IN THE GATE, deliberately. Asking the model to
      abstain is cheap and unreliable; the gate is what makes it true. A rule stated only in a
      prompt is a rule stated only in a docstring.
IMPORTS: stdlib only (json, re).
CONSUMED BY: `run.py` in this package.
"""

from __future__ import annotations

import json
import re

MAX_FINDINGS = 8

PROMPT = """You are reviewing a pull request diff. Report only defects a maintainer must fix
before merging: logic errors, missing error handling, concurrency hazards, security problems,
API contract violations, data-handling mistakes.

DO NOT report any of the following. They will be discarded:
- adding docstrings, type hints or comments
- unused or missing imports, unused variables
- using a more specific exception type
- naming, formatting, style or readability
- anything about a function, class or variable you cannot SEE DEFINED in the diff below —
  it is probably defined elsewhere in the codebase and you are guessing

For each defect return three fields:
- "quote": the EXACT text of a line the diff ADDS (a line beginning with +), copied character for
  character WITHOUT the leading +. This must be text you can see below. Do not paraphrase it, do
  not reformat it, do not invent it.
- "claim": one sentence naming the defect and why it is wrong.
- "fix": the corrected code that should replace the quoted line.

- "evidence": a SECOND exact quote from the diff which, together with "quote", is what makes
  the claim true. If you cannot find one in the diff, you do not have grounds for the claim --
  drop it. Write "SAME" only when the claim rests entirely on the quoted line itself.

Do not give line numbers. The quote is how the finding is located.

Report at most {max_findings}. If the change looks correct, return [] -- that is a valid answer.

Pull request: {title}

```diff
{diff}
```

Respond with ONLY a JSON array of objects, each with keys "quote", "claim", "evidence", "fix"."""


class ReviewFailed(RuntimeError):
    """The model returned nothing parseable. Distinct from a deliberate empty review."""


def _salvage(text: str) -> str | None:
    """Close an array the model was cut off mid-way through writing."""
    start = text.find("[")
    end = text.rfind("}")
    if start < 0 or end < start:
        return None
    return text[start : end + 1] + "]"


def _parse(text: str) -> list[dict[str, str]]:
    m = re.search(r"\[.*\]", text, re.S)
    raw = m.group(0) if m else _salvage(text)
    if raw is None:
        raise ReviewFailed(f"no JSON array and nothing salvageable: {text[:160]!r}")
    try:
        arr = json.loads(raw)
    except json.JSONDecodeError:
        salvaged = _salvage(text)
        if salvaged is None or salvaged == raw:
            raise ReviewFailed(f"reply is not JSON: {text[:160]!r}") from None
        try:
            arr = json.loads(salvaged)
        except json.JSONDecodeError as exc:
            raise ReviewFailed(f"not JSON even salvaged: {exc}") from None
    out: list[dict[str, str]] = []
    for item in arr:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "quote": str(item.get("quote") or ""),
                "claim": str(item.get("claim") or ""),
                "evidence": str(item.get("evidence") or ""),
                "fix": str(item.get("fix") or ""),
            }
        )
    return out[:MAX_FINDINGS]


def review(client: object, title: str, diff: str) -> tuple[list[dict[str, str]], str]:
    """(findings, finish reason). Raises rather than returning [] when the model did not answer."""
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": PROMPT.format(max_findings=MAX_FINDINGS, title=title, diff=diff)}
                ],
            }
        ],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 32768},
    }
    resp = client.generate(body)  # type: ignore[attr-defined]
    finish = str(resp.get("finish", "?"))
    text = str(resp.get("text") or "")
    if not text.strip():
        raise ReviewFailed(f"empty reply, finish={finish}, thoughts={resp.get('thoughts')}")
    return _parse(text), finish
