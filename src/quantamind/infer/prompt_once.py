"""One prompt in, the reply's text out. No schema, no parsing, no findings.

WHAT: `ask(prompt, project=...)` sends one prompt and returns the reply as text.
WHY:  **`read()` RETURNS `Finding`s AND ENFORCES THE REVIEW SCHEMA**, which is right for a review
      and wrong for everything else. The conversational settle step asks the model about a claim it
      already made — "what fact would settle this", "does it still stand given this" — and needs the
      raw answer. Putting that through the finding parser fails on a reply that was never meant to
      be a finding, and the failure would look like the model declining to answer.

      **THE TRUNCATION CHECK IS KEPT.** A cut-off reply reads as a shorter answer rather than a
      broken one, and that is the failure shape this project keeps mistaking for a result.
IMPORTS: infer.gemini (its transport and errors). Same layer.
CONSUMED BY: `serve/settle.py`.
"""

from __future__ import annotations

from quantamind.infer.gemini import MODEL, InferenceFailed, _post, _token


def ask(
    prompt: str,
    *,
    project: str,
    location: str = "us-central1",
    gcloud: str = "/opt/homebrew/share/google-cloud-sdk/bin/gcloud",
    model: str = MODEL,
) -> str:
    """One prompt, the reply's text. **Split from `read()` because it parses nothing.**

    `read()` returns `Finding`s and enforces the review schema. The conversational settle step asks
    the model a question about a claim it already made and needs the raw answer, so putting it
    through the finding parser would fail on a reply that was never meant to be a finding.

    **The truncation check stays.** A cut-off reply reads as a shorter answer rather than a broken
    one, which is the failure shape this project keeps mistaking for a result.
    """
    token = _token(gcloud)
    url = (
        f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}"
        f"/locations/{location}/publishers/google/models/{model}:generateContent"
    )
    answer = _post(
        url,
        token,
        {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 4096},
        },
    )
    candidates = answer.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise InferenceFailed(f"no candidates in reply: {str(answer)[:160]}")
    first = candidates[0]
    if isinstance(first, dict) and first.get("finishReason") != "STOP":
        raise InferenceFailed(f"finishReason {first.get('finishReason')!r}, not STOP")
    parts = first.get("content", {}).get("parts", [{}])
    return str(parts[0].get("text", ""))
