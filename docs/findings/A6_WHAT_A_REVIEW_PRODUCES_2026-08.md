# What a review actually produces — A6, first measurement

**Run 2026-08-28 on `pallets/flask`, 35 changes, the full pipeline with the model on.**
Bars were fixed in `docs/plans/product/product-build.md` before the run.

## Against the pre-registered bars

| bar | result | verdict |
|---|---|---|
| Coverage: 100% of reviewable changes receive a comment | 100%, by construction since A4 | **PASS** |
| Gate rejection strictly between 0% and 100% | **14.3%** of raw findings dropped | **PASS** |
| FULL vs FOCUSED split — reported, no bar | **77%** of flask changes touch ≤3 files | reported |
| Published findings per change — reported, no bar | **0.686** | reported |

```
CHANGES MEASURED   35   (the model failed on 0)
RAW FINDINGS        0.800 per change
KEPT FINDINGS       0.686 per change
GATE REJECTION      14.3%  — unanchored 3, refuted 1, withdrawn 0
COST                41,338 tokens in, 221,233 out, 2,108s
                    6,321 output tokens and 60 seconds per change
```

A first pass over 7 changes gave 0.714 raw and 0.571 kept, so the figures are stable across two
samples of very different size.

**Replicated 2026-08-28 on a third sample the pipeline had not seen** — 30 changes, commits 71–100
of the same repository — at **0.733 kept per measured change** against this run's 0.686. Pooled
two-proportion `z = 0.42`; the two are not distinguishable. See
`FINDINGS_PER_CHANGE_REPLICATED_2026-08.md`, which also retracts a claim made in the same session
that the rate was unstable — that comparison had divided by a different denominator.

## What this does NOT say

**0.686 is findings PUBLISHED, not findings CORRECT, and the two must not be compared.** The
0.013–0.037 figure in `AGENTS.md` is correctness-adjusted by blind raters. If the measured
66.7–82.1% wrong rate still held, 0.686 published would be roughly 0.12–0.23 correct per change —
several times the historical figure. **That error rate has not been re-measured on this pipeline**,
and until it is, the comparison is arithmetic on an assumption rather than a result.

**One repository, unreplicated.** This project has a rule about that, and it applies to its own
measurements: the retrospective run on the same clone refused its own verdict the same afternoon —
*"INCONCLUSIVE — 10 discordant pairs, floor is 20."* Thirty-five changes on one repository is a
first measurement, not a finding.

## The thing worth looking at next

**The oracle half of the gate is nearly inert here.** Of 28 findings, the anchor check dropped 3
and the oracles refuted 1; nothing was withdrawn. `verify/publishable.py` records the oracles
measuring −8.3% discrimination on a pinned set — a coin flip — and on this sample they barely fire
at all. The gate's 14.3% is almost entirely the parser confirming a quote exists in the diff.

That is worth knowing before D1c builds more on model-checked rules: the deterministic half of the
gate is doing nearly all of the filtering.

## Cost, for the first time

**6,321 output tokens and 60 seconds per change**, most of the output being the model's own
reasoning rather than its answer. Every pricing conversation before this one — BYOK, the free-tier
cap, whether the model half earns its keep — was arithmetic over a number nobody had measured.
It is measured now, on one repository, for changes of flask's size.
