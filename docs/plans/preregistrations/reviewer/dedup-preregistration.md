# Pre-registration — collapsing findings that say the same thing twice

**Registered 2026-08-30, before any dedup code was written and before any outcome was read.**

## The claim

We emit **194 comments covering 81 of 173 golden defects (0.42 per comment)**. Qodo-extended-v2
emits **152 covering 98 (0.64)**. The gap is not that we find less — it is that we say the same
defect repeatedly: **17.3% redundancy against Qodo's 1.0%**, measured in
`docs/product/reviewer/why-the-correct-rate-is-low.md`.

**The claim under test: a mechanical dedup removes repeats without removing coverage.**

This is worth registering because it is the one lever here that is model-free. Every mechanism
tried against the correctness rate has been a filter on generation and five moved nothing;
redundancy is an emission property and does not need the model to improve.

## What is NOT available, stated before it becomes an excuse

**Our own per-comment output for those 50 pull requests is not on disk.** `arm_OURS.json` holds
`tp/fp/fn/errors/prs_with_output` and nothing else, and no harness in the tree reproduces it.
So the 194/81/0.42 row **cannot currently be recomputed**, and dedup cannot be scored against it
without re-running our arm — 50 model calls at roughly 6,321 output tokens each.

That is a real limit on this work and it is why the bars below are split into what can be paid
for now and what cannot.

## The corpus, fixed now

`research/phase0/bench/martian/data/results/anthropic_claude-opus-4-5-20251101/candidates.json`
— **50 pull requests × 48 rival arms**, each comment carrying `path`, `line`, `source`, `text`.
Goldens in `research/phase0/bench/martian/data/golden_comments/`, 50 entries.

**The rule is developed against the RIVAL arms, never against ours.** Ours is unavailable anyway,
but the point stands independently: a rule tuned on the arm it must later judge is tuned on its
own test set.

## Bar 1 — the rule must reproduce a redundancy ordering already measured (free)

Qodo-extended-v2 was independently measured at **1.0% redundancy** and our arm at **17.3%**. A
dedup rule that fires on 15% of Qodo's comments is not detecting redundancy, it is detecting
something else and would delete real findings.

**PASS:** the rule removes **≤ 3.0%** of `qodo-extended-v2`'s comments.
**FAIL:** anything above that, and the rule is rejected rather than retuned on this arm.

This is a known-answer test: the answer is on record from a different method, so the rule can be
wrong in a way that shows.

## Bar 2 — coverage must not fall (requires model calls, NOT yet authorised)

Removing comments trivially reduces comment count. The claim is that it does not reduce **goldens
covered**, and only a judge can say which golden a comment covers.

**PASS:** on the arms tested, goldens covered after dedup equals goldens covered before, and
comments emitted falls.
**FAIL:** any drop in goldens covered. A rule that trades a covered defect for a shorter comment
list has made the product worse and is rejected outright — not tuned until it passes.

**Cost: one judge call per collapsed pair.** Until that is spent, **nothing ships to `render/`.**
A dedup merged on Bar 1 alone would be exactly the "we removed output and hope we lost nothing"
this project keeps finding in other people's evidence.

## What would make me drop this

- Bar 1 fails and the rule cannot be made conservative without removing nothing at all.
- Bar 2 fails on any arm.
- The rule removes fewer than **5%** of comments on any arm, which would make it not worth the
  code regardless of safety — the measured gap it is meant to close is 17.3%.

## What could still silently fail

Two comments about genuinely different defects on the same line would read as duplicates to any
text-similarity rule. Bar 2 is the only thing that would catch it, which is why Bar 1 alone is
not a licence to ship.

---

# Result — Bar 1 only, 2026-08-30

**BAR 1: PASS.** The rule removes **0.0%** of `qodo-extended-v2`'s 152 comments against a
registered ceiling of 3.0%. The ordering across arms is the one the independent measurement
implies:

| arm | removed | comments |
|---|---|---|
| graphite | 12.5% | 16 |
| greptile | 9.3% | 140 |
| copilot | 3.6% | 280 |
| coderabbit | 1.3% | 318 |
| greptile-v4-1 | 0.6% | 168 |
| qodo | 0.0% | 196 |
| **qodo-extended-v2** | **0.0%** | **152** |

