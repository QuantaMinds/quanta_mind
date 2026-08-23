# Fixes recorded rather than built

Four measured improvements to the reviewer half, each with an effect size, each not built. They
share one reason and it is not cost: **the reviewer half is closed.** Half B failed on 0 of 45 —
the parser can refute none of the wrong findings — and the optimistic case still misses the field
floor by 37 points. A component of something that does not ship is not worth building, however
sound the measurement behind it.

They are recorded because the arithmetic is real and re-deriving it later would cost more than
writing it down. **If the reviewer half is ever reopened, start here, in this order.**

| fix | measured worth | evidence |
|---|---|---|
| deduplication | +4.0 points golden-level precision, 18% of the gap to Qodo | `research/phase0/bench/forensic/redundancy.py` |
| live registry lookup | addresses 51% of wrong findings | `docs/product/reviewer/external-evidence-2026-08.md` |
| date injection | addresses 11% of wrong findings | `docs/product/reviewer/external-evidence-2026-08.md` |
| per-category thresholds | not sized; category rates differ 0%–45% | `docs/product/reviewer/greptile-gap-analysis.md` |

## Deduplication — the arithmetic

All four arms judged in one pass over the same 50 pull requests and 173 goldens:

| arm | comments emitted | matched something | goldens covered | redundant | rate |
|---|---|---|---|---|---|
| qodo-extended-v2 | 152 | 99 | **98** | +1 | **1.0%** |
| greptile-v4-1 | 168 | 93 | 86 | +7 | 7.5% |
| **OURS** | **194** | **98** | **81** | **+17** | **17.3%** |
| coderabbit | 318 | 140 | 106 | +34 | 24.3% |

Our 98 matching comments and Qodo's 99 are the same number. **They are not the same coverage** —
theirs land on 98 distinct defects, ours on 81. The rate orders all four arms exactly as their
published quality does.

Golden-level precision is covered ÷ emitted. Removing all 17 redundant comments, changing nothing
else:

- ours today: 81/194 = **41.8%**
- ours deduplicated: 81/177 = **45.8%** — **+4.0 points**, above the 2.1-point judge noise floor
- qodo: 98/152 = **64.5%**

**That is 18% of the 22.7-point gap.** The other 18.7 points is that Qodo emits 53 comments
matching nothing where we emit 96. Closing that means deleting about 43 more wrong comments, and
the generator cannot pick which — it retains **8.5–16.8%** of the available discrimination over its
own output. → `docs/plans/preregistrations/reviewer/prompt-direction-preregistration.md`

## Why none of these reopens the question

Deduplication moves a benchmark precision number. **It does not create a correct finding**, and the
closure was never about precision — it was that the parser cannot refute the wrong findings and the
ceiling misses the field floor by 37 points. A fix that improves the ratio without adding a true
finding leaves both of those exactly where they were.

This is the fifth measurement since the closure that confirms it rather than challenges it.
