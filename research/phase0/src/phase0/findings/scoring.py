"""Score a labelled findings pack against its sealed key. Run this last.

WHAT: `python -m phase0.score_findings --labels <csv> --key <csv>` prints the share of
      PUBLISHED findings a human judged correct, with a Wilson interval.
WHY:  Kept separate from drawing so the two are commands run in order, and so the labels
      exist before anything computes a number from them.

      **THE CONTROLS GATE THE RESULT AND THE GATE IS ARITHMETIC, NOT ADVICE.** If the
      planted items were not caught, the reading did not discriminate, and the findings
      rate is not a measurement of the findings -- so it is NOT COMPUTED. An earlier
      version printed the rate beneath a warning, which is how a number that was not
      evidence ends up quoted without its warning.

      **UNSURE SCORES AS DISAGREEMENT**, as `HAND_LABELLING_PROTOCOL.md` requires: not
      knowing is information and its honest cost is a point.

      What this measures is narrow and the printout says so: one repository, one language,
      findings from consecutive commits, no stratification. The interval covers sampling
      error alone. It is also an estimate of correctness AFTER the anchor gate and the
      refutation pass, which is a different quantity from the raw model error rate.
IMPORTS: stdlib only.
CONSUMED BY: an operator, by hand, after the labels are committed.
"""

from __future__ import annotations

import argparse
from pathlib import Path

VERDICTS = {"TRUE", "FALSE", "UNSURE"}
# Below this share of controls caught, the labelling did not discriminate and no rate is shown.
CONTROL_BAR = 0.8
Z = 1.96


def wilson(hits: int, n: int) -> tuple[float, float]:
    """Wilson score interval. The normal approximation is wrong at this n and near 1.0."""
    if n == 0:
        return (0.0, 1.0)
    p = hits / n
    mid = (p + Z * Z / (2 * n)) / (1 + Z * Z / n)
    half = Z * ((p * (1 - p) / n + Z * Z / (4 * n * n)) ** 0.5) / (1 + Z * Z / n)
    return (max(0.0, mid - half), min(1.0, mid + half))


def read_pairs(path: Path, header: bool) -> dict[str, str]:
    rows = [r for r in path.read_text().splitlines() if r.strip()]
    if header:
        rows = rows[1:]
    out: dict[str, str] = {}
    for row in rows:
        name, _, value = row.partition(",")
        out[name.strip()] = value.strip().upper()
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--key", type=Path, required=True)
    args = parser.parse_args()

    key = read_pairs(args.key, header=False)
    labels = read_pairs(args.labels, header=True)

    if set(key) != set(labels):
        print(f"labels cover {len(labels)} items, key has {len(key)} -- refusing to score")
        return 1
    blank = sorted(i for i, v in labels.items() if not v)
    if blank:
        print(f"unlabelled, refusing to score: {', '.join(blank)}")
        return 1
    bad = set(labels.values()) - VERDICTS
    if bad:
        print(f"not a verdict: {sorted(bad)}")
        return 1

    real = [i for i, arm in key.items() if arm == "REAL"]
    planted = [i for i, arm in key.items() if arm == "PLANTED"]
    caught = sum(labels[i] == "FALSE" for i in planted)
    correct = sum(labels[i] == "TRUE" for i in real)
    unsure = sum(v == "UNSURE" for v in labels.values())

    print(f"CONTROLS CAUGHT   {caught} of {len(planted)}")
    if caught < len(planted) * CONTROL_BAR:
        print()
        print("  A claim shown beside code it is not about was accepted, so the reading did")
        print("  not discriminate and the findings rate is not a measurement of the findings.")
        print("  IT IS WITHHELD -- not computed, not printed beneath a caveat.")
        print()
        print(f"  {len(planted) - caught} of {len(planted)} controls missed. Re-label, or find")
        print("  out why: a control that is genuinely true would be a defect in the pack.")
        return 2

    low, high = wilson(correct, len(real))
    print(f"FINDINGS CORRECT  {correct} of {len(real)}  = {correct / len(real):.1%}")
    print(f"UNSURE            {unsure} of {len(labels)}  (scored as disagreement)")
    print(f"95% INTERVAL      {low:.1%} to {high:.1%}  (Wilson, n={len(real)})")
    print()
    print("The rate at which a PUBLISHED finding is correct -- after the anchor gate and the")
    print("refutation pass, not the raw model error rate. One repository, one language,")
    print("consecutive commits, unstratified. The interval is sampling error alone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
