# Design fourteen — the model lever, with the bar fixed first

**Written before the run. Nothing below is edited after a number exists.**

This is the re-run the reserve conditions describe. `docs/plans/implementation.md` under "What would
reopen the reserved layers" requires, for `infer/` to open: G2 held **twice**, at least once by a
rater who did not design the experiment, **and** the correct-rate cleared alongside it. It has never
held once. This document fixes what would count.

---

## Why a re-run is admissible at all

The reserve conditions list what does **not** reopen the layers: a better prompt, aggregation, and
*"a stronger model alone, **without** a pre-registration fixing the bar before the run."* The
qualifier is the opening, and this document is the thing it requires. The lever being pulled is the
subject model. Everything else is held as close to design thirteen as the diagnosis permits.

---

## What design thirteen actually measured, recomputed from its own artefacts

`research/phase0/quote/adj13/verdicts.json` against `KEY_DO_NOT_OPEN.json`, blind, with ten planted
sabotage findings mixed into the pool.

**The rater caught 10 of 10 sabotage items.** The adjudication is load-bearing and it earns that.

| pool | n | W/n | Wilson 95% | C/n |
|---|---|---|---|---|
| all real findings | 86 | **52.3%** | 41.9% – 62.6% | **8.1%** |
| source code only, config excluded | 50 | **42.0%** | 29.4% – 55.8% | **6.0%** |

**Every WRONG finding falls into exactly two causes, and the third has disappeared:**

| cause | count | what it is |
|---|---|---|
| `EXTERNAL` | 28 | deciding it needs a fact the diff cannot supply |
| `TRACE` | 17 | the model traced the code and got it wrong |
| `ABSENT` | **0 of 86 real** | all ten `ABSENT` verdicts were the planted sabotage |

**The anchoring failure class is gone.** In the earlier adjudication it was 36.4% of all findings —
"the line numbers do not point at the code the claim is about" — and five designs that repaired the
line number all failed. Design thirteen removed the field: the model quotes code and
`research/phase0/quote/gate.py` derives the line from where the quote sits, so the prose and the
anchor cannot disagree because one is a function of the other. **Zero real findings mis-anchored.**
That part of the review half works and is not what is being retested.

**`EXTERNAL` is concentrated, and it contradicts a decision still live in the code.**

| bucket | n | W/n | C/n | EXTERNAL failures |
|---|---|---|---|---|
| `.github/` | 32 | **65.6%** | 12.5% | **21 of 28** |
| other config | 4 | 75.0% | 0.0% | 3 of 28 |
| source code | 50 | 42.0% | 6.0% | 5 of 28 |

`research/phase0/quote/paths.py` keeps `.github/` **on purpose**, and says so: *"CI configuration is
hand-written and produced three of design eight's eight CORRECT findings."* That was decided on
design eight. Design thirteen's own data says `.github/` is now the single largest source of
wrongness in the experiment, and the failures are a recognisable kind — the model asserting that a
pinned action SHA is not tagged what it is tagged, which no diff can settle. `AGENTS.md` already
records the same thing from another angle: *"CI-config findings are 66.7% wrong, 23 of 24
undecidable from a diff."*

---

## Design fourteen: exactly three changes

1. **The subject model becomes a current frontier model.** Design thirteen ran `gemini-2.5-pro`.
   This is the lever, and it is the only one the reserve conditions leave open.
2. **`.github/` and remaining config paths are excluded before the call**, reversing the
   design-eight decision on design-thirteen evidence. The filter runs before the request, not after,
   for the reason `paths.py` already gives: removing the findings afterwards leaves the model
   spending its attention on files it cannot reason about.
3. **A new corpus of six repositories**, each verified at zero prior mentions anywhere under
   `research/` by `scripts/guard/records/check_burned_corpora.py --check` before selection.

**Held fixed:** the quote-anchor prompt, `gate.py` unchanged, the rubric unchanged, the sabotage
items, the blind chunking, and the thresholds below.

**Not changed, deliberately:** no aggregation (retired on measurement — 4 of 5 correct findings came
from one arm, and wrong findings recur more often than correct ones), no rejection filter, no anchor
repair, no conventions file. Each was tried and moved nothing.

---

## The bars, fixed now

Let **C**, **W**, **U**, **T** be the counts and *n* = C + W + U + T over **real findings only**,
sabotage excluded from every rate.

| reading | rule |
|---|---|
| **STOP** — the review half still does not work | **W / n ≥ 0.50** |
| **REBUILD** the inference step | 0.30 ≤ W / n < 0.50 |
| **PROCEED**, residual as the product | W / n < 0.30 **and** U / n < 0.50 |
| **PROCEED but the schema is wrong** | W / n < 0.30 **and** U / n ≥ 0.50 |

**And the second bar, which is the binding one: C / n ≥ 0.49**, the bottom of the independent
benchmark's 49–76% precision band for the field. Below it we are worse than the competition while
claiming to be quieter than it, and quietness is only a virtue if what breaks the silence is right.

**BOTH must clear. Neither substitutes for the other.** A design clearing W/n by finding almost
nothing is worthless, and the reserve conditions say so in as many words.

**Wilson 95% intervals are printed beside both.** At n ≈ 90 the interval is roughly ±10 points.
**A point estimate on the correct side of a threshold with an interval spanning it is INCONCLUSIVE
and will be called one — it is not a pass.**

---

## The prior, stated before the run so the result cannot be re-read afterwards

On design thirteen's source-code-only pool: **W/n = 42.0%, C/n = 6.0%, 3 correct findings in 50.**

- **W/n clearing 0.50 is likely** and would not be surprising; it is already below it once config is
  excluded, which is why excluding config is not the interesting part of this design.
- **C/n reaching 0.49 requires an eightfold increase in the correct-finding rate. I do not expect it
  to clear.** This is written down now because a null result here must not be reported as "the model
  improved but the bar was too high", and a pass must not be reported as expected all along.

**The most likely outcome of this run is REBUILD on W/n and a failure on C/n**, which leaves the
reserve closed and costs one experiment rather than a shipped reviewer that is wrong half the time.

---

## Adjudication protocol

- **Blind.** Findings are chunked with the key sealed in `KEY_DO_NOT_OPEN.json`, unopened until
  every verdict is recorded.
- **Sabotage retained**, at the same ratio. A pool where the planted items are not caught invalidates
  that rater's block rather than the design.
- **Two clearances, and one grader must not have designed the experiment.** This is the condition
  four prior designs still owe. A second pass by the same family in a fresh context is **not** the
  independent grade — it is what design thirteen already has, and `undecidable-paths-preregistration.md`
  records that it does not count toward replication.
- Rater agreement is reported as **κ and raw agreement on the binary WRONG / not-WRONG cut**, which
  is the only distinction the thresholds depend on.

## Recorded alongside, not graded

- **Findings per pull request**, against a product that promises one comment.
- **Every silence**: whether it was correct, or a defect present and missed. This is the coverage
  line's honesty tested directly, and it is the one place where being wrong is worse than being
  quiet. Design thirteen did not audit this and recorded the omission as a gap.
- **`finishReason` on every call.** Six of design thirteen's eight silences pinned the thinking cap
  first; a truncation reported without its finish reason reads as "the model found nothing", which
  is the exact failure shape this project keeps hitting.
