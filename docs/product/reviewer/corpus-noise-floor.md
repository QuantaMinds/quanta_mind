# The 50-change benchmark has a ±4-point noise floor, and it was never measured until now

**Measured 2026-08-26. Two runs of the SAME arm, no context on either side, differing only in the
model's own nondeterminism:**

```
PLAIN_A    91 of 173 defects, 221 comments
PLAIN_B    84 of 173 defects, 224 comments

gap: 7 defects — 4.0 points — from nothing at all
```

→ `research/phase0/bench/forensic/shape/replicate.py`, result in `results/shape_replicate.json`.

## Why this matters to every result scored on this corpus

**Any arm measured here against a bar under roughly 4 points can be passed by noise.** The
shape-context arm was: it cleared `> +2.1 points` on its first judging with **+5.2**, and the floor
is 4.0. → `shape-context-result.md`, now NULL.

**The 2.1-point figure was the judge's replicate spread — re-scoring the same outputs.** That is one
term of the noise and the smaller one. The larger term is generation: **the reviewer is stochastic,
so two identical runs do not produce the same comments**, and defects found is computed from the
comments. Bars written against the judging term alone sit below the noise they exist to exclude.

## Where the variance comes from, per change

46 changes reviewed twice under identical conditions:

| | |
|---|---|
| mean disagreement | **0.76 comments** per change |
| largest | **4** comments on one change |
| direction | run A higher on 10, run B higher on 11, equal on 25 |

One `getsentry/sentry` change drew **2 comments in one run and 6 in the other**. Aggregate volume
barely moved — 221 against 224 — so **a stable total hides an unstable composition**. Reporting
comment counts as evidence of stability is a mistake this document exists to prevent.

## What this does and does not invalidate

**It does not touch the ranker.** The claim this company rests on — top-three-by-fix-history missing
1.21% against alphabetical's 3.12%, n = 2,400, McNemar b = 62 / c = 16, p < 1e-6, 6 of 6
repositories — is a different corpus, a different method, and model-free. Nothing here reaches it.

**It does apply to reviewer arms scored on the 50-change golden set**, whatever their recorded
status. An arm whose effect is smaller than ~4 points has not been shown to do anything, and several
were recorded before this floor was known. The affected documents carry a pointer to this file:
`greptile-gap-analysis.md`, `why-their-f1-is-higher.md`, `why-the-correct-rate-is-low.md`,
`pipeline-vs-competitors.md`, `review-half-record.md`.

**Large effects survive.** A 22.7-point precision gap or a 54.6-point move in a failure class is far
outside this floor. The rule is proportion, not blanket doubt: **compare the effect to 4 points
before believing it.**

## What every future arm on this corpus must do

- **Run the control twice and publish the gap** alongside the result. One run is a sample of size
  one from a distribution nobody has characterised.
- **Set the bar above the measured floor**, not above the judge's replicate spread.
- **Report the paired statistic and the per-repository split**, per
  `docs/plans/preregistrations/TEMPLATE.md`.

## What would fix the corpus rather than work around it

Fifty changes and 173 defects is too small to resolve the effects this project cares about. Detecting
a 3-point effect against a 4-point floor needs several times the defects, or averaging over repeated
runs, or both. **That is a sample-size problem and no prompt will solve it.**

**The honest position: this benchmark can compare things that differ a lot, and cannot adjudicate
things that differ a little.** Most of what the reviewer half has been testing differs a little.
