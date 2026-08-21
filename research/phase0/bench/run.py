"""Run the head-to-head: calibrate the judge, then score every arm on the same 50 pull requests.

WHAT: Judges CodeRabbit's checked-in candidates with our Gemini judge and compares against their
      published Claude-judged precision (bar P0). Only if that calibrates does it review the 50
      pull requests with our reviewer and score every arm.
WHY:  A different judge model makes every number a comparison between judges unless it is shown
      not to. P0 is checked and printed FIRST, so a miscalibrated judge cannot be discovered after
      the headline is already known and then explained away.
      → `docs/plans/preregistrations/reviewer/martian-comparison-preregistration.md`
IMPORTS: stdlib only (json, pathlib, sys, time). Local: `corpus`, `judge`, `reviewer`, and the
      Vertex `client`.
CONSUMED BY: nobody -- it prints and writes martian_comparison.json.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "vertex"))

import bench_reviewer as reviewer
import judge
import martian_corpus as corpus
from client import Client

MODEL = "gemini-2.5-pro"
RIVALS = ("coderabbit", "greptile-v4-1")  # calibration tool + the offline precision leader
CALIBRATION_TOOL = "coderabbit"
CALIBRATION_TOLERANCE = 0.10
OUT = pathlib.Path(__file__).resolve().parent / "results" / "martian_comparison.json"


def judge_arm(client: Client, prs: list[dict], cands: dict[str, list[str]], label: str) -> dict:
    """Score one arm across all 50 pull requests. Prints progress; never hides an empty arm.

    Completed arms are cached to disk. A harness defect in a LATER arm should not cost a
    twenty-minute recalibration of an EARLIER one -- but the cache is keyed by arm label only, so
    delete `arm_*.json` whenever the judge prompt or the candidates change.
    """
    cache = (
        pathlib.Path(__file__).resolve().parent / "results" / f"arm_{label.replace('/', '_')}.json"
    )
    if cache.exists():
        done = json.loads(cache.read_text())
        print(f"    {label}: cached  P={done['precision']:.1%} R={done['recall']:.1%}")
        return done
    tp = fp = fn = errors = 0
    reviewed = 0
    t0 = time.time()
    for i, pr in enumerate(prs, 1):
        golden = list(pr["golden"])
        cs = cands.get(str(pr["key"]), [])
        if cs:
            reviewed += 1
        v = judge.verdicts(client, golden, cs)
        tp += len(v["tp"])
        fp += len(v["fp"])
        fn += len(v["fn"])
        errors += int(v["errors"])
        if i % 10 == 0:
            p, r, f = judge.score(tp, fp, fn)
            el = time.time() - t0
            print(f"    {label}: {i}/{len(prs)}  P={p:.1%} R={r:.1%} F1={f:.1%}  ({el:.0f}s)")
    p, r, f = judge.score(tp, fp, fn)
    out = {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "errors": errors,
        "prs_with_output": reviewed,
        "precision": p,
        "recall": r,
        "f1": f,
    }
    cache.write_text(json.dumps(out))
    return out


def main() -> int:
    prs = corpus.pulls()
    print(f"  {len(prs)} pull requests, {sum(len(p['golden']) for p in prs)} golden comments\n")
    client = Client(MODEL)

    # ---- P0: calibrate the judge BEFORE anything else is computed ----
    ptp, pfp, pfn = corpus.published(CALIBRATION_TOOL)
    their_p = ptp / (ptp + pfp) if ptp + pfp else 0.0
    print(f"  P0 CALIBRATION — judging {CALIBRATION_TOOL} with our Gemini judge")
    print(f"    their Claude judge: P={their_p:.1%} (tp={ptp} fp={pfp} fn={pfn})")
    cal = judge_arm(client, prs, corpus.rival_candidates(CALIBRATION_TOOL), CALIBRATION_TOOL)
    delta = abs(cal["precision"] - their_p)
    ok = delta <= CALIBRATION_TOLERANCE
    print(f"    our Gemini judge  : P={cal['precision']:.1%} (tp={cal['tp']} fp={cal['fp']})")
    print(f"    |delta| = {delta * 100:.1f} points, tolerance {CALIBRATION_TOLERANCE * 100:.0f}")
    print(f"    [{'PASS' if ok else 'FAIL'}] P0\n")
    if not ok:
        print("  VOID — our judge does not reproduce theirs, so this would compare judges,")
        print("  not reviewers. Reported as void, per the pre-registration.")
        OUT.write_text(json.dumps({"void": True, "calibration": cal, "their_p": their_p}))
        return 1

    arms: dict[str, dict] = {CALIBRATION_TOOL: cal}

    # ---- our arm ----
    print("  reviewing 50 pull requests with our reviewer")
    ours: dict[str, list[str]] = {}
    finishes: dict[str, int] = {}
    for i, pr in enumerate(prs, 1):
        try:
            d = corpus.diff(str(pr["original"]))
            issues, finish = reviewer.review(client, str(pr["title"]), d)
        except (corpus.FetchFailed, reviewer.ReviewFailed, KeyError, IndexError) as exc:
            print(f"    {i:2d}/50 {str(pr['original'])[-28:]:28s} FAILED: {str(exc)[:70]}")
            finishes["FAILED"] = finishes.get("FAILED", 0) + 1
            continue
        ours[str(pr["key"])] = issues
        finishes[finish] = finishes.get(finish, 0) + 1
        print(f"    {i:2d}/50 {str(pr['original'])[-28:]:28s} {len(issues):2d} issues  {finish}")
    print(f"\n  finish reasons: {finishes}")
    print(f"  pull requests with a review: {len(ours)}/{len(prs)}  (bar P4 needs >= 40)\n")

    arms["OURS"] = judge_arm(client, prs, ours, "OURS")
    for tool in RIVALS:
        if tool == CALIBRATION_TOOL:
            continue
        print(f"  judging {tool}")
        arms[tool] = judge_arm(client, prs, corpus.rival_candidates(tool), tool)

    OUT.write_text(json.dumps({"arms": arms, "ours_candidates": ours}, indent=1))
    cols = f"{'PRs':>4} {'TP':>4} {'FP':>4} {'FN':>4} {'prec':>8} {'recall':>8} {'F1':>7}"
    hdr = f"{'arm':16s} {cols}"
    print(f"\n  {hdr}")
    for name, a in sorted(arms.items(), key=lambda kv: -kv[1]["f1"]):
        print(
            f"  {name:16s} {a['prs_with_output']:4d} {a['tp']:4d} {a['fp']:4d} {a['fn']:4d} "
            f"{a['precision']:9.1%} {a['recall']:7.1%} {a['f1']:6.1%}"
        )

    cr, us = arms[CALIBRATION_TOOL], arms["OURS"]
    bars = [
        (
            "P1 our precision >= coderabbit's",
            us["precision"] >= cr["precision"],
            f"{us['precision']:.1%} vs {cr['precision']:.1%}",
        ),
        ("P2 our F1 >= coderabbit's", us["f1"] >= cr["f1"], f"{us['f1']:.1%} vs {cr['f1']:.1%}"),
        ("P4 >= 40 of 50 PRs reviewed", us["prs_with_output"] >= 40, f"{us['prs_with_output']}/50"),
    ]
    print("\n  PRE-REGISTERED BARS")
    for label, okk, detail in bars:
        print(f"    [{'PASS' if okk else 'FAIL'}] {label:38s} {detail}")
    print(f"    (P3 recall reported without a bar: {us['recall']:.1%})")
    return 0


sys.exit(main())
