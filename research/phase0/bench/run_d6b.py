"""D6b: does the human context behind a change raise the golden defects our reviewer finds?

WHAT: Runs two arms over the exposed golden changes — identical prompts except one appended block
      carrying the pull request's stated goal and the titles of the tickets it names — scores both
      with `judge.verdicts`, and reports McNemar exact plus the per-repository sign.
WHY:  **PRE-REGISTERED BEFORE THIS FILE EXISTED**, bars and population and power all fixed:
      → `docs/plans/preregistrations/reviewer/d6b-human-context-preregistration.md`.
      The power calculation there says n = 33 detects only a +32% net effect at 80% power, so a
      NULL here is uninformative and is reported as such rather than as evidence of no effect.

      **ONE CODE PATH, TWO TEMPLATES.** `bench_reviewer.review()` takes `template` for exactly this
      reason — its own comment says a second copy of the request-building and parsing is where a
      divergence between an arm and its control would hide, invisible in the prompt diff a reader
      would check. Nothing else varies: same client, same temperature, same diff, same cap.

      **THE EXPOSED POPULATION IS COMPUTED BY THE PRODUCT'S OWN READER**, `tickets.behind`, not by
      a reimplementation — the failure this repository records as "two code paths, one column".
      Changes with under 120 characters of context are excluded because the two arms are IDENTICAL
      on them by construction, and scoring them would dilute a real effect by a third.
IMPORTS: bench_reviewer, judge, martian_corpus, client (research); quantamind.ingest.context.
CONSUMED BY: `docs/plans/preregistrations/reviewer/d6b-human-context-preregistration.md`.
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys
from math import comb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "vertex"))

import bench_reviewer as reviewer
import judge
import martian_corpus as corpus
from client import Client

MODEL = "gemini-2.5-pro"
MIN_CONTEXT_CHARS = 120
"""Copied from `scripts/measure/context/exposure.py`, fixed before any outcome was seen."""

OUT = pathlib.Path(__file__).resolve().parent / "results" / "d6b_human_context.json"

# The control is `bench_reviewer.PROMPT` verbatim. The arm appends one block and changes nothing
# else -- not the instructions, not the cap, not the ordering.
CONTEXT_BLOCK = """
The author of this change stated the following about why it exists. Use it to judge whether the
change does what it set out to do; do not report the context itself as a defect.

{context}
"""


def _context_for(repo: str, number: int) -> str:
    """The stated goal and ticket titles, via the product's own reader."""
    from quantamind.ingest.context.tickets import behind

    got = behind(repo, number)
    stated = " ".join(got.stated.text().split())
    titles = " ".join(" ".join(t.title.split()) for t in got.tickets)
    text = (stated + (" " if stated and titles else "") + titles).strip()
    # **BRACES IN REAL PROSE COLLIDE WITH `str.format`.** `bench_reviewer.review` formats the
    # template, so a pull request body containing `{ init }` raised KeyError -- and a body
    # containing `{title}` would have been SILENTLY SUBSTITUTED, corrupting the arm without
    # raising at all. Escaping here is what makes the arm's text the author's text.
    return text.replace("{", "{{").replace("}", "}}")


def _mcnemar(better: int, worse: int) -> float:
    total = better + worse
    if total == 0:
        return 1.0
    smaller = min(better, worse)
    return float(min(1.0, 2 * sum(comb(total, i) for i in range(smaller + 1)) / 2**total))


