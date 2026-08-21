"""The isolated judge: decide, per candidate finding, whether it may be published.

WHAT: `adjudicate()` takes ONE candidate issue and the diff it was made about, and returns
      KEEP or DROP with the deciding fact. `run()` applies it to a whole arm and reports how many
      false positives were discarded and how many true findings survived.
WHY:  **THIS IS THE ONLY LEVER ON THIS BENCHMARK AND THE MEASUREMENT SAYS SO.** Our reviewer with
      nits allowed finds 100 of 173 golden issues -- 57.8%, against Qodo's 57.2% -- and needs 464
      candidates to do it against their 152. The recall is already there; what is missing is
      anything that discards our own bad findings. `docs/product/why-their-f1-is-higher.md` puts
      the target as a number: **discard ~85% of false positives while keeping the true ones** and
      precision reaches 64.7% with F1 61.0%, past Greptile's 54.5% and Qodo's published 60.1%.

      **THE JUDGE DEFAULTS TO DROP, AND THAT IS THE WHOLE DESIGN.** On 2026-08-20 a judge that
      graded findings on their merits agreed with a careful rater on 34.9% of them and RATIFIED
      the reviewer's own hallucinations -- it accepted invented claims about which tag a pinned SHA
      carries and repeated the reviewer's belief that 2026 was in the future. A judge asked "is
      this plausible?" answers yes to a confident sentence. So it is asked the opposite: **the
      finding must be SHOWN to be true by lines present in the diff, and anything else is dropped.**

      **IT NEVER SEES THE REVIEWER'S REASONING.** One candidate, one diff, no other findings, no
      rank, no confidence, no arm label. In the product this is `verify/`, which `AGENTS.md` rule 7
      forbids from importing `infer/` -- the layer adjudicating the claims cannot start trusting
      the layer that made them.

      **THE FAMILY LIMITATION IS REAL AND IS NOT HIDDEN.** The reviewer here is `gemini-2.5-pro`
      and so is this judge, because no other capable model is reachable from this project. A
      same-family judge is the WEAK case -- it shares the subject's blind spots and will keep
      false positives it happens to agree with. **Whatever it discards is therefore a floor**, and
      the different-family judge is the arm still owed.
IMPORTS: stdlib (concurrent.futures, json, re). Local: the Vertex `client`.
CONSUMED BY: `run_judge.py` in this package.
"""

from __future__ import annotations

import concurrent.futures
import json
import re

MAX_WORKERS = 8

PROMPT = """You are the last check before a code-review comment is posted to a real pull request.
A reviewer has proposed ONE issue about the diff below. Decide whether it may be published.

YOUR DEFAULT IS DROP. A confident, well-written sentence is not evidence. Publish only if the
lines in this diff SHOW the claim to be true.

DROP the finding if any of these hold:
- deciding it would need a fact this diff cannot supply: a package version, a released tag, what
  another file does, what a caller passes, the current date, whether a name exists elsewhere
- the code it describes is not in the diff, or the diff shows something different
- it is hedged: "may", "might", "could", "potentially", "consider", "it is possible"
- it restates what the change does, or praises it
- it is a style, naming, formatting or documentation preference and the code is not actually wrong
- it asserts a test is wrong. This pull request was MERGED and its tests passed
- you cannot point at the specific added or removed line that makes it true

KEEP the finding only if you can name the line in the diff that makes it true, and a maintainer
would have to change something before merging.

Diff:
```
{diff}
```

Proposed issue: {issue}

Respond with ONLY a JSON object:
{{"line": "the exact diff line that decides it, or empty", "verdict": "KEEP" or "DROP",
"why": "one sentence giving the deciding fact"}}"""


