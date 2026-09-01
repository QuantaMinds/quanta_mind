"""D6b: does the human context behind a change raise the golden defects our reviewer finds?

WHAT: Runs two arms over the exposed golden changes — identical prompts except one appended block
      carrying the pull request's stated goal and the titles of the tickets it names — scores both
      with `judge.verdicts`, and reports McNemar exact plus the per-repository sign.
WHY:  **PRE-REGISTERED BEFORE THIS FILE EXISTED**, bars and population and power all fixed:
      → `docs/plans/preregistrations/reviewer/d6b-human-context-preregistration.md`.
      The power calculation there says n = 33 detects only a +32% net effect at 80% power, so a
      NULL here is uninformative and is reported as such rather than as evidence of no effect.

      **ONE CODE PATH, TWO TEMPLATES.** `bench_reviewer.review()` takes `template` for exactly this
      reason — a second copy of the request-building is where a divergence between an arm and its
      control would hide. Same client, same temperature, same diff, same cap.

      **THE ARM VARIES TWO THINGS AND THIS DOCSTRING ONCE CLAIMED OTHERWISE** ("nothing else varies
      — not the instructions"). `DIRECTIVE` IS an instruction, and it is appended AFTER the control
      prompt's terminal "Respond with ONLY a JSON array" line, demoting the format instruction from
      last position. A difference between arms can be the information, the directive, or the
      position; the first run reported the information as if it were the only candidate.
      `--placebo` holds the directive and position fixed and swaps in another change's context.

      **THE JUDGE IS THE SAME FAMILY AS THE REVIEWER**, while the Method promises a DIFFERENT one.
      **UNMET, NOT UNMEETABLE** — the earlier wording was wrong, and `judge_family.py` has the
      measurement and the reason.

      **RUN `run_d6b_noise.py` FIRST.** Identical arms moved +2 TP with 14 of 36 discordant; the
      first treatment run moved -3 with 18 of 36 and was withdrawn as shot noise.

      **THE EXPOSED POPULATION IS COMPUTED BY THE PRODUCT'S OWN READER**, `tickets.behind`, not by
      a reimplementation — the failure this repository records as "two code paths, one column".
      Changes with under 120 characters of context are excluded because the two arms are IDENTICAL
      on them by construction, and scoring them would dilute a real effect by a third.
IMPORTS: bench_reviewer, judge, martian_corpus, client (research); quantamind.ingest.context.
CONSUMED BY: `docs/plans/preregistrations/reviewer/d6b-human-context-preregistration.md`.
"""

from __future__ import annotations

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
DIRECTIVE = """
The author of this change stated the following about why it exists. Use it to judge whether the
change does what it set out to do; do not report the context itself as a defect.
"""
"""**AN INSTRUCTION, HELD APART FROM THE INFORMATION ON PURPOSE.** The first run treated
directive-plus-information as one variable and then explained its result by the information. A
model told to judge goal achievement and then doing so is compliance, not evidence."""

CONTEXT_BLOCK = (
    DIRECTIVE
    + """
{context}
"""
)

PREREGISTERED_BAR, PREREGISTERED_REPOSITORIES = 4, 6
REPOSITORY_SHARE = PREREGISTERED_BAR / PREREGISTERED_REPOSITORIES
"""The bar as WRITTEN: 4 of 6, two thirds. Hard-coding `>= 4` made it 4 of 4 on a four-repository
corpus, which no result could clear — so NULL was a property of the harness, not a fact."""


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
    placebo = "--placebo" in sys.argv
    if placebo:
        print("  PLACEBO ARM: same directive, context taken from a DIFFERENT change\n")
    prs = corpus.pulls()
    client = Client(MODEL)

    exposed: list = []
    unreadable: list[str] = []
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

        # **THE FINISH REASON IS KEPT.** Dropping it meant a truncation and a short review printed
        # the same number, and the arm's prompt is longer so a truncation lands asymmetrically.
        shown = exposed[index % len(exposed)][3] if placebo else context
        control, finish_control = reviewer.review(client, title, diff)
        armed, finish_context = reviewer.review(
            client, title, diff, template=reviewer.PROMPT + CONTEXT_BLOCK.format(context=shown)
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
                # **RECORDED BECAUSE THEIR ABSENCE MADE THE FIRST RUN UNAUDITABLE.** TP+FP is not
                # a candidate count and can exceed the cap; an unjudged pair scores as a
                # non-match; a truncation is not a short review.
                "candidates_control": len(control),
                "candidates_context": len(armed),
                "judge_errors_control": int(v_control["errors"]),
                "judge_errors_context": int(v_armed["errors"]),
                "finish_control": finish_control,
                "finish_context": finish_context,
            }
        )
        print(
            f"  {index:2d}/{len(exposed)} {repo.split('/')[-1][:12]:12s} #{number:<7} "
            f"golden={len(golden):2d}  control={tp_c:2d}  context={tp_a:2d}  "
            f"{'+' if tp_a > tp_c else ('-' if tp_a < tp_c else '=')}"
        )

    from d6b_report import report

    return report(detail, placebo, exposed, thin, unreadable, not_a_pull)


if __name__ == "__main__":
    raise SystemExit(main())
