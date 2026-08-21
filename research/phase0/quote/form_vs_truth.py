"""Does a finding's FORM predict whether it is TRUE? Zero model calls, and the answer is no.

WHAT: Joins every adjudicated finding that still has its text to its blind verdict, classifies each
      on six surface features, and cross-tabulates against WRONG and CORRECT.
WHY:  **NOTHING IN THIS PROJECT HAD EVER MEASURED FORM.** Every number is about truth — is the claim
      correct, does it point at the right line, can a parser confirm it. Whether a finding is one
      line or six, concrete or hedged, names a fix or waves at a problem, was never looked at.

      **HEDGING IS NOT A FILTER: 59.3% wrong against 58.4%, Fisher p = 1.0000.** A perfect null on
      the headline feature at n = 152 across two designs and two corpora.

      **AND THE INVERSION IS THE USEFUL PART. `definite wording` is the WORST of the confident forms
      at 66.7% wrong.** That is the mechanism behind this project's most memorable failures, now
      measured rather than anecdotal: *"Version 1.45.34 of awscli does not exist on PyPI"* is one
      line, specific, unhedged, and false. Someone will eventually propose publishing only the
      confident findings. This is the answer.

      **THE CORRECT-RATE IS THE SENTENCE THAT CLOSES IT: 3.7% to 12.0% across every form.** Even the
      best-formed slice tops out at one in eight, and unlike a wrong-rate that is a number no
      deletion can improve — the same argument that killed design fourteen's exclusion.

      This is the third attempt to find truth in the surface of the text, beside the anchor repairs
      and the lexical marker. The corpus study concluded review content is not keyword-shaped; this
      concludes findings are not form-shaped either. **The schema remains the only lever, because it
      does not reward good form — it makes bad form inexpressible.**
IMPORTS: stdlib only.
CONSUMED BY: nobody — it prints.
"""

import collections
import json
import math
import pathlib
import re

# Repo-relative, so it runs from anywhere rather than only from the project root.
R = pathlib.Path(__file__).resolve().parent.parent
rows = []  # (text, verdict)

# Design 1's adjudicated pool: claim text and verdict in one file.
d1 = json.loads((R / "results/adjudication_verdicts.json").read_text())
for v in d1.values():
    rows.append((str(v.get("claim", "")), str(v.get("verdict", "")).upper()))

# Design 13: the key has no arm_idx — it identifies a finding by (repo, pr, path, line).
run = json.loads((R / "quote/results/quote13_run.json").read_text())
key = {str(e["item"]): e for e in json.loads((R / "quote/adj13/KEY_DO_NOT_OPEN.json").read_text())}
ver = json.loads((R / "quote/adj13/verdicts.json").read_text())
by_site = {}
for r in run["results"]:
    for a in "ABC":
        for f in r["published"].get(a) or []:
            by_site.setdefault((f["repo"], f["pr"], f["path"], f["line"]), str(f.get("claim", "")))
hit = 0
for i_, text in ver.items():
    e = key.get(i_)
    if not e or e.get("kind") != "real":
        continue
    claim = by_site.get((e["repo"], e["pr"], e["path"], e["line"]))
    if not claim:
        continue
    hit += 1
    rows.append((claim, text.split()[0].upper()))
print(f"  design 13 joined: {hit}")

rows = [
    (t, v) for t, v in rows if t.strip() and v in ("CORRECT", "WRONG", "UNFALSIFIABLE", "TRIVIAL")
]
print(f"  {len(rows)} findings with BOTH text and a blind verdict")
print(f"  {collections.Counter(v for _, v in rows).most_common()}\n")

HEDGE = re.compile(
    r"\b(may|might|could|possibly|potential(?:ly)?|likely|consider|seems?|appears?|"
    r"suggest|probably|risk of)\b",
    re.I,
)
DEFINITE = re.compile(
    r"\b(will|does not|is not|cannot|never|always|incorrect|missing|"
    r"undefined|null)\b",
    re.I,
)
CODE = re.compile(r"`[^`]+`|\b\w+\(\)|\b[a-z]+_[a-z_]+\b|\b[A-Z][a-z]+[A-Z]\w*\b")
FIX = re.compile(r"\b(should|instead|replace|use \w+|add a|remove|change .* to)\b", re.I)


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


def fisher(a, b, c, d):
    C = math.comb
    n = a + b + c + d
    obs = C(a + b, a) * C(c + d, c) / C(n, a + c)
    p = 0.0
    for x in range(0, min(a + b, a + c) + 1):
        y, z_, w = a + b - x, a + c - x, n - x - (a + b - x) - (a + c - x)
        if y < 0 or z_ < 0 or w < 0:
            continue
        pr = C(a + b, x) * C(c + d, z_) / C(n, a + c)
        if pr <= obs + 1e-12:
            p += pr
    return min(p, 1.0)


feats = {
    "hedged": lambda t: bool(HEDGE.search(t)),
    "definite wording": lambda t: bool(DEFINITE.search(t)) and not HEDGE.search(t),
    "has a code token": lambda t: bool(CODE.search(t)),
    "names a fix": lambda t: bool(FIX.search(t)),
    "short (<= 20 words)": lambda t: len(t.split()) <= 20,
    "long (> 40 words)": lambda t: len(t.split()) > 40,
}
print(f"  {'form feature':<22}{'n':>5}{'WRONG rate':>12}{'  vs rest':>11}{'Fisher p':>10}")
base_w = sum(1 for _, v in rows if v == "WRONG") / len(rows)
print(f"  {'(all findings)':<22}{len(rows):>5}{base_w:>12.1%}\n")
for name, fn in feats.items():
    yes = [(t, v) for t, v in rows if fn(t)]
    no = [(t, v) for t, v in rows if not fn(t)]
    if not yes or not no:
        continue
    wy = sum(1 for _, v in yes if v == "WRONG")
    wn = sum(1 for _, v in no if v == "WRONG")
    p = fisher(wy, len(yes) - wy, wn, len(no) - wn)
    print(f"  {name:<22}{len(yes):>5}{wy / len(yes):>12.1%}{wn / len(no):>11.1%}{p:>10.4f}")
print("\n  CORRECT-rate by the same features:")
for name, fn in feats.items():
    yes = [(t, v) for t, v in rows if fn(t)]
    if not yes:
        continue
    c = sum(1 for _, v in yes if v == "CORRECT")
    print(f"    {name:<22}{c:>3}/{len(yes):<4} = {c / len(yes):>5.1%}")
