# Findings per change, replicated — and a retraction

**Run 2026-08-28 on `pallets/flask`, 30 changes, commits 71–100 of `git log --no-merges -- '*.py'`
— a slice neither A6 nor any other sample here touched.** Harness:
`research/phase0/bench/rate/measure.py`. Records: `research/phase0/results/findings_rate_flask_skip70.json`.

## The result

```
COMMITS ATTEMPTED  30      measured 30, nothing skipped
RAW FINDINGS       27
KEPT FINDINGS      22      = 0.733 per measured change
GATE REJECTION     18.5%   — unanchored 5, refuted 0, withdrawn 0
```

| | A6 | this slice |
|---|---|---|
| changes measured | 35 | 30 |
| kept per change | **0.686** | **0.733** |
| 95% interval | 0.520–0.814 | 0.556–0.858 |
| gate rejection | 14.3% | 18.5% |

**The two are not distinguishable.** Pooled two-proportion `z = 0.42`, against 1.96. The intervals
overlap across almost their whole length. A6's line — *"the figures are stable across two samples
of very different size"* — now holds across three.

## The retraction

**Earlier in this session I reported that findings-per-change came out at 0.686, 0.46 and ~0.25
on the same repository and pipeline, and concluded the rate was "one draw rather than a constant".
That was wrong, and it was wrong in a way this project has a rule about.**

A6 divides by *changes measured* — commits where the model was actually asked something. The 0.46
and 0.25 divided by *every commit in a log slice*, including commits skipped before inference ever
ran. Two rates over two denominators are not evidence of instability; they are a broken
comparison. The fixture in `bench/rate/record.py` shows the size of the error directly: the same
six findings read as **1.500, 1.000 or 0.600** depending only on which denominator is chosen.

Measured properly on A6's own denominator, the answer is 0.733 against 0.686.

**A second thing worth recording: the partial reads of this very run were misleading.** At 22 of
30 commits it stood at 0.500 and looked like it was confirming the instability story. The last
eight commits carried it to 0.733. A rate read before its sample is complete is not a smaller
version of the answer.

## What this does and does not say

**It replicates the rate, not the correctness.** 0.733 is findings *published*, and how many are
*right* is still unmeasured on this pipeline — the labelling pack in
`research/phase0/data/labelling/` exists for that and is unlabelled. Everything A6 says under
"What this does NOT say" applies here unchanged.

**One repository, one language, three samples.** All three are `pallets/flask`. Replication across
samples of the same repository is a weaker claim than replication across repositories, and the
ranking half's own result required six repositories the method had never seen.

**The gate is still almost entirely the anchor check.** 5 unanchored, 0 refuted, 0 withdrawn: the
oracles fired on nothing at all here, against 1 refutation in A6. `verify/publishable.py` records
them measuring −8.3% discrimination on a pinned set, and across 65 changes over two runs they have
now dropped exactly one finding. **A gate whose second and third stages have never fired is a
one-stage gate**, and describing it as three would be describing a capability the system does not
demonstrate.
