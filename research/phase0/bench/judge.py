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
import time
import urllib.error

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
    """One pair. Retries a TRANSPORT failure; never retries a bad answer.

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
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 2048},
    }
    last: Exception | None = None
    for attempt in range(TRANSPORT_RETRIES):
        try:
            resp = client.generate(body)  # type: ignore[attr-defined]
        except (TimeoutError, OSError, urllib.error.URLError) as exc:
            last = exc
            time.sleep(2**attempt)
            continue
        text = str(resp.get("text") or "")
        if not text.strip():
            raise JudgeFailed(f"empty judge reply, finish={resp.get('finish')}")
        return _parse(text)
    raise JudgeFailed(f"transport failed {TRANSPORT_RETRIES}x: {last}")


def verdicts(
    client: object, golden: list[str], candidates: list[str]
) -> dict[str, list[str] | int]:
    """TP / FP / FN for one pull request, aggregated as Martian's step 3 aggregates them."""
    if not candidates:
        return {"tp": [], "fp": [], "fn": list(golden), "errors": 0}

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
    return {"tp": tp, "fp": fp, "fn": fn, "errors": errors}


def score(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    """Precision, recall, F1 -- precision over total candidates, as their dashboard defines it."""
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f
