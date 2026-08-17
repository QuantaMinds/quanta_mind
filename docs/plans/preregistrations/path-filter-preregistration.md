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
