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
