# Pre-registration — does reject-on-imprecise-anchor hold on unseen repositories?

**Written before any pull request is fetched.** The rule under test was found by searching the
enriched run's own data, where eight filters were tried and none had an interval excluding 50%.
It is a hypothesis. This is the test that decides whether it is anything more.

## The rule, fixed exactly as found

**Reject a finding if EITHER condition holds:**

1. `line_a` or `line_b` falls **outside the line range of the function the model was shown**
2. the `ast` snapper **had to move** either anchor off the line the model returned

Publish only what survives. Everything rejected is recorded as an `Unresolved`-style residual, not
discarded silently — the same discipline as the coverage line.

## What was observed on the data that produced the rule

| | kept | wrong |
|---|---|---|
| no filter | 54 | 61.1% |
| **the rule** | **20 (37%)** | **35.0%**, Wilson [18.1%, 56.7%] |

## The prediction, stated so it can fail

**On a fresh set of pull requests from repositories not used before, the surviving findings will be
under 50% wrong.** That is the same bar the review half has been held to throughout.

| reading | rule |
|---|---|
| **HOLDS** | survivors < 50% wrong **and** the Wilson upper bound < 60% |
| **FAILS** | survivors ≥ 50% wrong |
| **UNDERPOWERED** | fewer than 20 surviving findings — report and do not interpret |

**A second, harder prediction, because the first can be met by a filter that merely discards
randomly:** the rule must *separate*. **Rejected findings must be wrong at a higher rate than
survivors, by at least 15 points.** A filter that keeps 37% of findings at the same error rate as
the whole is not a filter, it is a coin.

## Population

**Fresh pull requests from `scikit-learn`, `pandas`, `django`, `ansible`, `scrapy`, `celery`** —
none used for any review-half measurement. The prompt, model, schema, budget and rules are
identical to the enriched run. Nothing is tuned between runs.

## And what happens next either way

**This is one turn of a loop, not a verdict.** Whatever the number, the errors it produces get
categorised the same way — where does the model still go wrong, and is there a pattern with a
mechanical signature. **The loop stops when a turn produces no pattern, or when the surviving
findings clear the bar on a sample that was not used to find the rule.**


---

# RESULT — **BOTH PREDICTIONS FAIL**, and the reason is worse than the filter

39 findings, 20 pull requests, six repositories never used for a review-half measurement. Identical
prompt, model, schema, budget and rules — only the corpus differs. Blind adjudication.

| | seen corpus | **unseen** |
|---|---|---|
| CORRECT | 13.0% | **0.0% — zero of 39** |
| WRONG | 61.1% | **82.1%**, Wilson [67.3%, 91.0%] |
| UNFALSIFIABLE | 14.8% | 10.3% |
| TRIVIAL | 11.1% | 7.7% |

## The rule

| | n | wrong | correct |
|---|---|---|---|
| survivors | 17 | **76.5%** | **0** |
| rejected | 22 | 86.4% | **0** |
| **separation** | | **+9.9 points** | needed ≥ +15 |

**Prediction 1 — survivors under 50% wrong: FAILS at 76.5%.** Also underpowered at n = 17 against
the 20 floor, which the pre-registration required be said regardless of the number.

**Prediction 2 — rejected at least 15 points worse: FAILS at +9.9.**

**The rule was tuned on noise, exactly as it was labelled when found.** Eight filters on n = 54,
none with an interval excluding 50%, and the best one does not survive contact with fresh code.

## The finding that ends the loop

**Zero correct findings on both sides of the filter.** A rejection rule can only raise precision if
some findings are correct — it partitions a set, it does not create signal. **With a base rate of
zero there is nothing to separate, and no filter, prompt or context change repairs that.**

**And the drop from the first corpus is real, not noise.** Correct rate 13.0% → 0.0%, **Fisher
exact p = 0.039**. Wrong rate 61.1% → 82.1%, **p = 0.030**.

**The most likely explanation is the least flattering one, and it is mine.** The prompt rules used
in both runs were written against the *first* corpus's specific failures — *"do not assert what a
caller passes"*, *"do not report hedged claims"*. That is tuning on the evaluation set. **The 13%
was already inflated by it, and the unseen corpus shows what the reviewer does without that
advantage.**

## Where the loop stops, and why that is a result

The instruction was to iterate: run, find the error pattern, fix, re-measure, repeat while accuracy
moves. **Four turns:**

| turn | action | outcome |
|---|---|---|
| 1 | measure the reviewer | 66.7% / 74.2% wrong, two blind raters |
| 2 | fix anchors + add context | 61.1% wrong — **no movement**, p = 0.53 |
| 3 | deep-dive the error data | found imprecision is a *symptom*; reject-not-repair looked promising |
| 4 | **verify on unseen repositories** | **82.1% wrong, 0 correct; the rule fails both predictions** |

**The loop terminates on its own stopping condition: a turn that produces no pattern.** There is no
error pattern to extract from turn 4, because the errors are not concentrated in a mechanically
detectable class — they are spread across pointer errors, arithmetic the model could have checked
in its own prompt (*"1450804465901089690 − 1450804465901089614 = 76, exactly the comment's
value"*), and claims contradicted by lines adjacent to the ones cited.

**What would be needed next is not a fix, it is a different design** — and this project's own rule
applies: the review half is a separate project, and nothing in four turns of measurement argues for
starting it now.
