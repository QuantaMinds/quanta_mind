"""Recompute design thirteen's numbers -- expansion and the conventions file -- from its artefacts.

WHAT: `run(check)` recomputes every figure this project publishes about design thirteen and passes
      each to the caller's comparator. It asserts nothing itself and holds no counters.
WHY:  `verify.py` reached the 200-line cap, and the fix for a file over the cap is to split it by
      concern rather than raise the cap. This is one concern: the run that measured enclosing-
      function expansion and the repository conventions file.

      IT TAKES `check` AS AN ARGUMENT rather than importing it, so the pass/fail counters stay in
      one place. Two modules each keeping their own tally is how a total stops matching its parts.
IMPORTS: stdlib only (collections, json, pathlib).
CONSUMED BY: `verify.py` in this package.
"""

from __future__ import annotations

import collections
import json
import pathlib
from collections.abc import Callable

Q = pathlib.Path(__file__).parent.parent / "quote"


def run(check: Callable[..., None]) -> None:
    """Recompute and check every design-thirteen figure. Raises if an artefact is missing."""
    key = {
        int(k["item"]): k for k in json.loads((Q / "adj13" / "KEY_DO_NOT_OPEN.json").read_text())
    }
    ver = json.loads((Q / "adj13" / "verdicts.json").read_text())
    run13 = json.loads((Q / "results" / "quote13_run.json").read_text())

    def _bucket(i: int) -> str:
        return str(ver[str(i)]).split()[0]

    def _cause(i: int) -> str:
        return str(ver[str(i)]).split()[-1]

    sab = [i for i, k in key.items() if k["kind"] == "SABOTAGE"]
    check("sabotaged controls planted", len(sab), 10, 0)
    check("sabotaged controls caught as WRONG", sum(_bucket(i) == "WRONG" for i in sab), 10, 0)

    arms = collections.defaultdict(list)
    for i, k in key.items():
        if k["kind"] == "real":
            arms[k["arm"]].append(i)
    for arm, want_n, want_w in (("A", 29, 51.7), ("B", 27, 59.3), ("C", 30, 46.7)):
        idx = arms[arm]
        w = sum(_bucket(i) == "WRONG" for i in idx)
        check(f"arm {arm} findings rated", len(idx), want_n, 0)
        check(f"arm {arm} wrong-rate %", round(w / len(idx) * 100, 1), want_w, 0.1)

    for arm, want in (("A", 73.3), ("B", 18.8)):
        wr = [i for i in arms[arm] if _bucket(i) == "WRONG"]
        ta = sum(_cause(i) in ("TRACE", "ABSENT") for i in wr)
        check(f"arm {arm} TRACE+ABSENT share of wrong %", round(ta / len(wr) * 100, 1), want, 0.1)

    def _kind(path: str) -> str:
        return "ci" if path.startswith(".github/") or path.endswith((".yml", ".yaml")) else "other"

    ci = [i for i, k in key.items() if k["kind"] == "real" and _kind(str(k["path"])) == "ci"]
    ci_w = [i for i in ci if _bucket(i) == "WRONG"]
    check("CI-config findings", len(ci), 36, 0)
    check("CI-config wrong-rate %", round(len(ci_w) / len(ci) * 100, 1), 66.7, 0.1)
    check("CI-config wrong that are EXTERNAL", sum(_cause(i) == "EXTERNAL" for i in ci_w), 23, 0)

    ex = run13["expand"]
    check("hunks seen by expansion", ex["hunks"], 453, 0)
    check("hunks expanded", ex["expanded"], 230, 0)
    check("expansion rate %", round(ex["expanded"] / ex["hunks"] * 100, 1), 50.8, 0.1)
    check("pull requests reviewed", run13["prs"], 80, 0)
    for arm, want in (("A", 0.41), ("B", 0.40), ("C", 0.46)):
        pub = sum(len(r["published"].get(arm, [])) for r in run13["results"])
        check(f"arm {arm} yield per pull request", round(pub / run13["prs"], 2), want, 0.01)

    # --- bucket composition: is arm C's gain accuracy, or hedging? ---
    for arm, want_c, want_u in (("A", 2, 4), ("B", 2, 4), ("C", 3, 8)):
        idx = arms[arm]
        check(f"arm {arm} CORRECT count", sum(_bucket(i) == "CORRECT" for i in idx), want_c, 0)
        check(
            f"arm {arm} UNFALSIFIABLE count",
            sum(_bucket(i) == "UNFALSIFIABLE" for i in idx),
            want_u,
            0,
        )
    for arm, want in (("A", 6.9), ("B", 7.4), ("C", 10.0)):
        idx = arms[arm]
        c = sum(_bucket(i) == "CORRECT" for i in idx)
        check(f"arm {arm} CORRECT-rate %", round(c / len(idx) * 100, 1), want, 0.1)

    # --- design eleven: which arm cleared its own yield bar ---
    d11 = json.loads((Q / "results" / "quote11_run.json").read_text())
    n11 = d11["n_prs"]
    check("design 11 pull requests", n11, 58, 0)
    for arm, want in (("arm_r", 0.40), ("arm_e", 0.22)):
        check(
            f"design 11 {arm} yield per PR", round(len(d11[arm]["published"]) / n11, 2), want, 0.01
        )
    check(
        "design 11 arm R clears the 0.30 yield bar",
        len(d11["arm_r"]["published"]) / n11 >= 0.30,
        True,
    )
    check("design 11 arm E fails it", len(d11["arm_e"]["published"]) / n11 < 0.30, True)

    # --- the binding number: correct findings per pull request, and what excluding CI costs ---
    def _ci(path: str) -> bool:
        return path.startswith(".github/") or path.endswith((".yml", ".yaml"))

    real = [
        (k["arm"], _ci(str(k["path"])), _bucket(i)) for i, k in key.items() if k["kind"] == "real"
    ]
    for arm, want_all, want_off in (("A", 2, 1), ("B", 2, 1), ("C", 3, 1)):
        allc = sum(1 for r in real if r[0] == arm and r[2] == "CORRECT")
        offc = sum(1 for r in real if r[0] == arm and not r[1] and r[2] == "CORRECT")
        check(f"arm {arm} CORRECT findings, all files", allc, want_all, 0)
        check(f"arm {arm} CORRECT findings off CI config", offc, want_off, 0)
    ci_c = sum(1 for r in real if r[1] and r[2] == "CORRECT")
    ci_w = sum(1 for r in real if r[1] and r[2] == "WRONG")
    all_c = sum(1 for r in real if r[2] == "CORRECT")
    all_w = sum(1 for r in real if r[2] == "WRONG")
    check(
        "CI config CORRECT-rate %", round(ci_c / sum(1 for r in real if r[1]) * 100, 1), 11.1, 0.1
    )
    check(
        "off-CI CORRECT-rate %",
        round((all_c - ci_c) / sum(1 for r in real if not r[1]) * 100, 1),
        6.0,
        0.1,
    )
    check("share of CORRECT lost by excluding CI %", round(ci_c / all_c * 100, 0), 57, 1)
    check("share of WRONG lost by excluding CI %", round(ci_w / all_w * 100, 0), 53, 1)
    check(
        "excluding CI costs proportionally MORE correct than wrong",
        ci_c / all_c > ci_w / all_w,
        True,
    )

    # --- aggregation: would keeping what recurs across runs help? ---
    def _ident(k: dict) -> tuple:
        return (k["repo"], k["pr"], k["path"], k["line"])

    seen_by: dict[tuple, set] = collections.defaultdict(set)
    verdicts: dict[tuple, set] = collections.defaultdict(set)
    for i, k in key.items():
        if k["kind"] == "real":
            seen_by[_ident(k)].add(k["arm"])
            verdicts[_ident(k)].add(_bucket(i))
    corr = {t: a for t, a in seen_by.items() if "CORRECT" in verdicts[t]}
    wrong = {t: a for t, a in seen_by.items() if "WRONG" in verdicts[t]}
    check("distinct CORRECT findings across arms", len(corr), 5, 0)
    check("CORRECT found by exactly one arm", sum(1 for a in corr.values() if len(a) == 1), 4, 0)
    check(
        "CORRECT kept by a >=2-of-3 aggregator", sum(1 for a in corr.values() if len(a) >= 2), 1, 0
    )
    check(
        "aggregation keeps FEWER correct than the best single arm",
        sum(1 for a in corr.values() if len(a) >= 2) < 3,
        True,
    )
    rc = sum(1 for a in corr.values() if len(a) >= 2) / len(corr)
    rw = sum(1 for a in wrong.values() if len(a) >= 2) / len(wrong)
    check("CORRECT recurrence rate %", round(rc * 100, 0), 20, 1)
    check("WRONG recurrence rate %", round(rw * 100, 0), 37, 1)
    check("wrong findings recur MORE often than correct ones", rw > rc, True)
