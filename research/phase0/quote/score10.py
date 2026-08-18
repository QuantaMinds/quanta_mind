"""Score all three design-ten arms from one verdict file, with the control reported first.

WHAT: Joins the hand verdicts to the arm key, reports the sabotage catch rate, then arm A's
      wrong-rate (the replication of design nine) and B's and C's against it.
WHY:  B and C are index subsets of A, so a single blind rating pass scores all three and the rater
      never sees an arm label. The A-versus-B and A-versus-C deltas are therefore robust to rater
      leniency even though the absolute levels are not.

      DEDUPLICATED DENOMINATORS THROUGHOUT. Design nine's headline moved 30.6% to 34.9% once the
      model's own repeated findings were collapsed, and the duplicates all sat in TRIVIAL.
IMPORTS: stdlib only (collections, json, math, pathlib, sys).
CONSUMED BY: nobody -- it prints.
"""

from __future__ import annotations

import collections
import json
import math
import pathlib
import sys
from math import comb

HERE = pathlib.Path(__file__).resolve().parent
ADJ = HERE / "adj10"
RUN = HERE / "quote10_run.json"
WRONG_BAR = 0.50


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def fisher(a: int, b: int, c: int, d: int) -> float:
    def p(a: int, b: int, c: int, dd: int) -> float:
        return comb(a + b, a) * comb(c + dd, c) / comb(a + b + c + dd, a + c)

    obs, tot = p(a, b, c, d), 0.0
    for i in range(0, min(a + b, a + c) + 1):
        j, k = (a + b) - i, (a + c) - i
        ll = (c + d) - k
        if j < 0 or k < 0 or ll < 0:
            continue
        pr = p(i, j, k, ll)
        if pr <= obs + 1e-12:
            tot += pr
    return tot


def main() -> int:
    key = {r["item"]: r for r in json.loads((ADJ / "KEY_DO_NOT_OPEN.json").read_text())}
    verdicts = json.loads((ADJ / "verdicts.json").read_text())
    blob = json.loads(RUN.read_text())
    arm_a, arm_b, arm_c = blob["arm_a"], set(blob["arm_b"]), set(blob["arm_c"])

    if len(verdicts) != len(key):
        print(f"  REFUSING TO REPORT — {len(verdicts)} verdicts against {len(key)} items")
        return 1

    sab = collections.Counter()
    rated: list[tuple[int, str]] = []  # (index into arm_a, verdict)
    for n_str, verdict in verdicts.items():
        n = int(n_str)
        if str(key[n]["kind"]) == "SABOTAGE":
            sab[verdict] += 1
        else:
            rated.append((int(key[n]["idx"]), verdict))

    ns, caught = sum(sab.values()), sab["WRONG"]
    print("  J3 CONTROL FIRST — sabotaged findings, claim lifted from a different pull request\n")
    print(f"    {ns} controls, graded WRONG {caught}, catch rate {caught / ns:.0%}" if ns else "")
    if ns and caught / ns < 0.75:
        print("\n  VOID — the rater passed too many controls to be believed on the real findings.")
        return 1
    print("    [PASS] the rater discriminates\n")

    # Deduplicate by (pull request, claim) using arm A's own records.
    seen: dict[tuple[str, int, str], int] = {}
    uniq: set[int] = set()
    for idx, _v in rated:
        f = arm_a[idx]
        k = (str(f["repo"]), int(str(f["pr"])), str(f["claim"]))
        if k not in seen:
            seen[k] = idx
            uniq.add(idx)
    vmap = dict(rated)

    def arm(name: str, members: set[int]) -> tuple[int, int, int]:
        idxs = [i for i in members if i in vmap and i in uniq]
        c = collections.Counter(vmap[i] for i in idxs)
        n = len(idxs)
        print(
            f"    {name:24s} n={n:3d}  CORRECT {c['CORRECT']:3d}  TRIVIAL {c['TRIVIAL']:3d}  "
            f"UNFALS {c['UNFALSIFIABLE']:3d}  WRONG {c['WRONG']:3d}"
        )
        return n, c["WRONG"], c["CORRECT"]

    print(f"  THE THREE ARMS, deduplicated ({len(uniq)} unique of {len(rated)} rated)\n")
    na, wa, ca = arm("A  design nine", set(range(len(arm_a))))
    nb, wb, cb = arm("B  + lexical marker", arm_b)
    nc, wc, cc_ = arm("C  + model gate", arm_c)

    print(f"\n  {'arm':24s} {'wrong-rate':>11} {'95% Wilson':>16} {'correct':>9}")
    for name, n, w, c in (
        ("A design nine", na, wa, ca),
        ("B lexical", nb, wb, cb),
        ("C model", nc, wc, cc_),
    ):
        if not n:
            continue
        lo, hi = wilson(w, n)
        print(f"  {name:24s} {w / n:10.1%} {lo:8.1%}-{hi:6.1%} {c / n:8.1%}")

    lo, hi = wilson(wa, na) if na else (0, 0)
    print(f"\n  J2 REPLICATION — arm A wrong-rate {wa / na:.1%}, Wilson {lo:.1%}-{hi:.1%}")
    print("     design nine was 34.9%, Wilson 22.4%-49.8%")
    ok2 = na and wa / na < WRONG_BAR and hi < WRONG_BAR
    print(f"     [{'PASS — clean' if ok2 else 'FAIL or CANNOT DISTINGUISH'}]")

    for name, n, w, c in (("B lexical", nb, wb, cb), ("C model", nc, wc, cc_)):
        if not n or not na:
            continue
        p = fisher(wa, na - wa, w, n - w)
        better = w / n < wa / na
        if better and p < 0.05:
            verdict = "PASS"
        elif better:
            verdict = "FAIL - direction only"
        else:
            verdict = "FAIL - wrong direction"
        kind = "a precision filter" if c / n >= ca / na else "a VOLUME CONTROL"
        print(f"\n  J1 {name} vs A: {w / n:.1%} against {wa / na:.1%}, Fisher p = {p:.4f}")
        print(f"     [{verdict}]")
        print(f"     prediction 5: CORRECT {c}/{n} = {c / n:.1%} against A's {ca / na:.1%}")
        print(f"     -> {kind}")
    print(f"\n  gate errors: {blob.get('gate_errors', 0)}")
    return 0


sys.exit(main())
