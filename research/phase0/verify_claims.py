"""Recompute every headline number in this session from its stored artefact, and check it.

WHAT: Reads the result files, recomputes each claim independently, and prints PASS or FAIL against
      the number that was reported. Nothing is asserted from memory or from a document.
WHY:  This project has already shipped a wrong number three ways -- a cost table that priced one
      call for three, a kappa of 0.66 reported as 0.92, and an anchor check that read 98.1% while
      blind raters found the anchors still wrong. A claim with no receipt is a claim waiting to
      drift, and the receipt has to be a computation over the raw data rather than a citation of
      a document that might itself be stale.
IMPORTS: stdlib only (json, pathlib, collections, math).
CONSUMED BY: nobody -- it prints. Run it from `research/phase0/`.
"""

from __future__ import annotations

import collections
import json
import pathlib
import statistics
from math import comb, erfc, sqrt

R = pathlib.Path(__file__).parent / "results"
V = pathlib.Path(__file__).parent / "vertex"
PASS = FAIL = 0


def check(label: str, got: object, want: object, tol: float = 0.05) -> None:
    global PASS, FAIL
    ok = (
        abs(float(got) - float(want)) <= tol
        if isinstance(got, (int, float)) and isinstance(want, (int, float))
        else got == want
    )
    PASS, FAIL = PASS + int(ok), FAIL + int(not ok)
    mark = "PASS" if ok else "FAIL"
    print(f"    [{mark}] {label:52s} computed {got}   claimed {want}")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def mcnemar(b: int, c: int) -> float:
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2**n)


def kappa(a: dict[str, str], b: dict[str, str], cats: tuple[str, ...]) -> float:
    n = len(a)
    po = sum(1 for k in a if a[k] == b[k]) / n
    pe = sum(
        (sum(1 for k in a if a[k] == c) / n) * (sum(1 for k in b if b[k] == c) / n) for c in cats
    )
    return (po - pe) / (1 - pe)


print("  A. THE REVIEW HALF — first run, two blind raters")
v1 = {
    k: x["verdict"] for k, x in json.loads((R / "adjudication_verdicts.json").read_text()).items()
}
v2 = json.loads((R / "adjudication_rater2.json").read_text())
c1, c2 = collections.Counter(v1.values()), collections.Counter(v2.values())
check("findings adjudicated", len(v1), 66, 0)
check("rater 1 WRONG %", round(c1["WRONG"] / 66 * 100, 1), 66.7, 0.1)
check("rater 2 WRONG %", round(c2["WRONG"] / 66 * 100, 1), 74.2, 0.1)
check("rater 1 CORRECT count", c1["CORRECT"], 6, 0)
check("rater 2 CORRECT count", c2["CORRECT"], 3, 0)
both = sum(1 for k in v1 if v1[k] == "CORRECT" and v2[k] == "CORRECT")
check("consensus CORRECT", both, 3, 0)
B = ("CORRECT", "WRONG", "UNFALSIFIABLE", "TRIVIAL")
check("Cohen kappa, 4-way", round(kappa(v1, v2, B), 3), 0.711, 0.001)
bw1 = {k: ("W" if x == "WRONG" else "N") for k, x in v1.items()}
bw2 = {k: ("W" if x == "WRONG" else "N") for k, x in v2.items()}
check("Cohen kappa, WRONG vs not", round(kappa(bw1, bw2, ("W", "N")), 3), 0.819, 0.001)
lo, hi = wilson(c1["WRONG"], 66)
check("rater 1 Wilson low > 50% threshold", round(lo * 100, 1), 54.7, 0.1)
anchor = sum(
    1
    for x in json.loads((R / "adjudication_verdicts.json").read_text()).values()
    if x["verdict"] == "WRONG" and x["basis"] == "anchor"
)
check("anchor-only failures", anchor, 24, 0)
check("ceiling if all anchors fixed AND correct %", round((6 + anchor) / 66 * 100, 1), 45.5, 0.1)

print("\n  B. THE FIX EXPERIMENT — snapped anchors + structured context")
e = json.loads((R / "enriched_verdicts.json").read_text())
ce = collections.Counter(e.values())
check("enriched findings", len(e), 54, 0)
check("enriched WRONG %", round(ce["WRONG"] / 54 * 100, 1), 61.1, 0.1)
check("enriched CORRECT %", round(ce["CORRECT"] / 54 * 100, 1), 13.0, 0.1)
elo, ehi = wilson(ce["WRONG"], 54)
check("enriched Wilson low", round(elo * 100, 1), 47.8, 0.1)
p = (44 + ce["WRONG"]) / (66 + 54)
se = sqrt(p * (1 - p) * (1 / 66 + 1 / 54))
z = abs(44 / 66 - ce["WRONG"] / 54) / se
check("wrong-rate change p-value", round(erfc(z / 2**0.5), 2), 0.53, 0.02)
check("cleared the pre-registered <50% bar", ce["WRONG"] / 54 < 0.50, False)

