"""Bot prevalence in the review corpus, and the recency comparison on humans only.

WHAT: Prints what share of each repository's inline review comments is bot-written, then
      recomputes the structural share under both sampling schemes with bots excluded, per
      repository, with a two-proportion test and a sign test across repositories.
WHY:  It answers the sampling objection with data rather than agreement. The classifier is
      weak and known to be, but it is held IDENTICAL across the two draws, so it cannot
      manufacture a difference between them -- any shift is attributable to the sampling.
      Per-repository rather than pooled because the two draws have different repository
      mixes, and a pooled comparison would confound mix with scheme invisibly.
IMPORTS: stdlib only (json, re, collections, math).
CONSUMED BY: nobody -- it prints. Reads `review_both.json` from `fetch.py`.
"""

from __future__ import annotations

import collections
import json
import re
from math import comb, erfc

with open("review_both.json") as _fh:
    R = json.load(_fh)
NOT_FINDING = re.compile(
    r"^\s*(lgtm|nit\b|ok\b|okay|thanks|thank you|done|\+1|yes|no\b|sure|agreed|good catch"
    r"|nice|sounds good|fixed|ack)\b|^\s*(what|why|how|should we|could we|can we|do we|is "
    r"this|are these|does this|any reason|wdyt|thoughts)\b|\?\s*$",
    re.IGNORECASE,
)
STRUCTURAL = re.compile(
    r"\b(line \d+|missing import|not imported|undefined|not defined|typo|rename|misspel"
    r"|signature|argument order|wrong (?:name|type|argument)|does not exist|doesn'?t exist"
    r"|unused (?:import|variable)|shadow|duplicate)\b|`[A-Za-z_][\w.]*`\s+(?:is|does|"
    r"should|must)\b",
    re.IGNORECASE,
)


def structural(b):
    t = " ".join(b.split())
    if len(t) < 15 or NOT_FINDING.search(t):
        return None  # asserts nothing
    return bool(STRUCTURAL.search(t))


def z2p(x1, n1, x2, n2):
    if not n1 or not n2:
        return 1.0
    p = (x1 + x2) / (n1 + n2)
    se = (p * (1 - p) * (1 / n1 + 1 / n2)) ** 0.5
    return 1.0 if se == 0 else erfc(abs(x1 / n1 - x2 / n2) / se / 2**0.5)


print("  === BOT PREVALENCE IN OSS INLINE REVIEW COMMENTS ===")
print("  (uniform draw across full history; a repo's bots are not evenly spread in time)")
print(f"  {'repo':32s} {'n':>6} {'bot':>6} {'share':>7}   top bot authors")
tb = tn = 0
for repo in sorted({r["repo"] for r in R}):
    rs = [r for r in R if r["repo"] == repo]
    b = [r for r in rs if r["is_bot"]]
    tb += len(b)
    tn += len(rs)
    who = collections.Counter(r["login"] for r in b).most_common(2)
    print(
        f"  {repo:32s} {len(rs):6d} {len(b):6d} {len(b) / len(rs):6.1%}   "
        + ", ".join(f"{w}({c})" for w, c in who)
    )
print(f"  {'ALL':32s} {tn:6d} {tb:6d} {tb / tn:6.1%}")

print("\n  === RECENCY BIAS, HUMAN COMMENTS ONLY ===")
print("  structural share of comments that assert something")
print(f"  {'repo':32s} {'recent':>15} {'uniform':>15} {'shift':>9} {'p':>8}")
shifts = []
for repo in sorted({r["repo"] for r in R}):
    cell = {}
    for sch in ("recent", "uniform"):
        v = [
            structural(r["body"])
            for r in R
            if r["repo"] == repo and r["scheme"] == sch and not r["is_bot"]
        ]
        v = [x for x in v if x is not None]
        cell[sch] = (sum(v), len(v))
    (s1, n1), (s2, n2) = cell["recent"], cell["uniform"]
    if not n1 or not n2:
        print(f"  {repo:32s}  insufficient human comments")
        continue
    shifts.append(s2 / n2 - s1 / n1)
    print(
        f"  {repo:32s} {s1:3d}/{n1:3d}={s1 / n1:5.1%} {s2:3d}/{n2:3d}={s2 / n2:5.1%} "
        f"{(s2 / n2 - s1 / n1) * 100:+8.1f}pt {z2p(s1, n1, s2, n2):8.4f}"
    )

pos, n = sum(1 for s in shifts if s > 0), len(shifts)
p = min(1.0, 2 * sum(comb(n, i) for i in range(min(pos, n - pos) + 1)) / 2**n)
print(f"\n  sign test: {pos} up, {n - pos} down of {n}  p={p:.4f}")
print(
    f"  mean |shift| = {sum(abs(s) for s in shifts) / n * 100:.1f} points   "
    f"max |shift| = {max(abs(s) for s in shifts) * 100:.1f} points"
)

hum = [structural(r["body"]) for r in R if not r["is_bot"]]
hum = [x for x in hum if x is not None]
bot = [structural(r["body"]) for r in R if r["is_bot"]]
bot = [x for x in bot if x is not None]
print("\n  === WHY THE CONTAMINATION MATTERED ===")
print(
    f"  human comments that assert : {sum(hum)}/{len(hum)} = {sum(hum) / len(hum):.1%} structural"
)
print(
    f"  bot   comments that assert : {sum(bot)}/{len(bot)} = {sum(bot) / len(bot):.1%} structural"
)
