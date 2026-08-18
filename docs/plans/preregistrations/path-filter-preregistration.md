# Design nine — the same reviewer, told which files it may review

**Design eight failed at 60.8% wrong.** It also produced the cleanest single signal this project
has: **18 of 18 findings about lockfiles were WRONG. One hundred percent.**

This design changes one thing. **The diff is filtered before the model sees it.**

---

## The stratification design nine is built on — and the two bugs I had to fix to get it

**Reported in the design-eight write-up as "source code 20.0% wrong on n = 15". That number was
right by accident.** Two defects in my own analysis script, found while preparing this document:

1. `.github/*.yml` was bucketed with lockfiles by a `\.ya?ml` pattern, so CI configs — which
   produced **three of the eight CORRECT findings** — were counted as generated files.
2. The captured paths carry a `:LINE` suffix, so `\.md$` never matched and the docs bucket silently
   read **zero**.

**Corrected, with the suffix stripped and CI split out:**

| file kind | n | CORRECT | TRIVIAL | UNFALSIFIABLE | WRONG | wrong-rate |
|---|---|---|---|---|---|---|
| **lockfile** | 18 | 0 | 0 | 0 | **18** | **100.0%** |
| docs | 8 | 0 | 0 | 2 | 6 | 75.0% |
| dependency manifest | 5 | 0 | 0 | 2 | 3 | 60.0% |
| CI config | 4 | **3** | 0 | 0 | 1 | 25.0% |
| **source code** | 16 | **5** | 3 | 5 | 3 | **18.8%** |

**Every CORRECT finding in the entire run came from source code or a CI workflow. Not one came
from a lockfile, a manifest, or a document.**

---

## The change

**One rule, applied to the diff before the model is called**, so the excluded files consume no
attention rather than being filtered out of the answers afterwards:

| excluded | pattern |
|---|---|
| lockfiles | `*.lock`, `package-lock.json`, `yarn.lock`, `pylock*.toml` |
| dependency manifests | `pyproject.toml`, `requirements*.txt`, `Pipfile`, `package.json` |
| documentation | `*.md`, `*.mdx`, `*.rst`, `*.html` |

**KEPT: source code and `.github/` CI configuration.** CI configs are hand-written, they produced
three of eight CORRECT findings, and excluding them because they are YAML would repeat the exact
bucketing mistake above.

**Everything else is unchanged** — same quote-anchored prompt, same model-free gate, same rubric,
same sabotage controls.

---

## Corpus — fresh again

**Thirty-eight repositories are burned.** Six more, never touched, **fifteen** pull requests each,
**ninety** total. Design eight yielded 20 in-scope findings from 60 pull requests; ninety is chosen
to put n where a wrong-rate means something.

`dbt-labs/dbt-core`, `streamlit/streamlit`, `dagster-io/dagster`, `encode/httpx`,
`huggingface/datasets`, `bokeh/bokeh`.

---

## The bars

| # | bar | rationale |
|---|---|---|
| **H1** | **published wrong-rate < 50%** | unchanged, the bar eight designs have now faced |
| **H2** | UNFALSIFIABLE < 25% | the relabelling discriminator, unchanged |
| **H3** | sabotage catch rate ≥ 75% | **checked and reported before H1**, as in design eight. Below it the run is VOID, not a result |
| **H4** | yield ≥ 0.30 published per pull request | **lowered from 0.50** because the filter removes a category that supplied 60% of design eight's output. Lowering a bar between runs is exactly what this project forbids, so it is stated plainly: **this is a different bar for a different population, not the same bar relaxed.** ≥ 27 findings across 90 pull requests |
| **H5** | ≥ 25 published findings | below this the wrong-rate's interval is too wide to decide anything, and the run is reported as UNDERPOWERED rather than as a pass or a fail |

**H1 decides. H3 gates whether it may be read at all.**

### H1 is an INTERVAL, not a point estimate — fixed before the number exists

**A point estimate under 50% is not a pass unless the Wilson upper bound also clears 50%.**
Otherwise the run is reported as **CANNOT DISTINGUISH**, which is neither a pass nor a fail.

