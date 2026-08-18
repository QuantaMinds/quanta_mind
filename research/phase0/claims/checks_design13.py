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