def main() -> int:
    prs = corpus.pulls()
    client = Client(MODEL)

    exposed: list = []
    thin: list[str] = []
    not_a_pull: list[str] = []
    for pr in prs:
        url = str(pr["original"])
        parts = url.rstrip("/").split("/")
        # **NOT EVERY GOLDEN ENTRY IS A PULL REQUEST.** Some `original` links point at a commit,
        # which has no description and no linked ticket, so there is no context to give either arm.
        # Recorded as its own count rather than folded into "too thin": one is a change whose
        # author said little, the other is a change we cannot ask about at all.
        if len(parts) < 5 or "pull" not in parts or not parts[-1].isdigit():
            not_a_pull.append(url)
            continue
        repo, number = f"{parts[3]}/{parts[4]}", int(parts[-1])
        context = _context_for(repo, number)
        if len(context) >= MIN_CONTEXT_CHARS:
            exposed.append((pr, repo, number, context))
        else:
            thin.append(f"{repo}#{number}")

    print(
        f"  {len(exposed)} of {len(prs)} changes exposed (context >= {MIN_CONTEXT_CHARS} chars)\n"
    )

    detail = []
    for index, (pr, repo, number, context) in enumerate(exposed, 1):
        title = str(pr["title"])
        golden = list(pr["golden"])
        try:
            diff = corpus.diff(str(pr["original"]))
        except Exception as exc:
            print(f"  {index:2d}/{len(exposed)} {repo} #{number}: diff unreadable ({exc})")
            detail.append(
                {
                    "repo": repo,
                    "repo_file": str(pr["repo_file"]),
                    "number": number,
                    "skipped": "diff",
                }
            )
            continue

        control, _ = reviewer.review(client, title, diff)
        armed, _ = reviewer.review(
            client, title, diff, template=reviewer.PROMPT + CONTEXT_BLOCK.format(context=context)
        )
        v_control = judge.verdicts(client, golden, control)
        v_armed = judge.verdicts(client, golden, armed)
        tp_c, tp_a = len(v_control["tp"]), len(v_armed["tp"])
        detail.append(
            {
                "repo": repo,
                "repo_file": str(pr["repo_file"]),
                "number": number,
                "golden": len(golden),
                "tp_control": tp_c,
                "tp_context": tp_a,
                "fp_control": len(v_control["fp"]),
                "fp_context": len(v_armed["fp"]),
            }
        )
        print(
            f"  {index:2d}/{len(exposed)} {repo.split('/')[-1][:12]:12s} #{number:<7} "
            f"golden={len(golden):2d}  control={tp_c:2d}  context={tp_a:2d}  "
            f"{'+' if tp_a > tp_c else ('-' if tp_a < tp_c else '=')}"
        )

    scored = [d for d in detail if "skipped" not in d]
    better = sum(1 for d in scored if d["tp_context"] > d["tp_control"])
    worse = sum(1 for d in scored if d["tp_context"] < d["tp_control"])
    same = len(scored) - better - worse
    p = _mcnemar(better, worse)

    by_repo: dict[str, int] = collections.defaultdict(int)
    for d in scored:
        by_repo[d["repo_file"]] += d["tp_context"] - d["tp_control"]
    positive = sum(1 for v in by_repo.values() if v > 0)

    total_c = sum(d["tp_control"] for d in scored)
    total_a = sum(d["tp_context"] for d in scored)

    print(f"\n  scored {len(scored)} changes")
    print(f"  golden defects found: control {total_c}, context {total_a} ({total_a - total_c:+d})")
    print(f"  per change: context better on {better}, worse on {worse}, equal on {same}")
    print(f"  McNemar exact p = {p:.4f}")
    print(f"  repositories positive: {positive} of {len(by_repo)}  {dict(by_repo)}")

    confirmed = total_a > total_c and p < 0.05 and positive >= 4
    print(f"\n  [{'CONFIRMED' if confirmed else 'NULL'}] against the pre-registered bars")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "exposed": len(exposed),
                "too_thin": len(thin),
                "not_a_pull": len(not_a_pull),
                "scored": len(scored),
                "tp_control": total_c,
                "tp_context": total_a,
                "better": better,
                "worse": worse,
                "same": same,
                "mcnemar_p": p,
                "by_repo": dict(by_repo),
                "repositories_positive": positive,
                "confirmed": confirmed,
                "detail": detail,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
