"""What this change does, in the author's terms, and whether it did what it said.

WHAT: `summarise(diff, stated, project)` returns a `Summary`: the change in plain words, whether it
      achieves the goal the author stated, and the reasoning. `Unavailable` when there are no
      credentials; a `Summary` with `consulted=False` is never fabricated here — the caller decides.
WHY:  **THE REVIEW'S ONE QUESTION IS WHETHER THE CHANGE DID WHAT IT SAID WITHOUT DISTURBING
      ANYTHING ELSE**, and neither half can be answered from the diff alone. "What it said" comes
      from the author's own title and body; a goal inferred from the code makes the question
      circular, because a diff always achieves what the diff does.

      **THIS IS A DIFFERENT TASK FROM FINDING DEFECTS, AND THE EVIDENCE AGAINST US IS ABOUT THE
      OTHER ONE.** Four blind pools put raw findings 66.7-82.1% wrong; that measured a model
      asserting a bug exists in code a human then had to check. Summarising a diff and comparing it
      to a paragraph the author wrote is a reading-comprehension task with both halves present in
      the prompt. It may well be reliable where finding defects was not — **and it is not yet
      measured, so nothing here may be stated as though it were.**

      **`achieves_goal` IS THREE-VALUED FOR THAT REASON.** True, False, and `None` for "the author
      stated no goal to check against" — an empty description is a real answer, and inventing a
      goal to grade against would manufacture agreement. A reviewer reading "achieves its goal"
      must be able to trust that a goal existed.
IMPORTS: stdlib, `ingest.diff` for `Stated`, and `infer.gemini` for the transport it already owns.
CONSUMED BY: `serve/deep_review.py`.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass

from quantamind.infer import gemini
from quantamind.ingest.diff import Stated

MAX_DIFF_CHARS = 60_000
PROMPT = """Review this change for the developer about to merge it. Plain words. Be brief: a
sentence or two each, never a paragraph. They are waiting.

WHAT THE AUTHOR SAYS IT IS FOR:
{goal}

THE DIFF:
{diff}

WHAT IMPORTS THE CHANGED FILES (static Python imports only; dynamic imports and other languages
are invisible to this list, so absence is not proof nothing depends on them):
{importers}

Reply with ONLY a JSON object, no markdown fence:
{{
  "what_changed": "ONE OR TWO sentences, plain words, naming the function or file. What the code
                   now does differently. Not a restatement of the diff.",
  "achieves_goal": true | false | null,
  "reasoning": "One sentence. If false, name exactly what is missing or contradicted. If null,
                say the author stated no goal.",
  "impact": "ONE sentence on whether the callers listed above are affected — say plainly if they
             are not, and say so cautiously if the list is empty, because an empty list means no
             static import was found rather than that nothing depends on this."
}}
Set achieves_goal to null if and only if the goal section is empty or states no purpose."""


@dataclass(frozen=True, slots=True)
class Summary:
    """A plain-words account of the change, and whether it matches what was promised."""

    what_changed: str
    achieves_goal: bool | None
    reasoning: str
    impact: str = ""
    """One sentence on the callers. Empty when the model was not given an importer list."""

    def __post_init__(self) -> None:
        if not self.what_changed.strip():
            raise ValueError("a summary with nothing in it is not a summary; raise instead")


def summarise(
    diff: str,
    stated: Stated,
    *,
    project: str,
    importers: Sequence[str] = (),
    gcloud: str = "gcloud",
    location: str = "us-central1",
) -> Summary:
    """Ask the model what changed and whether it matches the author's stated purpose."""
    if not diff.strip():
        raise gemini.InferenceFailed("no diff to summarise")
    token = gemini._token(gcloud)
    url = (
        f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}"
        f"/locations/{location}/publishers/google/models/{gemini.MODEL}:generateContent"
    )
    goal = stated.text() or "(the author wrote no description)"
    # **AN EMPTY LIST IS SAID IN WORDS, NOT LEFT AS A BLANK.** A blank section reads to a
    # model as "no information", and it would fill the gap; the sentence makes the absence
    # itself the fact, which is what `parse/importers` can actually support.
    imports = "\n".join(f"- {name}" for name in importers) or (
        "(no static Python import of these files was found anywhere in the repository)"
    )
    answer = gemini._post(
        url,
        token,
        {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": PROMPT.format(
                                goal=goal, diff=diff[:MAX_DIFF_CHARS], importers=imports
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 2048},
        },
    )
    candidates = answer.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise gemini.InferenceFailed(f"no candidates in reply: {str(answer)[:160]}")
    first = candidates[0]
    if first.get("finishReason") != "STOP":
        raise gemini.InferenceFailed(f"finishReason {first.get('finishReason')!r}, not STOP")
    text = str(first.get("content", {}).get("parts", [{}])[0].get("text", "")).strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        raise gemini.InferenceFailed(f"reply was not JSON: {text[:160]}") from None
    achieved = payload.get("achieves_goal")
    return Summary(
        what_changed=str(payload.get("what_changed", "")).strip(),
        achieves_goal=achieved if isinstance(achieved, bool) else None,
        reasoning=str(payload.get("reasoning", "")).strip(),
        impact=str(payload.get("impact", "")).strip(),
    )
