"""Four reviewer prompts over the same 50 pull requests, judged together in one run.

WHAT: Generates fresh reviews under CONTROL, ABSTAIN, AIM and BOTH, judges every candidate against
      the same goldens, and prints precision, true positives per pull request, and false positives
      per true positive for each arm.
WHY:  **THE QUESTION IS NOT WHAT THE REVIEWER IS TOLD TO LOOK AT -- FOUR ARMS HAVE ALREADY TESTED
      THAT AND MOVED NOTHING.** It is how many things it is told it may say. The per-candidate
      labels show true positives per pull request at parity with Qodo (1.9 against 2.1) and the
      whole gap sitting in what we emit alongside them; and Qodo running 83.3% precision on the
      pull requests where it emits three or fewer against 51.4% where it emits six or more, while
      we read 46.1% and 52.2% -- flat. That is a reviewer that does not modulate.

      **ALL FOUR ARMS GENERATE FRESH, INCLUDING THE CONTROL.** Reusing the stored candidates for
      the control would compare one arm's draw against another's frozen one, through a different
      code path, and credit the difference to the prompt. Generation runs at temperature 0.0, so
      this pins the draw rather than sampling it -- **the spread this does NOT measure is the
      generator's, and only the judge's is quantified**, by `judge_variance.py`.

      **THE BAR IS A MULTIPLE OF THE MEASURED JUDGE SPREAD, NOT ZERO**, because re-judging
      IDENTICAL candidates moved CodeRabbit by ten precision points. → `judge_variance.py` and
      `docs/plans/preregistrations/reviewer/prompt-direction-preregistration.md`
IMPORTS: stdlib; local `martian_corpus`, `bench_reviewer`, `judge`, and the Vertex `client`.
CONSUMED BY: read by a human; writes `results/prompt_arms.json`.
"""

from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "vertex"))
sys.path.insert(0, str(HERE.parent))

import bench_reviewer as br  # noqa: E402
import judge  # noqa: E402
import martian_corpus as mc  # noqa: E402
from client import Client  # noqa: E402

OUT = HERE.parent / "results" / "prompt_arms.json"

# The control's own words, so a difference cannot come from an incidental rewrite.
_ABSTAIN = """
Most pull requests deserve NO comment or ONE. Emitting nothing is the correct answer for a change
that is fine, and it is the answer you should give most often. Before you report an issue, ask
whether you would defend it to the author in review with the diff in front of you. If you would
hedge, do not report it. Report your single strongest finding rather than your three best.
"""

_AIM = """
Concentrate on FUNCTIONAL defects: code that will produce a wrong result, crash, or fail to do
what its caller expects, for some input that will actually occur. That is what maintainers fix.
Security posture, missing validation on internal callers, and hardening suggestions are worth far
less than one concrete wrong answer, and you should report them only when you can name the input
that breaks.
"""

ARMS = {
    "A0_CONTROL": "",
    "A1_ABSTAIN": _ABSTAIN,
    "A2_AIM": _AIM,
    "A3_BOTH": _ABSTAIN + _AIM,
}


def prompt_for(extra: str) -> str:
    """The shipped prompt with one paragraph inserted before the report-at-most line."""
    if not extra:
        return br.PROMPT
    marker = "Report at most {max_issues} issues."
    if marker not in br.PROMPT:
        raise RuntimeError(
            "the control prompt no longer contains the insertion point this arm builds on; "
            "the arms would silently differ from the control by more than the paragraph"
        )
    return br.PROMPT.replace(marker, extra.strip() + "\n\n" + marker)


def main() -> int:
    mc._assert_intact()
    client = Client("gemini-2.5-pro")
    pulls = [p for p in mc.pulls() if p.get("golden")]
    print(f"  {len(pulls)} pull requests with goldens, {len(ARMS)} arms\n", flush=True)

    out: dict[str, object] = {}
    for name, extra in ARMS.items():
        tmpl = prompt_for(extra)
        cands: dict[str, list[str]] = {}
        errors = 0
        for p in pulls:
            try:
                d = mc.diff(str(p["original"]))
                issues, _finish = br.review(client, str(p["title"]), d, template=tmpl)
            except (mc.FetchFailed, br.ReviewFailed, KeyError, IndexError):
                errors += 1
                continue
            cands[str(p["key"])] = issues
        tp = n = 0
        for key, texts in cands.items():
            g = next((x["golden"] for x in pulls if str(x["key"]) == key), [])
            if not texts or not g:
                continue
            v = judge.verdicts(client, list(g), texts)
            tp += len(texts) - len(set(v["fp"]))
            n += len(texts)
        prs = len(cands)
        out[name] = {
            "tp": tp,
            "n": n,
            "prs": prs,
            "errors": errors,
            "precision": tp / max(1, n),
            "tp_per_pr": tp / max(1, prs),
            "fp_per_tp": (n - tp) / max(1, tp),
            "candidates": cands,
        }
        print(
            f"  {name:<12} {tp:>3}/{n:<4} = {tp / max(1, n):>6.1%}   "
            f"TP/PR {tp / max(1, prs):.2f}   FP/TP {(n - tp) / max(1, tp):.2f}   "
            f"{errors} generation errors",
            flush=True,
        )

    OUT.write_text(json.dumps(out, indent=1))
    base = out["A0_CONTROL"]
    print(f"\n  vs control (TP/PR {base['tp_per_pr']:.2f}, FP/TP {base['fp_per_tp']:.2f}):")
    for name, v in out.items():
        if name == "A0_CONTROL":
            continue
        print(
            f"    {name:<12} dTP/PR {v['tp_per_pr'] - base['tp_per_pr']:+.2f}   "
            f"dFP/TP {v['fp_per_tp'] - base['fp_per_tp']:+.2f}"
        )
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
