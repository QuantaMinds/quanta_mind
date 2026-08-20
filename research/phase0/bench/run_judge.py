"""Put the isolated judge on the widest arm we have, and re-score what survives.

WHAT: Takes the nits arm's 464 candidates from `results/nits_arm.json`, adjudicates every one
      against the diff it was made about, then re-judges ONLY the survivors against the same 173
      golden comments with the same benchmark judge. Prints precision, recall and F1 before and
      after, and how many false positives were discarded.
WHY:  **The bet is a number and this is the run that tests it.** Discarding ~85% of false
      positives while keeping the true findings takes precision to 64.7% and F1 to 61.0%, past
      Greptile's 54.5% and Qodo's published 60.1%. Anything less is a partial result and is
      reported as one.

      **THE SURVIVORS ARE RE-SCORED, NOT SUBSET FROM THE OLD LABELS.** The benchmark's true and
      false positives were never recorded per candidate -- only which goldens were caught -- so
      subsetting would be guesswork dressed as arithmetic. The kept set goes through
      `judge.py` exactly as a fresh arm would, which is also the order production runs in:
      review, judge, publish, and only what was published is scored.

      **THE PRE-JUDGE ARM IS PRINTED BESIDE IT EVERY TIME.** A filter that improves precision by
      discarding everything is not a result, so the recall it cost is never off-screen.
IMPORTS: stdlib (json, pathlib, sys). Local: `corpus`, `judge`, `isolated_judge`, Vertex `client`.
CONSUMED BY: nobody -- it prints and writes results/judged_arm.json.
"""

from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "vertex"))

import isolated_judge  # noqa: E402
import judge  # noqa: E402
from client import Client  # noqa: E402

import corpus  # noqa: E402

MODEL = "gemini-2.5-pro"
NITS = HERE / "results" / "nits_arm.json"
OUT = HERE / "results" / "judged_arm.json"


def score(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def main() -> int:
    blob = json.loads(NITS.read_text())
    cands: dict[str, list[str]] = blob["candidates"]
    golden = {pr["key"]: pr["golden"] for pr in blob["detail"]}
    total_before = sum(len(v) for v in cands.values())
    print(f"  {len(cands)} pull requests, {total_before} candidates before the judge\n")

    client = Client(MODEL)
    kept: dict[str, list[str]] = {}
    detail: list[dict[str, object]] = []
    failures = 0
    for n, (key, issues) in enumerate(cands.items(), 1):
        if not issues:
            kept[key] = []
            continue
        try:
            diff = corpus.diff(key)
        except Exception as exc:  # a diff we cannot fetch is not a judgement
            print(f"    {key}: diff unavailable ({str(exc)[:50]}) — arm left unjudged")
            kept[key] = issues
            continue
        verdicts = isolated_judge.screen(client, diff, issues)
        failures += sum(1 for v in verdicts if v.get("failed"))
        kept[key] = [str(v["issue"]) for v in verdicts if v["keep"]]
        detail.append({"key": key, "verdicts": verdicts})
        print(f"    {n}/{len(cands)}  kept {len(kept[key])}/{len(issues)}", end="\r", flush=True)

    total_after = sum(len(v) for v in kept.values())
    # **WRITTEN BEFORE SCORING.** The first attempt screened all 464 candidates and then died in
    # the scoring loop below, and because the file was written at the end, every judgement was
    # lost -- 464 model calls for nothing.
    OUT.write_text(
        json.dumps(
            {
                "model": MODEL,
                "same_family_as_reviewer": True,
                "before": total_before,
                "after": total_after,
                "judge_failures": failures,
                "kept": kept,
                "detail": detail,
            },
            indent=1,
        )
    )
    print(
        f"\n\n  {total_after} of {total_before} candidates survived "
        f"({1 - total_after / total_before:.0%} discarded), {failures} judge failures"
    )
    print(f"  screening written to {OUT}")

    # **A FAILED CALL IS NOT A VERDICT.** At an 8192-token ceiling, 136 of 464 calls finished
    # MAX_TOKENS, and recording those as DROPs reported a 47% discard rate that was mostly
    # breakage. A run this degraded describes the harness rather than the judge.
    rate = failures / total_before
    if rate > 0.05:
        print(
            f"\n  REFUSING TO SCORE: {failures}/{total_before} = {rate:.0%} of judge calls FAILED."
            f" Above the 5% floor the discard rate is breakage, not judgement."
        )
        return 1

    print("\n  re-scoring the survivors against the same 173 golden comments ...")
    tp = fp = fn = 0
    for key, issues in kept.items():
        g = golden.get(key) or []
        if not g:
            fp += len(issues)
            continue
        v = judge.verdicts(client, g, issues)
        tp += len(v["tp"])
        fp += len(v["fp"])
        fn += len(v["fn"])

    p, r, f = score(tp, fp, fn)
    OUT.write_text(
        json.dumps(
            {
                "model": MODEL,
                "same_family_as_reviewer": True,
                "before": {"candidates": total_before},
                "after": {"candidates": total_after},
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "precision": p,
                "recall": r,
                "f1": f,
                "judge_failures": failures,
                "detail": detail,
            },
            indent=1,
        )
    )

    print(f"\n  {'arm':<34}{'cands':>7}{'prec':>8}{'recall':>9}{'F1':>8}{'noise/PR':>10}")
    for label, c, pp, rr, ff in (
        ("ours, nits allowed (before)", 464, 0.216, 0.578, 0.314),
        ("ours + ISOLATED JUDGE (after)", total_after, p, r, f),
        ("ours, nits suppressed", 181, 0.436, 0.457, 0.446),
        ("greptile-v4-1", 161, 0.565, 0.526, 0.545),
        ("qodo-extended-v2", 152, 0.651, 0.572, 0.601),
    ):
        noise = (c * (1 - pp)) / 50
        print(f"  {label:<34}{c:>7}{pp:>8.1%}{rr:>9.1%}{ff:>8.1%}{noise:>10.1f}")

    print(f"\n  TP {tp}  FP {fp}  FN {fn}")
    print("  BAR: discard ~85% of false positives keeping the true ones -> P 64.7%, F1 61.0%")
    print("  THE JUDGE IS THE SAME FAMILY AS THE REVIEWER. It shares the subject's blind spots,")
    print("  so what it discards is a FLOOR; the different-family arm is still owed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