# **THE SECOND PROMPT, AND THE DIFFERENCE IS THE DIAGNOSIS.** `PROMPT` above asks whether a finding
# is TRUE, and it answers that well: it dropped 89 of 464 -- nits, typos, style preferences and
# claims the diff contradicts -- and kept 366. But the benchmark counts a candidate as a FALSE
# POSITIVE when no human wrote that comment, whether or not it is true. Four separate reports of
# the same `forEach` hazard in four files are all true; the humans wrote one.
#
# **So truth is the wrong bar. Materiality is the bar.** This is what Qodo's judge filters on --
# "confidence AND RELEVANCE", and a "Precise" mode that "reports only issues that clearly require
# developer action". The pair is the experiment: same evidence requirement, different question.
PROMPT_MATERIAL = """You are the last check before a code-review comment is posted to a real pull
request. A reviewer has proposed ONE issue about the diff below.

A human maintainer reviewing this pull request wrote a handful of comments. Your question is NOT
"is this true?" -- it is "IS THIS ONE OF THE COMMENTS A MAINTAINER WOULD HAVE WRITTEN?"

YOUR DEFAULT IS DROP. Most true observations are not worth a comment.

DROP unless ALL of these hold:
- the diff itself shows the claim to be true; you can name the line
- a maintainer would require a change before merging, not merely note it
- it is the PRIMARY defect in that code, not a secondary observation about it
- it is specific to what this pull request changed, not a pre-existing property of the file

DROP on sight if:
- deciding it needs a fact this diff cannot supply: a version, a tag, another file, a caller, the
  current date
- it is hedged: "may", "might", "could", "potentially", "consider"
- it is style, naming, formatting, documentation, or test coverage and the code is not wrong
- it asserts a test is wrong. This pull request was MERGED and its tests passed
- it repeats an issue that is obvious from the same change in another file: the maintainer writes
  that comment ONCE

Diff:
```
{diff}
```

Proposed issue: {issue}

Respond with ONLY a JSON object:
{{"line": "the exact diff line that decides it, or empty", "verdict": "KEEP" or "DROP",
"why": "one sentence giving the deciding fact"}}"""


class JudgeFailed(RuntimeError):
    """The judge returned nothing parseable. Never silently a KEEP."""


def _parse(text: str) -> tuple[bool, str, str]:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise JudgeFailed(f"no JSON in reply: {text[:120]!r}")
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        raise JudgeFailed(f"reply is not JSON: {exc}") from None
    verdict = str(obj.get("verdict", "")).strip().upper()
    if verdict not in ("KEEP", "DROP"):
        raise JudgeFailed(f"verdict {verdict!r} is neither KEEP nor DROP")
    return verdict == "KEEP", str(obj.get("why", ""))[:200], str(obj.get("line", ""))[:200]


def adjudicate(
    client: object, diff: str, issue: str, prompt: str = PROMPT
) -> tuple[bool, str, str]:
    """(keep, why, line). A failure RAISES; it is never turned into a publish."""
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt.format(diff=diff, issue=issue)}]}],
        # 32768, NOT 8192. Gemini bills thinking tokens against this ceiling, so a judge that
        # reasons about a 20k-character diff finishes MAX_TOKENS and returns nothing. At 8192 this
        # failed on **136 of 464 candidates** -- and every failure was recorded as a DROP, which is
        # a harness error wearing a filter's verdict. Same defect as `judge14.py`, twice.
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 32768},
    }
    answer = client.generate(body)  # type: ignore[attr-defined]
    if answer["finish"] != "STOP":
        raise JudgeFailed(f"finished {answer['finish']!r}, not STOP")
    return _parse(str(answer["text"]))


def screen(
    client: object, diff: str, issues: list[str], prompt: str = PROMPT
) -> list[dict[str, object]]:
    """Adjudicate every candidate for one pull request, independently and in parallel.

    **INDEPENDENTLY IS THE POINT.** Judging the list together lets the model rank them against each
    other and keep "the best of these", which is a different and much weaker question than whether
    any single one is true. Each call sees one issue and the diff, and nothing else.
    """
    out: list[dict[str, object]] = [{} for _ in issues]
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(adjudicate, client, diff, i, prompt): n for n, i in enumerate(issues)
        }
        for done in concurrent.futures.as_completed(futures):
            n = futures[done]
            try:
                keep, why, line = done.result()
                out[n] = {"issue": issues[n], "keep": keep, "why": why, "line": line}
            except Exception as exc:
                # **NOT A DROP. A FAILURE.** Recording an error as a DROP makes a broken judge look
                # like a working filter -- the discard rate rises, precision rises with it, and
                # nothing says the calls never happened. `failed` is carried separately and
                # `run_judge.py` refuses to score a run whose failure rate is material.
                out[n] = {
                    "issue": issues[n],
                    "keep": None,
                    "why": f"JUDGE FAILED: {type(exc).__name__}: {exc}"[:200],
                    "line": "",
                    "failed": True,
                }
    return out