At the sample sizes in play:

| n | wrong | rate | 95% Wilson | verdict |
|---|---|---|---|---|
| 70 | 14 | 20.0% | 12.3–30.8% | **PASS, clear** |
| 70 | 21 | 30.0% | 20.5–41.5% | **PASS, clear** |
| 70 | **26** | **37.1%** | 26.7–**48.9%** | **the last clean pass** |
| 70 | 27 | 38.6% | 28.0–**50.3%** | **CANNOT DISTINGUISH** |
| 70 | 32 | 45.7% | 34.6–57.3% | CANNOT DISTINGUISH |
| 70 | 38 | 54.3% | 42.7–65.4% | CANNOT DISTINGUISH |

**Note what this says about a 54% result: it is not a clean fail either.** At n = 70 nothing
between roughly 37% and 63% separates from the bar. **The honest outcomes are "clearly under",
"clearly over", or "this run cannot tell you" — and the third is the most likely one.**

### A correction to how design eight's subgroup has been described

I have twice called the 18.8% source-code subgroup too wide to decide anything. **The interval is
6.6–43.0%, which does NOT cross 50%.** On width alone it would have passed.

**The reason to distrust it is selection, not width.** It was found by slicing a failed run by a
variable that was not pre-registered, after seeing the failure. That is the whole objection, and
stating it as "the sample is too small" was imprecise in a way that made the objection sound
weaker than it is.

---

## Predictions

1. **Wrong-rate lands between 35% and 55%.** Design eight's in-scope subset was 20% on n = 20, and
   **I do not believe that survives a larger sample** — it is four wrong findings.
2. **Yield falls below design eight's 0.85** and is the bar most at risk again, despite H4.
3. **The lockfile failure mode disappears entirely**, since those files are no longer sent.
4. **A new dominant failure mode appears in its place.** Design eight replaced design one's anchor
   failures with lockfile failures; removing lockfiles should reveal whatever is underneath rather
   than leaving nothing.

**Prediction 1 is deliberately pessimistic relative to the 18.8% subgroup.** If the run comes back
near 20%, that is a genuine surprise and the replication becomes the priority. **If it comes back
near 55%, the subgroup was small-sample noise and design nine is the ninth failure.**

---

## What a pass would mean

**One configuration, one fresh corpus, at n around 30.** It licenses a replication on a second
fresh corpus, nothing more.

**It would not reopen `infer/`.** That needs a result to hold twice, and the deterministic half is
the roadmap regardless.

**And a near-miss is a fail. 51% is a fail.**

---

# The result — **PASS**, the first in nine designs

77 pull requests from six untouched repositories, 60 reviewed (17 had nothing left after
filtering), 54 raw findings, **49 published**, all 49 hand-adjudicated out of the Gemini family.
Artefacts: `research/phase0/quote/quote9_run.json`, `adj9/`.

## The control first

**8 sabotaged findings graded WRONG, 8 of 8. Catch rate 100%.** The rater discriminates.

## The bars

| bar | threshold | result | |
|---|---|---|---|
| **H3** sabotage catch | ≥ 75% | **100%** | **PASS** |
| **H4** yield | ≥ 0.30/PR | 0.64 | **PASS** |
| **H5** findings | ≥ 25 | 49 | **PASS** |
| **H2** UNFALSIFIABLE | < 25% | 16.3% | **PASS** |
| **H1** wrong-rate | **< 50%** | **30.6%**, Wilson **19.5–44.5%** | **CLEAN PASS** |

| verdict | design 8 | **design 9** |
|---|---|---|
| CORRECT | 15.7% | **30.6%** |
| TRIVIAL | 5.9% | 22.4% |
| UNFALSIFIABLE | 17.6% | 16.3% |
| **WRONG** | **60.8%** | **30.6%** |

**The upper bound clears 50%, so this is a clean pass under the interval rule fixed before the
number existed — not a point estimate that happens to sit under the bar.**

## Where the findings are right and where they are not

