# A47's stopping rule: every evaluation, including the ones that failed

**The rule was committed at `28d553c` BEFORE any pool was counted.** That commit timestamp
is the proof, in the same way the hand-labels' timestamp is the proof of blindness. This
file records every evaluation the rule called for — the eight failures as well as the pass
— because a stopping rule that reports only the evaluation that succeeded is
indistinguishable from one chosen after the fact.

**The rule.** Stop at the first repository index that is a multiple of ten at which both
unseen-reachable BROKE ≥ 30 and unseen-reachable CLEAN ≥ 30, or at repository 200,
whichever comes first.

- *reachable* = admitted, carrying a scan verdict, at most `MAX_PER_REPO = 3` per repository
- *unseen* = `pr_id` not among the 51 drawn across seeds 20260809–20260812
- evaluated from the journal only; **no draw was run and no key was opened**

## Every evaluation

| repos walked | raw BROKE | capped BROKE | **capped + unseen BROKE** | CLEAN | verdict |
|---|---|---|---|---|---|
| 20 | 10 | — | — | — | **NOT MET** (unmeetable on the total alone) |
| 30 | 12 | — | — | — | **NOT MET** (unmeetable on the total alone) |
| 40 | 19 | — | — | — | **NOT MET** (unmeetable on the total alone) |
| 50 | 20 | — | — | — | **NOT MET** (unmeetable on the total alone) |
| 60 | 33 | 25 | *(mapping not yet built)* | 47 | **NOT MET** — the cap alone took 8 BROKE back off |
| 70 | 42 | 31 | **19** | 44 | **NOT MET** |
| 80 | — | — | **19** | 47 | **NOT MET** |
| 90 | 48 | — | **22** | 63 | **NOT MET** |
| **100** | **56** | — | **30** | **71** | **MET** |
| 110 | — | — | 37 | 83 | (met; recorded for the record) |

At 20–50 the condition could not be met on the *total* admitted count, so no unseen or
per-repo filtering was needed to reach the verdict. From 60 the filters bind, and from 70
the `unseen` half became computable — `results/drawn_pr_ids.json`, built from the blind
sheets only.

## What the two filters cost, and why the rule counts them

At the moment the rule fired, raw BROKE was **56** and drawable BROKE was **30**. The
filters discard nearly half.

- **The cap.** `MAX_PER_REPO = 3` in the draw against `--per-repo 7` in the walk. At the
  60 mark this alone took a raw 33 down to 25 — 11 repositories over the cap and 17
  admitted rows structurally undrawable. This is A43's cap mismatch, reproducing live.
- **The unseen filter.** **32 of the 51 previously drawn PRs had already been re-walked**
  by repo 78. The walk re-covers ground three earlier draws already took.

Reading the raw count would have declared the rule met three evaluations early, at repo
60. That is precisely the error the specification was written to avoid.

**The filter is demonstrably live rather than vacuously true.** 32 hits means a zero would
have been a real zero and not a broken join — the distinction rule 14 exists for.

## What A47 does NOT say

A47 governs **draw feasibility only**. It does not say the corpus is finished, and its own
text makes reaching repository 200 an equally valid terminus. Whether to stop the walk at
the point the rule fires or to continue for a larger breakage-rate and arm-comparison
sample is a separate decision, and not one the rule makes.

## The margin is 3×, and landing exactly on 30 is why

The threshold was set at 30 rather than the 10 a bucket needs because a draw is not a
filter over the pool: `_shuffled_by_repo` shuffles repositories, clones them in order and
stops when the buckets fill, so it examines a fraction of the pool and loses whole
repositories to `CloneFailed` and every attempt inside them to `UNSCANNABLE`. The count
here is also an **over-estimate by construction** — the cap applies to *candidates* before
any scan, so admitted-capped-at-3 is a ceiling on what a draw can reach, not its size.

The pool cleared the threshold at exactly 30. The margin was written for that.
