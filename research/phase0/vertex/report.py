"""Report the billed C3 run per request, with the caveats attached to the number itself.

WHAT: Reads `vertex_cost.json` and prints per-request token and dollar detail, the per-PR roll
      up, an internal consistency check on the token accounting, and the schema drop rate.
WHY:  The cost table failed once already by aggregating three calls into one line -- it priced
      one call for three and inverted the sign of the product's cost argument. So the unit of
      reporting here is the REQUEST, and the per-PR figure is derived in view rather than
      measured directly.

      THREE THINGS THIS RUN CANNOT SAY, printed alongside the number so they travel with it:
      it declares NO cached content, so it is the uncached ceiling and not the steady state the
      $0.140 estimate assumed; it says nothing about whether the findings are any good, since
      nothing adjudicated them; and its population is 24 merged pull requests from the same 8
      repositories whose representativeness is unestablished.
IMPORTS: stdlib only (collections, json, statistics, sys).
CONSUMED BY: nobody -- it prints.
"""

from __future__ import annotations

import collections
import json
import statistics
import sys

IN_RATE, OUT_RATE = 1.25, 10.00  # gemini-2.5-pro list, USD per 1M, <=200k context
DERIVED_ESTIMATE = 0.140


def cost_of(r: dict[str, object]) -> float:
    return int(r["prompt"]) * IN_RATE / 1e6 + (int(r["thoughts"]) + int(r["out"])) * OUT_RATE / 1e6


def main() -> int:
    with open("vertex_cost.json") as fh:
        rows = json.load(fh)
    if not rows:
        print("  REFUSING TO REPORT — empty result file")
        return 1

    print("  PER REQUEST — the unit of measurement, because aggregating three calls into one")
    print("  line is the exact defect that inverted this table's sign once already.\n")
    print(
        f"  {'repo':13s} {'pr':>7} {'unit':24s} {'lines':>5} {'in':>7} {'think':>7} "
        f"{'out':>6} {'$':>8}"
    )
    for r in rows:
        print(
            f"  {str(r['repo']).split('/')[1][:13]:13s} {r['pr']:>7} "
            f"{str(r['unit'])[:24]:24s} {r['unit_lines']:>5} {r['prompt']:>7} "
            f"{r['thoughts']:>7} {r['out']:>6} {cost_of(r):8.5f}"
        )

    # Consistency: Vertex should account for every billed token we know about. If total exceeds
    # the three components, something else is being billed and the cost figure is a floor.
    bad = [
        r for r in rows if int(r["total"]) != int(r["prompt"]) + int(r["thoughts"]) + int(r["out"])
    ]
    print(
        f"\n  token accounting: {len(rows) - len(bad)}/{len(rows)} requests where "
        f"total == prompt + thinking + answer"
    )
    if bad:
        d = [int(r["total"]) - int(r["prompt"]) - int(r["thoughts"]) - int(r["out"]) for r in bad]
        print(
            f"    UNEXPLAINED on {len(bad)}: residual mean {statistics.mean(d):.0f} "
            f"min {min(d)} max {max(d)} — the dollar figure below is a FLOOR"
        )

    print("\n  DISTRIBUTIONS")
    for label, key in (("prompt", "prompt"), ("thinking", "thoughts"), ("answer", "out")):
        v = [int(r[key]) for r in rows]
        print(
            f"    {label:9s} mean {statistics.mean(v):8.0f}  median {statistics.median(v):7.0f}"
            f"  p90 {sorted(v)[int(0.9 * (len(v) - 1))]:7.0f}  max {max(v):7d}"
        )
    th = sum(int(r["thoughts"]) for r in rows)
    an = sum(int(r["out"]) for r in rows)
    print(
        f"    thinking is {th / max(1, th + an):.1%} of billed output tokens "
        f"({th:,} vs {an:,} answer)"
    )

    by_pr: dict[tuple[str, int], list[dict[str, object]]] = collections.defaultdict(list)
    for r in rows:
        by_pr[(str(r["repo"]), int(r["pr"]))].append(r)
    costs = sorted(sum(cost_of(r) for r in v) for v in by_pr.values())
    reqs = [len(v) for v in by_pr.values()]
    print(f"\n  PER PULL REQUEST  ({len(costs)} PRs, {statistics.mean(reqs):.1f} requests each)")
    print(f"    mean   ${statistics.mean(costs):.4f}")
    print(f"    median ${statistics.median(costs):.4f}")
    print(f"    p90    ${costs[int(0.9 * (len(costs) - 1))]:.4f}")
    print(f"    max    ${max(costs):.4f}")
    print(
        f"    the derived estimate it replaces was ${DERIVED_ESTIMATE:.3f} — "
        f"ratio {statistics.mean(costs) / DERIVED_ESTIMATE:.2f}x"
    )

    empty = sum(1 for r in rows if str(r["text"]).strip() in ("[]", "```json\n[]\n```", ""))
    parsed = 0
    findings = 0
    for r in rows:
        t = str(r["text"]).strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        try:
            d = json.loads(t)
        except json.JSONDecodeError:
            continue
        if isinstance(d, list):
            parsed += 1
            findings += len(d)
    print("\n  SCHEMA CONFORMANCE — recorded, NOT interpreted")
    print(f"    responses parsing as a JSON array   {parsed}/{len(rows)}")
    print(f"    returned the empty array            {empty}/{len(rows)}")
    print(f"    findings emitted in total           {findings}")
    print("    Near-total conformance is the EXPECTED outcome of forcing the schema. It says")
    print("    the schema works. It says nothing about whether a single finding is correct —")
    print("    published-and-wrong is untested and needs hands.")

    print("\n  WHAT THIS NUMBER CANNOT SAY")
    print("    1. NO CACHED CONTENT WAS DECLARED. This is the uncached ceiling. The $0.140")
    print("       estimate assumed prefix caching at 0.1x, so the two are not like for like.")
    print("    2. Nothing here evaluates finding quality. 24 PRs and 203 units move C3 from")
    print("       priced to billed; they do not touch precision.")
    print("    3. Population: 24 merged PRs from the same 8 repositories, median 20-line units.")
    print("       Whether that resembles a customer's diff is unestablished.")
    return 0


sys.exit(main())
