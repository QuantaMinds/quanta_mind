"""The noise floor D6b never measured: the SAME arm, run twice, scored the same way.

WHAT: runs the control prompt twice on every exposed change and reports the discordance and TP
      swing between two identical arms.
WHY:  **D6b HAS NO NOISE FLOOR AND ITS ENTIRE RESULT RESTS ON ONE DRAW PER ARM.** 18 of 36 changes
      changed their true-positive count between two prompts sharing ~95% of their tokens. Nothing
      in that run distinguishes an unstable pipeline from a treatment effect, because the run that
      would distinguish them — this one — was not performed.

      **THIS IS THE PROJECT'S OWN RECORDED FAILURE.** Shape-context cleared `> +2.1 points` twice
      and was retracted with "the effect was smaller than the noise floor". If control-vs-control
      also yields ~18/36 discordance and a +/-3 swing, then D6b's -3, its 7:11 split and its whole
      mechanism story are this pipeline's shot noise.

      Temperature is 0.0 and that is NOT determinism: the model is stochastic at this granularity
      and the judge adds a second independent source of variance on top.
IMPORTS: bench_reviewer, judge, martian_corpus, client (research); run_d6b for the population.
CONSUMED BY: `docs/findings/reviewer/D6B_HUMAN_CONTEXT_NULL_2026-08.md`.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "vertex"))

import bench_reviewer as reviewer
import judge
import martian_corpus as corpus
from client import Client
from run_d6b import MIN_CONTEXT_CHARS, MODEL, _context_for, _mcnemar

OUT = pathlib.Path(__file__).resolve().parent / "results" / "d6b_noise_floor.json"


def main() -> int:
    client = Client(MODEL)
    exposed = []
    for pr in corpus.pulls():
        parts = str(pr["original"]).rstrip("/").split("/")
        if len(parts) < 5 or "pull" not in parts or not parts[-1].isdigit():
            continue
        repo, number = f"{parts[3]}/{parts[4]}", int(parts[-1])
        if len(_context_for(repo, number)) >= MIN_CONTEXT_CHARS:
            exposed.append((pr, repo, number))

    print(f"  {len(exposed)} exposed changes; running the CONTROL prompt twice on each\n")
    detail = []
    for index, (pr, repo, number) in enumerate(exposed, 1):
        golden = list(pr["golden"])
        try:
            diff = corpus.diff(str(pr["original"]))
        except Exception as exc:
            print(f"  {index:2d} {repo} #{number}: diff unreadable ({exc})")
            continue
        first, fin_a = reviewer.review(client, str(pr["title"]), diff)
        second, fin_b = reviewer.review(client, str(pr["title"]), diff)
        v1 = judge.verdicts(client, golden, first)
        v2 = judge.verdicts(client, golden, second)
        row = {
            "repo_file": str(pr["repo_file"]),
            "number": number,
            "golden": len(golden),
            "tp_a": len(v1["tp"]),
            "tp_b": len(v2["tp"]),
            "fp_a": len(v1["fp"]),
            "fp_b": len(v2["fp"]),
            # **RECORDED THIS TIME.** D6b discarded all four and could not tell a degraded run
            # from a clean one.
            "candidates_a": len(first),
            "candidates_b": len(second),
            "judge_errors_a": int(v1["errors"]),
            "judge_errors_b": int(v2["errors"]),
            "finish_a": fin_a,
            "finish_b": fin_b,
        }
        detail.append(row)
        mark = "+" if row["tp_b"] > row["tp_a"] else ("-" if row["tp_b"] < row["tp_a"] else "=")
        print(
            f"  {index:2d}/{len(exposed)} {repo.split('/')[-1][:12]:12s} #{number:<7} "
            f"gold={len(golden):2d} run1={row['tp_a']:2d} run2={row['tp_b']:2d} {mark}  "
            f"cand={row['candidates_a']:2d}/{row['candidates_b']:2d} "
            f"err={row['judge_errors_a']}/{row['judge_errors_b']}"
        )

    better = sum(1 for d in detail if d["tp_b"] > d["tp_a"])
    worse = sum(1 for d in detail if d["tp_b"] < d["tp_a"])
    same = len(detail) - better - worse
    tp_a = sum(d["tp_a"] for d in detail)
    tp_b = sum(d["tp_b"] for d in detail)
    errors = sum(d["judge_errors_a"] + d["judge_errors_b"] for d in detail)
    truncated = sum(1 for d in detail if d["finish_a"] != "STOP" or d["finish_b"] != "STOP")

    print(f"\n  IDENTICAL ARMS: run1 TP={tp_a}, run2 TP={tp_b} ({tp_b - tp_a:+d})")
    print(
        f"  discordant: {better} up, {worse} down, {same} equal"
        f"  -> p = {_mcnemar(better, worse):.4f}"
    )
    print(f"  judge errors: {errors}    non-STOP finishes: {truncated}")
    print("\n  D6b measured -3 TP and 7:11 discordance between DIFFERENT arms.")
    print(f"  Two IDENTICAL arms differ by {tp_b - tp_a:+d} TP and {better + worse}/{len(detail)}.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "scored": len(detail),
                "tp_a": tp_a,
                "tp_b": tp_b,
                "better": better,
                "worse": worse,
                "same": same,
                "judge_errors": errors,
                "non_stop_finishes": truncated,
                "detail": detail,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