**It is not passing by refusing to fire.** Loosening the threshold from 0.90 to 0.50 takes
greptile from 8.6% to 15.7% and copilot from 2.9% to 9.6% while `qodo-extended-v2` stays at or
below 1.3%. The rule discriminates between arms rather than tracking comment volume.

## What this result does NOT establish

**Whether it detects the phenomenon the 17.3% figure counted.** That number came from a different
method on our own arm; this rule matches near-verbatim prose about one file. "The same defect said
again in different words" is a semantic claim and a `SequenceMatcher` ratio is not. The two may
measure different things, and **our per-comment output is not on disk, so the two cannot be
compared.**

That is the honest state: the rule is safe on the arm whose low redundancy is independently known,
and its usefulness on ours is unmeasured.

## Bar 2 is unmet and nothing is wired

`verify/repeats.py` exists, is tested, and **is called by nothing.** Wiring it into `render/`
requires the coverage bar, which requires a judge — one call per collapsed pair — and the arm
regeneration that would produce pairs to judge: 50 model calls at roughly 6,321 output tokens.

**Not authorised, not spent, not merged into the review path.**


---

# Result — Bar 2 NOT RUN, and the rule is DROPPED by this document's own criterion, 2026-08-31

**No model calls were spent, and none should be.** The drop criterion registered above — *"the rule
removes fewer than 5% of comments on any arm"* — is met on every arm, measured on the judged
benchmark comments rather than estimated. → `scripts/measure/dedup_reach.py`

| arm | comments | repeats WITHIN a file (what the rule collapses) | same claim ACROSS files (kept) | semantic redundancy |
|---|---|---|---|---|
| OURS | 194 | **0** | 3 | 17 (17.3%) |
| qodo-extended-v2 | 152 | **0** | 0 | 1 (1.0%) |
| greptile-v4-1 | 168 | **0** | 1 | 7 (7.5%) |
| coderabbit | 318 | **0** | 5 | 34 (24.3%) |

The instrument reproduces the published 17.3% and 1.0% from `redundancy.json`, so it is reading the
same corpus those figures came from.

## The two measurements are different things, and that is now VERIFIED rather than open

This document recorded it as unknown: *"Whether it detects the phenomenon the 17.3% figure counted
... The two may measure different things."* They do.

**17.3% is `redundant / candidates_matching` — 17 comments matching a golden a SIBLING had already
covered.** That is semantic duplication: one defect described twice in different words, usually on
different files. **`repeats()` collapses near-verbatim prose about the SAME file**, and there are
**zero** such pairs in the corpus. The rule cannot reach the redundancy that justified building it.

Bar 2 asks whether coverage falls when comments are removed. **The rule removes no comments here,**
so coverage trivially cannot fall — and the judge calls would have bought a PASS that means nothing.
Spending them would have produced a green bar for a rule with no effect.

## What this does NOT say

**It does not say redundancy is not worth attacking.** 17 of our 98 matching comments restate a
golden a sibling already covered, against qodo's 1 of 99. That gap is real and remains the one
model-free lever with positive evidence. What is dead is *this* rule as the way to close it: any
mechanism that works has to compare claims across files and by meaning, not by shared prose within
one file.

## A defect found while measuring, fixed separately

`alike()` called `SequenceMatcher(None, a, b)`, whose `autojunk` default ignores any element
appearing in more than 1% of a sequence longer than 200 characters. Compared character by
character, that is ordinary letters and spaces. **Two real findings measured 97.3% alike scored
0.100.** Most review comments exceed 200 characters, so the rule was close to inert on real input
while all thirteen unit tests passed — every one compared strings short enough that the heuristic
never engaged.

**This also undermines the Bar 1 evidence.** Bar 1 passed on the reading that the rule fires
sensibly and discriminates between arms, and the check offered against "passing by refusing to
fire" was loosening the threshold. That check could not detect this: the threshold does not affect
whether long strings are compared at all. Bar 1's own table cannot be re-examined either — it names
arms (`graphite`, `copilot`) that appear in no results file here, and **the commit recording it
added no instrument**, which is why `scripts/measure/dedup_reach.py` now exists.
