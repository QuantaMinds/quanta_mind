# The queue-level claim fails its pre-registered bar — 1.35× against 2.03×

**The sixth framing, and the last one that had not been tested.** Every other measurement in this
project is file-level; this one asks the question the surviving story rests on: *does the firing
gate concentrate the changes that later need repair?*

## Run one was void, and the reason is a pre-registration error

The first attempt used the shipped outcome — a fix-worded commit touching any file the change
touched, within ninety days. **That is true of 81.1% of changes.**

A pull request touches two to twelve files, and the chance that *any* of them sees a fix-worded
commit in ninety days is a union that approaches one in an active repository. **The file-level
outcome discriminates — that is the 1.21% against 3.12% — and at the change level it says almost
nothing.**

**The ceiling on the lift is 1 ÷ base rate = 1.23×, and the bar was set at 1.5×.** The test could
not pass. Recorded as an error in the bar, not a result: **the observed 1.18× was 96% of a ceiling
nobody checked.**

## Run two — the outcome tightened, the bar stated relative to its ceiling

A change counts as needing repair only when the later fix **touched lines the change touched**,
within thirty days. That is the actionability criterion, and it drops the base rate from 81.1% to
**32.7%**.

| | |
|---|---|
| base rate of a line-overlapping repair | **32.7%** |
| the gate fires on | **17.0%** |
| **ceiling on the lift** | **3.05×** — printed before the lift was read |
| **observed lift** | **1.35×** |
| **PASS needed** | **2.03×** (half the distance to the ceiling) |
| Fisher exact p | 3.1e-09 |

**FAIL.**

## Per repository, which is where a pooled number stops being safe

| repository | fires | repaired | caught | lift |
|---|---|---|---|---|
| scikit-learn | 12.2% | 49.0% | 18.4% | **1.51×** |
| django | 14.0% | 34.8% | 18.4% | 1.31× |
| pandas | 40.4% | 49.4% | 48.6% | 1.20× |
| celery | 19.2% | 14.8% | 21.6% | 1.13× |
| scrapy | 12.8% | 14.0% | 11.4% | **0.89×** |
| ansible | 3.6% | 34.4% | 2.9% | **0.81×** |

**Two of six are below 1.0 — the gate picks worse than a random draw there.**

## What 1.35× would actually buy, per 100 pull requests

- **33** will need a line-overlapping repair
- you can review **17** of them
- a random 17 catches **5.6** of the repairs
- the gate catches **7.5**

**+2.0 repairs caught for the same review budget.** Real — p = 3.1e-09 — and small, and negative in
a third of the repositories tested.

## What this closes

**The stopping rule was agreed before the run:** if the PR-level test fails and the incident link
fails, the honest conclusion is that the signal is real and inert rather than that a seventh
framing is waiting.

**The PR-level test has failed.** The incident link is untested and needs a customer's data — it is
the one remaining question, and it is no longer one public data can answer.

**What is NOT closed by this.** The ranker itself is untouched: 1.21% against 3.12%, reproduced
twice this week from independent reimplementations. **What failed is the sixth attempt to turn that
into something someone buys**, not the measurement it rests on.
