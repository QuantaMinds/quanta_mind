"""Run PLAIN twice and score both, to measure the noise floor the bar was actually set against.

WHAT: Reviews the same 50 changes with no context, twice, judges both, and reports the gap between
      two runs of the SAME arm.
WHY:  **THE 2.1-POINT BAR IS THE JUDGE'S REPLICATE SPREAD, WHICH IS ONLY ONE TERM OF THE NOISE.**
      That figure comes from re-judging the same comments and watching the score move. It does not
      capture the larger term: the reviewer is stochastic, so re-running it produces a DIFFERENT
      comment set, and total variance is generation plus judging.

      So "+5.2 points is two and a half times the noise floor" was not established -- it is 2.5x a
      component of the floor. This measures the whole thing the only way it can be measured: two
      runs that differ in nothing except the seed the model does not let us set.

      **THE EXPECTED VALUE OF THIS ARM'S EFFECT IS ZERO.** Whatever gap appears between PLAIN and
      PLAIN is noise by construction, and the shape effect has to be read against it. A replicate
      gap near +5 would make the headline uninterpretable; a gap near 0 would leave it standing.
IMPORTS: stdlib; the local `bench_reviewer`, `judge`, `martian_corpus`; the Vertex `client`.
CONSUMED BY: read by a human; writes `results/shape_replicate.json`.
"""

from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "vertex"))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))

import bench_reviewer as br  # noqa: E402
import judge  # noqa: E402
import martian_corpus as mc  # noqa: E402
from client import Client  # noqa: E402

OUT = HERE.parents[1] / "results" / "shape_replicate.json"
RUNS = ("PLAIN_A", "PLAIN_B")


def main() -> int:
    mc._assert_intact()
    client = Client("gemini-2.5-pro")
    pulls = [p for p in mc.pulls() if p.get("golden")]
    arms: dict[str, dict[str, list[str]]] = {r: {} for r in RUNS}

    for pull in pulls:
        key, url = str(pull["key"]), str(pull["original"])
        try:
            diff = mc.diff(url)
        except mc.FetchFailed:
            continue
        for run in RUNS:
            try:
                issues, _ = br.review(client, str(pull["title"]), diff)
            except br.ReviewFailed:
                continue
            arms[run][key] = issues
        print(
            f"    {url[-26:]:>26}  A {len(arms['PLAIN_A'].get(key, [])):>2}  "
            f"B {len(arms['PLAIN_B'].get(key, [])):>2}",
            flush=True,
        )

    scored: dict[str, dict[str, int]] = {}
    for run in RUNS:
        covered = emitted = 0
        for pull in pulls:
            texts = arms[run].get(str(pull["key"]), [])
            if not texts:
                continue
            got = judge.verdicts(client, [str(g) for g in pull["golden"]], texts)
            covered += len(got["tp"])
            emitted += len(texts)
        scored[run] = {"defects_found": covered, "comments": emitted}
        print(f"\n  {run:<10} {covered} of 173 defects, {emitted} comments", flush=True)

    a, b = scored["PLAIN_A"], scored["PLAIN_B"]
    points = (b["defects_found"] - a["defects_found"]) / 173 * 100
    OUT.write_text(json.dumps({"scored": scored, "points": points, "arms": arms}, indent=1))
    print(f"\n  SAME-ARM GAP: {a['defects_found']} vs {b['defects_found']}  ({points:+.1f} points)")
    print("  This is generation noise plus judging noise. The 2.1-point bar covered judging only.")
    print(
        f"  The shape effect was +5.2 points; read it against {abs(points):.1f}, not against 2.1."
    )
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
