# Widening the ranker to YAML costs nothing — and would manufacture the exposure it fixes

**Measured before the change, on the same six out-of-sample repositories the ranker was validated
on.** → `research/phase0/external/yaml_scope.py`

## The cost to the ranker is zero

| scope | events | ours miss | alphabetical | McNemar p |
|---|---|---|---|---|
| `.py` only, as it ships | 2,400 | **1.21%** | 3.12% | 1.5e-07 |
| `.py` + workflow YAML | 2,400 | **1.17%** | 3.21% | 2.3e-08 |

The source-only arm reproduces the published figure exactly, which is the known-answer check on
this harness.

**And the displacement risk did not materialise.** The worry was that workflows churn constantly,
accumulate fix-word commits, and would take top-three places from source files a later fix returns
to. Counted directly rather than inferred:

| | repaired source outside the top three | YAML in the top three |
|---|---|---|
| source only | 613/2400 = **25.5%** | 0 |
| with YAML | 610/2400 = **25.4%** | 57 = 2% |

**A repaired source file sits outside the top three a quarter of the time in BOTH arms** — that is a
property of three-file budgets, not of this change. The first version of this measurement reported
25.4% with no baseline beside it, which reads as a cost and is not one.

## So the answer is not "it costs too much". It is that the reason to do it is self-defeating

**The DETECTOR already runs on every workflow and needs no ranking.** It reads the diff and asks
GitHub; no model is involved. That was wired separately and fires regardless of what the ranker
ranks.

**Widening only makes the VERIFIER reachable** — the half that refutes a *model's* false SHA claim.
And the model can only make such a claim if it **reads** a workflow.

**Its measured discrimination on exactly that class is −8.3%** — it objected to 6 of 12 correct
pin/tag pairings and 5 of 12 wrong ones, and in 7 of 24 trials declared a SHA absent that had been
fetched from GitHub seconds earlier.

So widening would let the model read workflows on 2% of changes, invent SHA claims there at chance,
and spend an API call each to delete them. **It manufactures the exposure the oracle exists to
cover, and the net is a token bill.**

## Decision

**Do not widen `REVIEWABLE_SUFFIXES`.** Not because the ranker cannot afford it — it can, at no
measurable cost — but because the only thing it buys is the ability to clean up a mess that only
exists if you make it.

**What would change this:** evidence that the model finds something TRUE in workflows that is not a
SHA claim. Unmeasured, and it would need its own corpus. Recorded, not pursued.
