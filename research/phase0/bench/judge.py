"""Match candidate issues to golden comments, using Martian's own judge prompt and aggregation.

WHAT: `verdicts()` judges every (golden, candidate) pair for one pull request and returns the
      true positives, false positives and false negatives exactly as
      `step3_judge_comments.py` aggregates them: a golden is matched if any candidate matches it,
      a candidate is a false positive if it matched no golden.
WHY:  The prompt below is copied verbatim from their pipeline rather than paraphrased. A judge we
      wrote ourselves would make every number here a comparison between judges, and the whole
      reason for running their benchmark is that the ground truth and the scoring are not ours.

      OUR JUDGE MODEL IS NOT THEIRS. They score with Claude and GPT-5.2; we hold Vertex
      credentials and neither of those. So the same Gemini judge is applied to every arm, ours
      included, and calibrated against their published numbers before anything is concluded --
      see the P0 bar in
      `docs/plans/preregistrations/reviewer/martian-comparison-preregistration.md`.
IMPORTS: stdlib only (concurrent.futures, json, re, time, urllib.error). Local: the
      Vertex `client`.
CONSUMED BY: `run.py` in this package.
"""

from __future__ import annotations

import concurrent.futures
import json
import re
import sys as _sys
import time
import urllib.error
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "vertex"))
from client import VertexError

# Copied verbatim from code_review_benchmark/step3_judge_comments.py. Do not reword: a changed
# judge prompt silently changes every number it produces and nothing would fail.
JUDGE_PROMPT = """You are evaluating AI code review tools.
Determine if the candidate issue matches the golden (expected) comment.

Golden Comment (the issue we're looking for):
{golden_comment}

Candidate Issue (from the tool's review):
{candidate}

Instructions:
- Determine if the candidate identifies the SAME underlying issue as the golden comment
- Accept semantic matches - different wording is fine if it's the same problem
- Focus on whether they point to the same bug, concern, or code issue

Respond with ONLY a JSON object:
{{"reasoning": "brief explanation", "match": true/false, "confidence": 0.0-1.0}}"""

MAX_WORKERS = 12
TRANSPORT_RETRIES = 4

JUDGE_TOKENS = 2048
"""Output budget for one verdict, DOUBLED on a MAX_TOKENS finish rather than failed.

A fixed cap makes the more verbose model look like the less accurate one: `gemini-2.5-flash` lost
8 pairs to truncated JSON where `gemini-2.5-pro` lost 1, and every lost pair scored as a
non-match."""


class JudgeFailed(RuntimeError):
    """The judge did not return a decision. Never silently a non-match."""


def _parse(text: str) -> tuple[bool, float]:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise JudgeFailed(f"no JSON in judge reply: {text[:120]!r}")
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        raise JudgeFailed(f"judge reply is not JSON: {exc}") from None
    return bool(obj.get("match")), float(obj.get("confidence") or 0.0)


