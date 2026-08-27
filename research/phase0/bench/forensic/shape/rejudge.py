"""Per-defect verdicts for both arms, so the PAIRED statistic can be computed.

WHAT: Re-judges the stored comments from `results/shape_context.json` and records, for every one
      of the 173 golden defects, whether each arm found it. Writes `results/shape_rejudge.json`
      and prints McNemar's discordant pairs plus a per-repository split.
WHY:  **81 AND 90 ARE MARGINS, AND MARGINS DO NOT SETTLE A PAIRED COMPARISON.** 9:0 and 25:16
      produce the same +9 headline and opposite conclusions. Every comparable result in this
      project reports the discordant pairs -- 62:16, 17:5, 26:6 -- and the one favourable result
      reporting differently is exactly what a reader should be suspicious of.

      The first run stored only the two aggregate counts, so the pairs could not be recovered from
      it. **This re-judges rather than re-reviews**: the comments are already on disk, so no new
      model output is generated and the arms being compared are the same texts that produced the
      headline.

      **THE JUDGE IS BLIND TO ARM BY CONSTRUCTION.** `judge.JUDGE_PROMPT` takes one golden and one
      candidate and nothing else -- no arm name, no ordering, no shape block -- and every pair is
      judged independently. That does NOT make the comparison immune to phrasing: if the shape
      block changes how a finding is worded, a judge agreeing with a careful rater 34.9% of the
      time has room to reward the wording. Blinding removes label leakage, not that channel, and
      the writeup says so.
IMPORTS: stdlib; the local `judge` and Vertex `client`; the corpus via `martian_corpus`.
CONSUMED BY: read by a human; writes `results/shape_rejudge.json`.
"""

from __future__ import annotations

import collections
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "vertex"))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))

import judge  # noqa: E402
import martian_corpus as mc  # noqa: E402
from client import Client  # noqa: E402

RESULT = HERE.parents[1] / "results" / "shape_context.json"
OUT = HERE.parents[1] / "results" / "shape_rejudge.json"
ARMS = ("PLAIN", "WITH_SHAPE")


def exact_p(b: int, c: int) -> float:
    """Two-sided exact binomial p for `b` vs `c` discordant pairs. 1.0 when there are none.

    Exact rather than the chi-square approximation because the discordant count here is small,
    and the approximation is unreliable below about 25 pairs.
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def main() -> int:
    mc._assert_intact()
    if not RESULT.exists():
        print(f"{RESULT} does not exist -- run shape_context.py first")
        return 1
    stored = json.loads(RESULT.read_text())
    arms = stored["arms"]
    client = Client("gemini-2.5-pro")

    pulls = [p for p in mc.pulls() if p.get("golden")]
    found: dict[str, dict[str, bool]] = {}
    repo_of: dict[str, str] = {}
    errors = 0

    for pull in pulls:
        key = str(pull["key"])
        # **`repo_file`, NOT THE URL HOST.** Two of sentry's ten changes point at
        # `ai-code-review-evaluation/sentry-greptile`, an evaluation mirror the corpus labels
        # `repo_file: sentry`. Grouping by URL splits one repository's defects across two clusters
        # and turns a five-repository corpus into six.
        repo = str(pull.get("repo_file") or "/".join(str(pull["original"]).split("/")[3:5]))
        golden = [str(g) for g in pull["golden"]]
        hits: dict[str, set[str]] = {}
        for arm in ARMS:
            texts = [str(t) for t in arms[arm].get(key, [])]
            got = judge.verdicts(client, golden, texts)
            hits[arm] = {str(g) for g in got["tp"]}
            errors += int(got.get("errors", 0) or 0)
        for i, g in enumerate(golden):
            defect = f"{key}#{i}"
            repo_of[defect] = repo
            found[defect] = {arm: (g in hits[arm]) for arm in ARMS}
        print(
            f"    {key[-34:]:>34}  plain {len(hits['PLAIN']):>2}  "
            f"shape {len(hits['WITH_SHAPE']):>2}  of {len(golden)}",
            flush=True,
        )

    both = sum(1 for v in found.values() if v["PLAIN"] and v["WITH_SHAPE"])
    b = sum(1 for v in found.values() if v["PLAIN"] and not v["WITH_SHAPE"])
    c = sum(1 for v in found.values() if v["WITH_SHAPE"] and not v["PLAIN"])
    neither = sum(1 for v in found.values() if not v["PLAIN"] and not v["WITH_SHAPE"])

    print(f"\n  defects: {len(found)}   judge errors: {errors}")
    print(f"  both found          {both}")
    print(f"  PLAIN only      (b) {b}")
    print(f"  WITH_SHAPE only (c) {c}")
    print(f"  neither             {neither}")
    print(f"\n  McNemar b:c = {b}:{c}   exact two-sided p = {exact_p(b, c):.4g}")
    print(f"  totals  PLAIN {both + b}   WITH_SHAPE {both + c}")

    print("\n  per repository (plain -> shape, of that repo's defects):")
    per: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0, 0])
    for defect, v in found.items():
        row = per[repo_of[defect]]
        row[0] += int(v["PLAIN"])
        row[1] += int(v["WITH_SHAPE"])
        row[2] += 1
    for repo, (p_, s_, total) in sorted(per.items()):
        print(f"    {repo:<42} {p_:>3} -> {s_:>3}   of {total}")

    OUT.write_text(
        json.dumps(
            {
                "found": found,
                "repo_of": repo_of,
                "both": both,
                "plain_only": b,
                "shape_only": c,
                "neither": neither,
                "exact_p": exact_p(b, c),
                "judge_errors": errors,
            },
            indent=1,
        )
    )
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
