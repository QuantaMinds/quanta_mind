# What fraction of useful findings survive the forced schema

**Written before the run. Bars fixed here.**

`docs/product/evidence-ledger.md` states the open question in these words:

> stage four does not try to detect structure in prose — it adjudicates the fields **the schema
> forces** (`claim_type`, `file`, `line_a`, `line_b`, `relation`), which makes every finding
> checkable by construction. The open question is no longer *what fraction of review claims are
> checkable* but **what fraction of useful findings survive that form without distortion** —
> answerable from the worked example before any model runs, and not yet answered.

**This answers it, and it decides whether a mechanically-verified reviewer is possible at all.**
Every one of the fourteen prior attempts asked a model whether another model was right. This asks
whether a *parser* could, which is a different kind of mechanism and the only one not yet tried.

## The corpus, and why it is not ours

**Martian's 173 golden comments across 50 pull requests.** They are written by humans and verified
by the benchmark's own process. **"Useful" is therefore defined by someone other than us**, which is
the property our own 12 correct findings do not have — those were graded by a rater using a rubric
we wrote.

## The definition, fixed before anything is classified

A finding **SURVIVES** the schema if all three hold:

1. **It names a location** — a line, a call, an identifier in the changed code.
2. **Its truth rests on a relation** — between that location and another specific location, or
   between that location and a structural property of the code around it.
3. **A parser could confirm or refute that relation without judgement.** Syntactic or structural,
   not semantic. *"`forEach` is passed an `async` callback and does not await it"* survives.
   *"this naming is inconsistent"* does not.

**Rule 3 is the binding one and it is deliberately strict.** The entire value of the schema is that
`verify/` can adjudicate mechanically. A finding a parser cannot settle is one a model would have to,
which returns us to the fourteen failures.

## The bars

| survival rate | reading |
|---|---|
| **≥ 50%** | **The schema is the product.** Mechanically-verified review at competitive volume — 173 goldens over 50 pull requests is 3.46 useful findings per PR, so half of them is ~1.7 published per PR at a near-zero wrong rate, against Qodo's 3.04 at 35% wrong |
| **20–49%** | **Viable as a high-precision, low-volume tier.** ~0.7–1.7 proven findings per PR. Fewer comments than any rival and, by construction, right |
| **< 20%** | **The schema discards too much.** `verify/` cannot carry a reviewer, and the deterministic product stands alone |

**Wilson 95% intervals printed beside the rate.** At n = 173 the interval is roughly ±7 points. **An
interval spanning a bar is INCONCLUSIVE and is not a pass.**

## How it is classified, and the check on the classifier

**Three passes, because the classifier is itself a judgement and this project has been burned by
trusting one.**

1. **A mechanical approximation, free** — does the comment name a code identifier, a line, or a
   construct keyword? Scored alongside the model exactly as `decidable.py` scores its keyword flag,
   *"so the model's value is measurable rather than assumed"*.
2. **A model classification** against the three-part definition above.
3. **A hand-adjudicated sample of 30**, drawn by seed before the model runs, graded by me against
   the same definition. **This is the human baseline.**

**If model-vs-hand agreement on the 30 is below 0.85, the model pass is reported VOID** and only the
hand sample's rate is quoted, with its wider interval. That threshold is the one the literature
recommends and it is fixed here rather than after the numbers exist.

**Known risk, stated first:** I wrote the definition and I grade the hand sample, so my labels and
the definition share an author. That is the same structural weakness the p = 0.0007 gate had — a
rater whose reasoning correlates with the criterion. It is not removable without an independent
grader, and the result is reported with that limit attached rather than without it.

## The prediction, written before the run

**I expect 25–40%.** Reasons: the four comments I have read include two that clearly survive
(a missing try/catch around an `await`; an `async` callback passed to `forEach`) and two that
clearly do not (*"inconsistent naming"*; *"the error message mentions login but this is a disable
endpoint"* — semantic, needs intent). Human review is **5.9% structural** by the generous pattern
measured on seven years of history, which argues for the low end; but the goldens here are
*defect* comments rather than all review traffic, which argues higher.

**If it lands above 50% I should be suspicious of my own classifier**, because it would sit far
above the structural rate measured on real review traffic.
