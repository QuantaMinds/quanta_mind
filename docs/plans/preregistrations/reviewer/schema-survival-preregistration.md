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

---

# The result — the calibration gate fired, and the question is not answered

**Run 2026-08-21. All 173 golden comments classified, zero failures.**

| pass | agreement with the hand baseline | bar |
|---|---|---|
| **model** (`gemini-2.5-pro`) | **76.7%** | 0.85 |
| **mechanical** (identifier present, no hedge) | **50.0%** | — |

**THE MODEL PASS IS VOID.** It came in below the 0.85 bar fixed before the run, so its number is not
quoted — it would be a measurement of the classifier rather than of the schema.

**And the free approximation is worthless: 50.0% against a hand baseline is a coin flip.**
`decidable.py`'s discipline — *"the free approximation, scored alongside the model so the model's
value is measurable rather than assumed"* — was applied here and **both instruments failed**, which
is the useful part of running them together.

## What can be quoted

**The hand sample alone: 17 of 30 survive = 56.7%, Wilson 39.2% – 72.6%.**

| bar | verdict |
|---|---|
| **≥ 50%** — the schema is the product | **INCONCLUSIVE.** The interval spans it, and this document says an interval spanning a bar is not a pass |
| **20–49%** — high-precision, low-volume tier | **NOT A PASS EITHER.** The point estimate is 56.7%, which is ABOVE this band, and the interval covers both |

**A FLOOR IS ESTABLISHED. WHICH TIER WE ARE IN IS NOT KNOWN.** Reading the second row as a clean
pass would be the error the first row refuses: 39.2%–72.6% sits inside both bands, so the honest
statement is **"at least 39% survive"** and nothing more. The schema may be the product or may be a
narrow tier, and this run cannot tell them apart. A mechanically-verified reviewer is viable
as a low-volume, high-precision tier — at 173 goldens over 50 pull requests, 3.46 useful findings
per pull request, of which at least ~39% survive the schema is **at least 1.3 published per pull
request with a parser behind each one.** Whether it is the whole product needs n far above 30.

> **THIS CAVEAT TRAVELS WITH THE NUMBER, PERMANENTLY.** The 173 goldens are *benchmark* defect
> reports — curated, and skewed toward the structural, checkable kind of finding. **General review
> traffic is 5.9% structural.** Measuring how many books fit a shelf using the reference section
> tells you little about the general collection. **Any quotation of 56.7%, or of the 39% floor, that
> does not carry this sentence is overstating what was measured.**

## The prediction was wrong in the informative direction

**I predicted 25–40% and wrote that above 50% I should suspect my own classifier.** It landed at
56.7%. The suspicion is recorded rather than resolved: these are *defect* comments from a benchmark,
which skew toward concrete code faults, where general review traffic is **5.9% structural**. The
number is real for this corpus and should not be read as a property of review comments at large.

## What this actually costs to finish, and it is the debt this project already owes

**More hand-grading.** The model cannot do it — 76.7% — and the keyword rule cannot — 50.0%. To
separate 40% from 60% needs roughly 150 hand-graded findings, and **the grader must not be the
author of the definition**, which is the same independent-rater debt four prior designs have
carried.

**That is a day of a person's attention, and it is the only thing standing between this and an
answer.** It is also cheaper than every experiment in this document's history, none of which
resolved it.


---

# The grading pack was designed and is NOT being built — the question it answers is moot

**A day of independent grading was about to be spent measuring the schema's RECALL. Reading the
canonical document back found that its PRECISION is already determined, and it is zero.**

## What the document already said

`QUANTAMIND.md` step 6, written long before this run:

> The verifier is a parser. It decides claims a parser can decide — a symbol exists, a signature has
> that arity, a return precedes a write. **It cannot adjudicate a semantic claim**: that logic is
> wrong, that an edge case is unhandled, that a lock is held. And semantic defects are precisely why
> a model runs at all. So the verifier is structurally unable to check the claim class the model
> exists to produce, and **a wrong semantic finding publishes.**

## And now it is measured, not argued

Design thirteen's 45 real WRONG findings, by the cause the blind rater assigned:

| cause | n | can a parser refute it? |
|---|---|---|
| `EXTERNAL` | 28 | **No** — needs a fact outside the code |
| `TRACE` | 17 | **No** — semantic; a parser cannot follow logic |
| `ABSENT` | **0** | Yes — but every ABSENT verdict in the pool was a PLANTED sabotage item |

**PARSER-REFUTABLE WRONG FINDINGS: 0 of 45.**

**So the schema's recall does not matter.** Even if every useful finding fitted the form, the parser
would still pass all 45 wrong ones through, because not one of them is structurally refutable. **The
grading day would have measured the half that cannot change the answer** — which is the same defect
as design fourteen's exclusion arm, arriving one level up.

## What the best available fixes actually buy, on our own numbers

Live lookup addresses 23 `EXTERNAL` findings; injecting the current date addresses 5 more:

| | W/n | C/n |
|---|---|---|
| today | 52.3% | 8.1% |
| + live lookup | 34.9% | 11.1% |
| **+ lookup + date injection** | **29.3%** | **12.1%** |

**The optimistic case clears the REBUILD bar (W/n < 30%) and misses the field floor (C/n ≥ 49%) by
37 points.** Seventeen `TRACE` findings remain, and nothing in this project or in the field checks
them — an August 2026 result has LLMs failing to re-localise a fault they had localised correctly in
**78%** of cases under semantic-preserving mutation, which is that class exactly.

## The standing decision

**Half B is closed on a measurement.** Not on a judgement, not on a preference, and not pending an
independent grader — **the grader was going to answer a question whose other half is already zero.**

**What would reopen it is unchanged and is now specific:** a verifier that can settle EXTERNAL facts
(a live lookup, which someone has shipped but never measured as a trade) and a verifier that can
settle SEMANTIC claims (which nobody has). The second does not exist, and it is 17 of 45.