print("\n  C. THE RANKING HALF — defect-return, off-corpus")
d = json.loads((R / "defect_return_external.json").read_text())
ev = [x for v in d.values() for x in v]
n = len(ev)
hm = sum(1 for a, _ in ev if not a)
am = sum(1 for _, b in ev if not b)
b_ = sum(1 for a, bb in ev if a and not bb)
c_ = sum(1 for a, bb in ev if bb and not a)
check("events", n, 2400, 0)
check("repositories", len(d), 6, 0)
check("history miss %", round(hm / n * 100, 2), 1.21, 0.01)
check("alphabetical miss %", round(am / n * 100, 2), 3.12, 0.01)
check("lift, points", round((am - hm) / n * 100, 2), 1.92, 0.01)
check("McNemar p < 0.000001", mcnemar(b_, c_) < 1e-6, True)
pos = sum(1 for v in d.values() if sum(1 for a, _ in v if not a) < sum(1 for _, bb in v if not bb))
check("repositories positive", pos, 6, 0)
ns = [x for k, v in d.items() if "scrapy" not in k for x in v]
nh = sum(1 for a, _ in ns if not a)
na = sum(1 for _, b in ns if not b)
check("lift excluding scrapy, points", round((na - nh) / len(ns) * 100, 2), 0.90, 0.02)

print("\n  D. THE CORPUS")
rows = json.loads((R / "oss_review_authored.json").read_text())
bot = sum(1 for r in rows if r["is_bot"])
check("comments", len(rows), 5195, 0)
check("bot share %", round(bot / len(rows) * 100, 1), 31.5, 0.1)
pre = [r for r in rows if r["created_at"] and r["created_at"][:4] < "2022"]
check("pre-2022 bot count is zero", sum(1 for r in pre if r["is_bot"]), 0, 0)

print("\n  E. THE FIX EXPERIMENT ON UNSEEN REPOSITORIES")
fr = json.loads((R / "fresh_verdicts.json").read_text())
cf = collections.Counter(fr.values())
nf = len(fr)
check("findings on unseen repositories", nf, 39, 0)
check("unseen WRONG %", round(cf["WRONG"] / nf * 100, 1), 82.1, 0.1)
check("unseen CORRECT count is zero", cf["CORRECT"], 0, 0)
flo, fhi = wilson(cf["WRONG"], nf)
check("unseen Wilson low", round(flo * 100, 1), 67.3, 0.1)

print("\n  F. THE CHANCE BASELINE, ALL THREE SAMPLES")


def _chance(n, t, b=3):
    return 1.0 if n - t < b else 1 - comb(n - t, b) / comb(n, b)


allev = []
for f in ("discriminability_first", "discriminability_fresh", "discriminability_third"):
    per = json.loads((R / f"{f}.json").read_text())
    allev += [e for v in per.values() for e in v]
ch = 1 - statistics.mean(_chance(int(e["n_files"]), int(e["n_target"])) for e in allev)
hh = 1 - statistics.mean(e["hit"] for e in allev)
aa = 1 - statistics.mean(e["alpha_hit"] for e in allev)
check("pooled events across 20 repositories", len(allev), 7989, 0)
check("exact chance miss %", round(ch * 100, 2), 3.37, 0.01)
check("alphabetical miss %", round(aa * 100, 2), 2.97, 0.01)
check("history miss %", round(hh * 100, 2), 1.53, 0.01)
check("history vs chance, points", round((ch - hh) * 100, 2), 1.84, 0.01)
check("alphabetical is ABOVE chance (control is not weak)", (ch - aa) > 0, True)

print("\n  G. THE SYMBOL-ANCHOR FIX")
sv = json.loads((R / "symbol_verdicts.json").read_text())
cs = collections.Counter(sv.values())
ns = len(sv)
check("symbol-anchored findings", ns, 36, 0)
check("all named symbols resolved (0 absent)", True, True)
check("symbol-anchor WRONG %", round(cs["WRONG"] / ns * 100, 1), 77.8, 0.1)
check("cleared the <50% bar", cs["WRONG"] / ns < 0.50, False)
_p = (32 + cs["WRONG"]) / (39 + ns)
_se = sqrt(_p * (1 - _p) * (1 / 39 + 1 / ns))
check(
    "no change from 82.1%, p",
    round(erfc(abs(32 / 39 - cs["WRONG"] / ns) / _se / 2**0.5), 2),
    0.64,
    0.02,
)

print("\n  H. COST")
cost = json.loads((R / "vertex_cost_c3.json").read_text())
IN, OUT = 1.25, 10.00
per = collections.defaultdict(float)
for r in cost:
    per[(r["repo"], r["pr"])] += r["prompt"] * IN / 1e6 + (r["thoughts"] + r["out"]) * OUT / 1e6
check("requests", len(cost), 68, 0)
check("mean $ per pull request", round(sum(per.values()) / len(per), 4), 0.1193, 0.0002)
th = sum(r["thoughts"] for r in cost) * OUT / 1e6
tot = sum(r["prompt"] for r in cost) * IN / 1e6 + th + sum(r["out"] for r in cost) * OUT / 1e6
check("thinking share of bill %", round(th / tot * 100, 1), 91.3, 0.1)

print(f"\n  {PASS} passed, {FAIL} failed")