| | n | CORRECT | WRONG | wrong-rate |
|---|---|---|---|---|
| **source code** | 25 | **13** | **0** | **0.0%** |
| tests | 11 | 0 | 7 | 63.6% |
| CI / config | 13 | 2 | 8 | 61.5% |

**Not one wrong finding about source code.** Design eight's post-hoc 18.8% subgroup replicated.

## Predictions

| # | predicted | actual |
|---|---|---|
| 1 | wrong-rate 35–55% | **30.6% — wrong, better than predicted** |
| 2 | yield falls, H4 most at risk | fell 0.85 → 0.64, passed easily — **half right** |
| 3 | the lockfile failure mode disappears | **71% → 40%, not gone.** It migrated into the CI files we deliberately kept — conda channels, pip specifiers, action versions |
| 4 | a new dominant failure appears underneath | **right: "claims a merged, passing test is wrong" is now 47% of failures** |

## The headline number is the DEDUPLICATED one, and it passes by 0.2 points

The model emits the same finding more than once inside a single pull request. **43 of the 49 are
unique by (pull request, claim); all six duplicates sat in TRIVIAL.**

| | all 49 | **unique 43** |
|---|---|---|
| WRONG | 30.6% | **34.9%** |
| Wilson upper bound | 44.5% | **49.8%** |

**34.9% is the number of record.** It clears the bar by two tenths of a point, which is a pass and
should never be described as a comfortable one.

## Is the improvement over design eight real? Yes — and NOT by the interval test

**Two 95% intervals can overlap while the difference is significant.** Design eight's interval
(47.1–73.0%) overlaps design nine's deduplicated one (22.4–49.8%), and the difference is still
real:

| comparison | Fisher exact | |
|---|---|---|
| design 8 vs 9, all 49 | **p = 0.0029** | real |
| design 8 vs 9, unique 43 | **p = 0.0142** | real |
| **source-only, 3/16 vs 0/22** | **p = 0.0664** | **not significant** |

**The stratified comparison is the MECHANISM but it is the weaker evidence**, because n is smaller.
Leading with it would understate what is established and overstate what is not.

**The strongest defensible statement about source code pools both designs: 3 wrong of 38 = 7.9%,
Wilson 2.7–20.8%.**

## Three limitations, and the first is the serious one

**The rater wanted this to pass.** The 8-of-8 sabotage catch rules out rubber-stamping. **It does
not rule out systematic leniency on the 49 real items**, and nothing in this run addresses that.

**A second corpus rated by the same person reproduces the bias with more data.** The precedent is
in this project's own results: on design one, a rater from a disjoint pool disagreed on **9 of 66**
findings and was **harsher on 5 of them**, moving the wrong-rate from 66.7% to 74.2%. **A
replication that does not change the rater is not a replication of the thing in doubt.**

**Design eight was not a clean fail either.** Its 60.8% carried a Wilson interval of **47.1–73.0%**,
which crosses 50%. It failed its bar as written — a point estimate — but under the interval
standard registered afterwards it was **CANNOT DISTINGUISH**. Both are true and the second should
have been said at the time.

**22.4% TRIVIAL is a defect, not a neutral bucket.** The model emitted the identical finding three
times inside one pull request (`datasets#8369`, the conda-channel claim). Qodo deduplicates at
generation time; we do not.

## What this licenses

**A replication on a second fresh corpus, with a rater who is not the author.** Nothing else.

**The replication's pre-registration must carry all four:**

1. **A different rater pool**, blind, out-of-family, with the same sabotage controls. Without this
   the run adds data to one bias.
2. **The unique-finding denominator as primary**, with duplicates reported separately.
3. **The pooled before/after as the headline and the stratum as the mechanism**, not the reverse.
4. **A pre-registered prediction about test files.** Design nine's failures are 63.6% wrong on
   tests and 47% of all failures are "this merged, passing test is broken" — the same disposition
   as the 2026-timestamp claims, the model treating its own uncertainty as evidence about the
   world. **Excluding test files afterwards would be a post-hoc filter; predicting it now makes it
   a test.**

**`infer/` stays closed.** One pass on n = 49, rated by an interested party, is not a product
decision. The deterministic half remains the roadmap.
