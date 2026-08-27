# Every arm runs its control twice — because one run is a sample of size one

**Branch:** `feat/replicated-arms`. **Status: PLAN. The variance estimate below is from three
samples and its out-of-sample test has NOT been run** — it is blocked on `gcloud auth login`. Every
number here is marked with which of those it is.

## The finding this exists to answer

The reviewer's output is not reproducible, at `temperature: 0.0`, and the score is computed from
the output.

| | |
|---|---|
| PLAIN generated three times | **81, 91, 84** — sd **5.13 defects (3.0 points)**, range 10 |
| the same comments re-judged | 81 → **81** — judging moved it **zero** |
| changes where two runs agree exactly on comment count | **29 of 50 (58%)** |
| comments with a counterpart in the other run, loosest matching | **75%** |
| comment TOTALS across those runs | 221 vs 224 — **1.4% apart** |

**The totals are stable and the composition is not.** That is why the shape arm's volume bar looked
healthy through every bucket: 221-against-224 numbers read as a well-behaved arm while a quarter of
the comments turned over.

**It is not concentrated in a few bad changes.** 21 of 50 disagree, spread thin — 13 by one comment,
3 by two, 4 by three, 1 by four. There is nothing to exclude.

**And it is not a settings mistake.** `bench_reviewer.py:143` already sets `temperature: 0.0`. What
remains is serving nondeterminism — batching, routing, floating-point non-associativity — and no
client-side setting removes it.

## What that costs, in power

To resolve a 6-defect effect at 80% power and α = 0.05, given sd ≈ 5.13 defects per run:

| route | cost |
|---|---|
| **repeated paired runs** | **6 runs** if arms correlate at r = 0.5 (same pull requests), **12** if independent |
| single run, bigger corpus | sd must fall to ≈ 2.1 defects — about **6× the corpus, ≈ 993 hand-verified defects** against 173 today |

**The corpus route is not available.** Those 173 defects are human-verified; sixfold is a labelling
programme. **Replication is roughly two orders of magnitude cheaper** and is the lever nobody pulled.

## The change

**Every arm runs its control at least twice and publishes the gap**, in the pre-registration and in
the result. `research/phase0/bench/forensic/shape/replicate.py` is the pattern and already exists.

**The bar is set against the measured floor, not the judge's replicate spread.** The 2.1-point
figure came from re-scoring identical candidates — `prompt-direction-preregistration.md` derived it
and correctly concluded *"the judge is stable"*. That conclusion is true and was then used as the
noise floor for comparing ARMS, which needs generation stability too. **The judge being stable is
not the reviewer being stable, and the difference is the whole error.**

→ `docs/plans/preregistrations/TEMPLATE.md` gains the requirement; `corpus-noise-floor.md` carries
the number.

## What to test, in order

1. **Verify the variance estimate out of sample.** sd = 5.13 is from three points. Two further
   PLAIN runs should land in **[75, 95]** (±2 sd of 85.3). **PRE-REGISTERED HERE, NOT YET RUN** —
   blocked on auth. If either falls outside, the estimate is too small and the 6-run figure is
   optimistic.
2. **Re-derive deduplication's +4.0 across two runs.** It is the largest deferred fix and sits
   exactly on the floor; its duplicate count comes from one run whose composition is now known to
   be unstable. The arms are already stored, so this costs a judge pass, not a review pass.
3. **Only then consider re-running shape at n = 6.** It is the cheapest real test of a mechanism
   that is wired, free, and undemonstrated — but it is third, because the two checks above cost
   almost nothing and change what the answer would mean.

## The fix that is not available, and why it is worth stating

**Averaging cannot be replaced by a better prompt, a better judge, or a bigger model.** The variance
is in the generator's sampling, and the score is a function of what it sampled. A different-family
judge — the thing this project has argued for and never run — addresses whether findings are
*correct*, not whether they *recur*. **These are different problems and the judge does not touch
this one.**

## What could still silently fail

**sd from three samples is itself uncertain.** With n = 3 the 95% interval on a standard deviation
is roughly half to three times the estimate, so "6 runs" could honestly be 3 or 20. Test 1 exists to
narrow that and does not eliminate it.

**Variance may not be constant across arms.** A prompt that makes the model terser may also make it
more repeatable. Each arm's own control is therefore the right comparator — which the requirement
above already produces, but only if the control is run alongside, not reused from a previous study.
