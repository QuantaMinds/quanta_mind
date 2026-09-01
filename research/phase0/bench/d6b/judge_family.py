"""Is a verdict a property of the finding, or of the model doing the judging?

WHAT: scores the SAME checked-in CodeRabbit candidates with two Gemini judges (2.5-pro and
      2.5-flash) and compares both against the different-family reference already in the corpus —
      CodeRabbit's own Claude-judged tp/fp/fn.
WHY:  **I CLAIMED "NO OTHER CAPABLE MODEL IS REACHABLE FROM THIS PROJECT" WITHOUT TESTING IT.**
      Two things came back when it was finally tested: Anthropic models on Vertex return "not found
      or your project does not have access", which is a provisioning state and not an absolute; and
      `gemini-2.5-flash` answers fine, roughly 2.5x faster. Neither makes a DIFFERENT-family judge
      available, so the pre-registration's Method requirement is still unmet — but "unmeetable"
      was the wrong word and this file is what should have been run before using it.

      **THE COMPARISON THAT IS AVAILABLE IS THE ONE ALREADY CHECKED IN.** `martian_corpus.published`
      holds CodeRabbit's candidates as scored by THEIR Claude judge: tp=103, fp=194, fn=70. Scoring
      the identical candidates with our Gemini judges measures how much of a verdict is the finding
      and how much is the judge — which is the confounder both audits raised about D6b, and it is
      answerable without a different-family judge of our own.

      **A SECOND GEMINI IS NOT A SECOND FAMILY, AND THIS FILE DOES NOT PRETEND OTHERWISE.** Pro and
      Flash share a trainer and a corpus; agreement between them bounds nothing about shared bias.
      What disagreement between them WOULD show is that the verdict is unstable across models even
      within one family — a floor on judge noise, not a check on judge correctness.
IMPORTS: judge, martian_corpus, client (research).
CONSUMED BY: `docs/findings/reviewer/D6B_HUMAN_CONTEXT_NULL_2026-08.md`.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "vertex"))

import judge
import martian_corpus as corpus
from client import Client

MODELS = ("gemini-2.5-pro", "gemini-2.5-flash")
TOOL = "coderabbit"
SAMPLE = 20
"""Pull requests judged per model. The full 50 is 1,413 pairs per model and hours per arm; 20 is
enough to see whether two judges disagree materially and is stated rather than presented as 50."""

OUT = pathlib.Path(__file__).resolve().parents[1] / "results" / "d6b_judge_family.json"


def main() -> int:
    prs = corpus.pulls()[:SAMPLE]
    candidates = corpus.rival_candidates(TOOL)
    their_tp, their_fp, _their_fn = corpus.published(TOOL)
    their_precision = their_tp / (their_tp + their_fp)
    print(
        f"  {TOOL} scored by THEIR Claude judge: precision {their_precision:.1%} "
        f"(tp={their_tp} fp={their_fp}) over all 50\n"
    )

    scored: dict[str, dict] = {}
    per_pr: dict[str, dict[str, list[str]]] = {}
    for model in MODELS:
        client = Client(model)
        tp = fp = errors = 0
        per_pr[model] = {}
        for index, pr in enumerate(prs, 1):
            cands = candidates.get(str(pr["key"]), [])
            if not cands:
                continue
            got = judge.verdicts(client, list(pr["golden"]), cands)
            tp += len(got["tp"])
            fp += len(got["fp"])
            errors += int(got["errors"])
            per_pr[model][str(pr["key"])] = [str(t) for t in got["tp"]]
            print(
                f"  {model:18} {index:2d}/{len(prs)} tp={len(got['tp']):2d} fp={len(got['fp']):2d}"
            )
        precision = tp / (tp + fp) if tp + fp else 0.0
        scored[model] = {"tp": tp, "fp": fp, "precision": precision, "errors": errors}
        print(f"  {model:18} TOTAL precision {precision:.1%} (tp={tp} fp={fp}) errors={errors}\n")

    # **THE NUMBER THAT MATTERS: do the two judges call the same goldens found?**
    a, b = MODELS
    agree = differ = 0
    for key in per_pr[a]:
        left, right = set(per_pr[a][key]), set(per_pr[b].get(key, []))
        agree += len(left & right)
        differ += len(left ^ right)
    print(
        f"  judges agree on {agree} golden verdicts and differ on {differ} "
        f"({differ / (agree + differ):.1%} disagreement)"
        if agree + differ
        else "  no overlap"
    )

    OUT.write_text(
        json.dumps(
            {
                "sample": len(prs),
                "their_precision": their_precision,
                "models": scored,
                "agree": agree,
                "differ": differ,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