def _one(client: object, golden: str, candidate: str) -> tuple[bool, float]:
    """One pair. Retries a TRANSPORT failure or a TRUNCATION; never retries a bad answer.

    A read timeout is the network, not a verdict, and letting one kill a two-hour run is how the
    first attempt at this ended at pull request 11 of 50. But the retry is deliberately narrow:
    an unparseable reply is a real result and is raised so the caller counts it, because a judge
    that quietly retries until it likes the answer is not a judge.
    """
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": JUDGE_PROMPT.format(golden_comment=golden, candidate=candidate)}
                ],
            }
        ],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": JUDGE_TOKENS},
    }
    budget = JUDGE_TOKENS
    last: Exception | None = None
    for attempt in range(TRANSPORT_RETRIES):
        try:
            resp = client.generate(body)  # type: ignore[attr-defined]
        except (TimeoutError, OSError, urllib.error.URLError) as exc:
            last = exc
            time.sleep(2**attempt)
            continue
        except VertexError as exc:
            # **A 429 OR A 5xx IS TRANSPORT, NOT A VERDICT, AND IT WAS NOT BEING RETRIED.**
            # `client.generate` raises `VertexError(RuntimeError)` for both, which fell past this
            # loop into the caller's `except RuntimeError` and was counted as an unjudged pair —
            # and an unjudged pair scores IDENTICALLY to a non-match, so the arm that issues more
            # judge calls loses true positives for a reason that has nothing to do with its
            # findings. A 4xx that is not 429 is a real refusal and still raises on the first try.
            if " 429" not in str(exc) and " 5" not in str(exc)[:12]:
                raise
            last = exc
            time.sleep(2**attempt)
            continue
        text = str(resp.get("text") or "")
        finish = str(resp.get("finish") or "")
        if finish == "MAX_TOKENS":
            # **A TRUNCATED VERDICT IS AN INCOMPLETE ANSWER, NOT A BAD ONE, AND THIS LOOP COULD NOT
            # TELL THEM APART.** The finish reason was never read on a non-empty reply, so a JSON
            # object cut off mid-`"reasoning"` reached `_parse` and raised "Unterminated string" —
            # indistinguishable from a judge that answered badly. Measured on `gemini-2.5-flash`:
            # 8 of 8 unjudged pairs were this, none were throttling. Flash writes longer reasoning
            # than Pro and overran the 2048-token cap, so the noisier-looking judge was really the
            # more verbose one, and every truncated pair scored as a NON-MATCH.
            budget *= 2
            body["generationConfig"] = {"temperature": 0.0, "maxOutputTokens": budget}
            last = JudgeFailed(f"truncated at {budget // 2} tokens")
            continue
        if not text.strip():
            raise JudgeFailed(f"empty judge reply, finish={finish}")
        return _parse(text)
    raise JudgeFailed(f"transport failed {TRANSPORT_RETRIES}x: {last}")


def verdicts(
    client: object, golden: list[str], candidates: list[str]
) -> dict[str, list[str] | int]:
    """TP / FP / FN for one pull request, aggregated as Martian's step 3 aggregates them."""
    if not candidates:
        return {"tp": [], "fp": [], "fn": list(golden), "errors": 0, "undecided": []}

    best: dict[str, tuple[float, str | None]] = dict.fromkeys(golden, (0.0, None))
    matched_cand: set[str] = set()
    errors = 0

    pairs = [(g, c) for g in golden for c in candidates]
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = {pool.submit(_one, client, g, c): (g, c) for g, c in pairs}
        for fut in concurrent.futures.as_completed(futs):
            g, c = futs[fut]
            try:
                match, conf = fut.result()
            except (JudgeFailed, KeyError, IndexError, RuntimeError, OSError):
                # Counted, never absorbed: an unjudged pair is not a non-match, and the count is
                # printed per arm so a silently degraded run cannot read as a clean one.
                errors += 1
                continue
            if match:
                matched_cand.add(c)
                if conf > best[g][0]:
                    best[g] = (conf, c)

    tp = [g for g, (_, c) in best.items() if c is not None]
    fn = [g for g, (_, c) in best.items() if c is None]
    fp = [c for c in candidates if c not in matched_cand]
    # **AN UNJUDGED PAIR IS EXCLUDED FROM THE DENOMINATOR, NOT COUNTED AS A NON-MATCH.** Leaving it
    # in `fn`/`fp` is what made the noisier judge look like the worse reviewer: the pair was never
    # decided, so scoring it against either arm is inventing a verdict nobody reached. `undecided`
    # names the goldens whose match status is unknown, and they are kept OUT of `fn`.
    undecided = (
        sorted(g for g in golden if g not in tp and best.get(g, (0.0, None))[1] is None and errors)
        if errors
        else []
    )
    fn = [g for g in fn if g not in undecided]
    if errors:
        # **THE DOCSTRING SAID THIS WAS PRINTED AND NOTHING PRINTED IT.** `run_d6b.py` took `tp`
        # and `fp` and dropped `errors`, so a run degraded by throttling read as a clean one —
        # the exact failure this module's comment claims cannot happen. Printed HERE rather than
        # left to a caller, because sixteen call sites each had to remember and one did not.
        print(
            f"    [judge] {errors} of {len(pairs)} pair(s) went unjudged; "
            f"{len(undecided)} golden comment(s) held UNDECIDED rather than counted against",
            flush=True,
        )
    return {"tp": tp, "fp": fp, "fn": fn, "errors": errors, "undecided": undecided}


def score(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    """Precision, recall, F1 -- precision over total candidates, as their dashboard defines it."""
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f
