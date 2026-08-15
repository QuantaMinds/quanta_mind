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


---

# RESULT — the gate selects code that does **not** break. Significant, and inverted.

**165 aged pull requests, 278 requests, 229 findings, 275 funded units scored against git.** No
raters. The outcome is a commit.

**The ranker's own hit rate on these units: 50.5%.** Every model signal is measured against that,
not against chance.

| signal | units | fix returned | vs ranker | p |
|---|---|---|---|---|
| the model spoke | 217 | 49.3% | −1.2 | 0.462 |
| a snippet showed **confusion** | 40 | **57.5%** | **+7.0** | 0.394 |
| a snippet **CONFIRMED** | 85 | **36.5%** | **−14.1** | **0.003** |
| emitted ≥ 2 findings | 9 | 44.4% | −6.1 | 0.748 |

## The significant result is the one nobody wanted

**When the model successfully demonstrates its claim, the code is significantly LESS likely to have
a fix return to it.** −14.1 points, p = 0.003, surviving Bonferroni at five comparisons (α = 0.01).

**And it is not function length in disguise.** Median unit length is 12 lines for CONFIRMED against
13 for the rest. Controlling for length makes it *stronger*:

| length band | CONFIRMED | not confirmed | p |
|---|---|---|---|
| **≤15 lines** | 50 units, **24.0%** | 111 units, **51.4%** | **0.001** |
| 16–40 | 26 units, 42.3% | 52 units, 57.7% | 0.235 |
| >40 | 9 units, 88.9% | 27 units, 77.8% | 0.652 |

## What it means, and it is the sharpest thing this investigation produced

**The execution gate — built to raise precision — actively selects away from defects.** The model
can construct a working demonstration when the code is simple enough to reason about in isolation,
and code simple enough to reason about in isolation is code that does not break. **Demonstrability
and defectiveness are anti-correlated.**

That also explains the earlier result that the gate raised TRIVIAL from 7.7% to 28.6%. It was not a
side effect. **It is the same fact measured two ways**: the gate finds claims that are easy to
prove, and easy-to-prove claims are about code where nothing is wrong.

## The inversion the data supports, and the one it does not

**Supported and significant**: model *succeeds* → code is stable.

**Directional only**: model *confused* → code more likely to break, 57.5% against 50.5%, **+7.0
points, p = 0.394 on 40 units. That is not evidence.** The pre-registration set the underpowered
floor at 20 units and this clears it, but it does not clear the significance bar and must not be
reported as if it did.

## What this closes and what it opens

**Closes:** the execution gate is not a fix, it is a defect *avoider*. Any future design that gates
on demonstrability inherits this. It should be recorded next to the gate itself.

**Opens, as a hypothesis and not a finding:** the model's distress may be a locating signal where
its claims are not. To test it needs roughly 80 confused units against a 50.5% base — about three
times this corpus — and it must beat the ranker, which is free.

**Does not change:** the review half stops. Nothing here rescues a claim; the significant result is
that the reviewer's confident output points at stable code.
