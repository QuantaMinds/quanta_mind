"""Design fourteen: the quote-anchor review with CI and config excluded BEFORE the call.

WHAT: Reviews `corpus.REPOS_D14` once per pull request, one arm, and writes every published finding
      to results/quote14_run.json with the counts needed to compute W/n and C/n after adjudication.
WHY:  Bars, corpus and the prior are fixed in
      docs/plans/preregistrations/reviewer/design14-model-lever-preregistration.md before this ran.

      **THIS IS ARM 1, THE CONFIG EXCLUSION, AND IT IS NOT THE MODEL LEVER.** Amendment 1 of that
      document records that no frontier model is reachable from this project -- `gemini-3-pro*` and
      the Anthropic publisher models all answer 404 across three regions, and no API key is set --
      so `MODEL` is the same one design thirteen ran. Any report of this run that describes it as
      testing a stronger model is describing something that did not happen.

      **WHAT IT DOES BUY: the 42.0% source-code-only figure was computed POST HOC**, by filtering
      design thirteen's pool after its verdicts existed. Choosing a subset after seeing a result is
      the same defect as moving a threshold after seeing one, so that number is a hypothesis.
      Applying the filter BEFORE the call, on a corpus the method has never seen, is what makes it
      a measurement.

      **ONE ARM.** Design thirteen ran three -- plain, hunk expansion, conventions file -- and the
      headline moved for neither addition. Carrying them here would triple the cost to re-measure
      two things already answered.

      **A GATE FAILURE IS RECORDED, NEVER DROPPED.** A run that filtered everything and a run whose
      model found nothing must not produce the same file.
IMPORTS: stdlib (collections, concurrent.futures, json, pathlib, sys). Local: `corpus`, `gate`,
      `paths`, `reviewer`, and the Vertex `client`.
CONSUMED BY: nobody -- it prints and writes results/quote14_run.json.
"""

from __future__ import annotations

import collections
import concurrent.futures
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "vertex"))

import gate
import paths
import reviewer
from client import Client

import corpus

# Arm 1. Amendment 1 records why this is not a frontier model; changing it is arm 2 and nothing
# else in this file moves with it.
MODEL = "gemini-2.5-pro"
OUT = pathlib.Path(__file__).resolve().parent.parent / "results" / "quote14_run.json"
WORKERS = 4


def prepare(pr: dict) -> dict:
    """One pull request's reviewable diff, or a record saying why there is none."""
    repo, num = str(pr["repo"]), int(str(pr["number"]))
    try:
        full = corpus.diff(repo, num)
    except corpus.FetchFailed as exc:
        return {"repo": repo, "pr": num, "error": f"fetch: {str(exc)[:70]}"}
    text, removed, kept = paths.filter_diff(full, strict=True)
    if kept == 0 or not text.strip():
        # NOT an error and NOT silence: every file was config or generated. Counted separately,
        # because a corpus that is mostly CI churn would otherwise read as a model finding nothing.
        return {"repo": repo, "pr": num, "error": "nothing reviewable", "removed": removed}
    return {
        "repo": repo,
        "pr": num,
        "title": str(pr["title"]),
        "url": str(pr.get("url") or ""),
        "diff": text,
        "removed": removed,
        "files": kept,
    }


def review_one(client: Client, job: dict) -> dict:
    """One review, gated. Returns the job with its findings, failures and finish reason attached."""
    out: dict[str, object] = dict(job)
    out.pop("diff", None)
    try:
        findings, finish = reviewer.review(client, job["title"], job["diff"], rules="")
    except reviewer.ReviewFailed as exc:
        out["failed"] = str(exc)[:90]
        return out
    added, sizes = gate.added_lines(job["diff"])
    published, rejected = [], collections.Counter()
    for f in findings:
        v = gate.check(f, job["diff"], added, sizes)
        if v["ok"]:
            published.append(v | {"repo": job["repo"], "pr": job["pr"], "url": job["url"]})
        else:
            for why in v.get("failed", ["unnamed"]):
                rejected[why] += 1
    out["raw"] = len(findings)
    out["published"] = published
    out["rejected"] = dict(rejected)
    out["finish"] = finish
    return out


def main() -> int:
    prs = corpus.pulls(corpus.REPOS_D14, corpus.PER_REPO_D14)
    print(f"design 14 arm 1 — {MODEL}")
    print(f"  {len(prs)} pull requests, {len(corpus.REPOS_D14)} repositories never touched")
    print("  CI and config excluded BEFORE the call. This is not the model lever.\n")

    jobs = [prepare(p) for p in prs]
    usable = [j for j in jobs if "diff" in j]
    skipped = [j for j in jobs if "diff" not in j]
    print(f"  {len(usable)} reviewable, {len(skipped)} skipped")
    dropped: collections.Counter[str] = collections.Counter()
    for j in jobs:
        for why, count in (j.get("removed") or {}).items():
            dropped[why] += count
    print(f"  files removed before the call: {dict(dropped)}\n")

    client = Client(MODEL)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(review_one, client, j): j for j in usable}
        for done in concurrent.futures.as_completed(futures):
            job = futures[done]
            try:
                results.append(done.result())
            except Exception as exc:  # recorded, never swallowed: a lost review is not a silence
                results.append(
                    {
                        **{k: v for k, v in job.items() if k != "diff"},
                        "failed": f"{type(exc).__name__}: {str(exc)[:80]}",
                    }
                )
            print(f"    {len(results)}/{len(usable)}", end="\r", flush=True)

    published = sum(len(r.get("published") or []) for r in results)
    raw = sum(int(r.get("raw") or 0) for r in results)
    silent = sum(1 for r in results if not r.get("published") and "failed" not in r)
    failed = [r for r in results if "failed" in r]
    finishes = collections.Counter(str(r.get("finish")) for r in results if "finish" in r)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "model": MODEL,
                "arm": "1 — config exclusion, NOT the model lever",
                "prs": len(prs),
                "reviewable": len(usable),
                "skipped": len(skipped),
                "removed_before_call": dict(dropped),
                "results": results,
            },
            indent=1,
        )
    )

    print(f"\n\n  raw findings          {raw}")
    print(f"  published after gate  {published}")
    why_rejected: collections.Counter[str] = collections.Counter()
    for r in results:
        for why, count in (r.get("rejected") or {}).items():
            why_rejected[why] += count
    print(f"  gate rejection reasons {dict(why_rejected)}")
    print(f"  pull requests with no published finding  {silent}")
    print(f"  finish reasons        {dict(finishes)}")
    print(f"  failed calls          {len(failed)}")
    print(f"\n  -> {OUT}")
    print(
        "  NOT A RESULT UNTIL ADJUDICATED. W/n and C/n need blind grading; see the "
        "pre-registration."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
