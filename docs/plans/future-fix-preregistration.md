# Pre-registration — score the reviewer against the future, not against a rubric

**Written before the corpus is fetched.** Every measurement so far asked a rater *"is this claim
true of the code shown?"*. This asks git: **did a fix come back to this code?**

## Why this instrument is better than the six that came before

**No adjudication.** The outcome is a commit, not a judgement. No rubric to argue about, no rater
pool, no κ, no author grading their own prompt.

**And it asks the question the product actually sells.** A reviewer that points at code which later
breaks is useful even if its sentences are wrong. A reviewer whose sentences are true about code
that never breaks is not. **Six designs measured truth. None measured usefulness.**

## The measurement

For every unit the allocator funds on a pre-2022 pull request:

| recorded | |
|---|---|
| **spoke** | the model emitted ≥ 1 finding |
| **confused** | any snippet CRASHED, was REFUTED, or printed nothing |
| **outcome** | a fix-word commit touched that file within 90 days of the merge |

`corpus_age.assert_corpus_age` enforces the window at fetch time.

## The bar, and it is not zero

**The ranker already selects these units, and on the first 40 it hit 32.5%.** Any signal from the
model must beat **32.5%**, not beat chance. A model-derived signal that matches the ranker is a
model-derived signal worth deleting, because the ranker is free.

| reading | rule |
|---|---|
| **CONFIRMED** | a model signal reaches ≥ 45% against the ranker's base, Fisher p < 0.05 |
| **NULL** | within 5 points of the base, or p ≥ 0.05 |
| **UNDERPOWERED** | fewer than 20 units carrying the signal — report and do not interpret |

## Power, computed before the run

Confusion fired on 7 of 40 units — **17.5%**. Detecting a 45% rate against a 32.5% base needs
about **80 confused units**, which needs roughly **460 funded units ≈ 150 aged pull requests**.
Forty confused units detects 50%. **Twenty detects only 60%**, which is the floor this run targets
and the reason the underpowered branch is written down.

## What each outcome means

**CONFIRMED** — the model is useful as a *confusion detector* rather than a reviewer: where it
flails is where defects live, and the output to publish is the flag, never the prose. That is a
genuinely different product and a defensible one.

**NULL** — the model contributes nothing to locating defects, on top of a ranker that already does
it for free. Combined with 65.2% of its claims being wrong, **the review half has no remaining
justification of any kind** and the question is closed on outcome data rather than on rater
opinion.

## Stated so it cannot be reinterpreted afterwards

**A positive result here does NOT rescue the findings.** It would mean the model's *distress* is
informative, not its claims. Publishing the claims would remain forbidden by everything already
measured.
