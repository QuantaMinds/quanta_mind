# External evidence, August 2026 — and the one item that corrects a decision we made

**Read against our own measurements, not accepted or dismissed on the strength of the source.**

---

## 1. Live lookup on third-party libraries — this corrects our arm E retirement

**Macroscope integrated a search API so the reviewer can query current documentation during a
review.** The diagnosis is that models review code against libraries using stale training knowledge,
and that diagnosis matches ours exactly.

> **THE 55% FIGURE DOES NOT MEASURE WHAT IT IS USUALLY CITED FOR, AND I CITED IT THAT WAY FIRST.**
> Verified against the source: *"Macroscope was able to reduce review comments by 55% by querying
> Parallel's APIs."* **That is a reduction in comment VOLUME.** The case study gives no baseline
> false-positive rate, no definition of a false positive, no ground truth, and **no check that true
> findings were not removed alongside the wrong ones.**
>
> **It is D with no L** — the exact shape `filter-gate-preregistration.md` refuses, in this
> project's own words: *"Precision rises whatever you delete, including at random. A number that
> improves under a null operation is not evidence. The bar is the trade."* Deleting 55% of
> library-related comments at random would also read as a 55% reduction.
>
> **So this is a plausible mechanism with an unmeasured effect, not a published effect size.** The
> distinction matters because it is the whole reason the correction below is partial.

**That is our largest measured failure class, and it is not close.** From design thirteen's blind
adjudication, recomputed:

| | count | share |
|---|---|---|
| WRONG findings | 45 | 52.3% of real findings |
| of those, `EXTERNAL` — needs a fact the diff cannot supply | **28** | **62% of wrong** |
| lookup-addressable (tags, versions, releases, package existence) | **23** | **51% of ALL wrong findings** |
| date-shaped (a lookup cannot answer "what is today") | 5 | 11% of all wrong |

*"`actions/setup-python@5fda3b95` does not exist"* is a documentation-staleness error. Someone has
now shipped the fix and measured it.

### What it corrects

**Arm E was retired on the reasoning that exclusion is free and covers both tags and dates. That
reasoning is incomplete.** Exclusion also discards CI config's correct findings, and CI config has
the **highest correct-rate of any file kind we have measured**:

| file kind | n | **CORRECT** | WRONG |
|---|---|---|---|
| **CI config** | 32 | **12.5%** | 65.6% |
| other config | 4 | 0.0% | 75.0% |
| source code | 50 | 6.0% | 42.0% |

**Lookup keeps those four findings; exclusion throws them away.** That argument stands on OUR
numbers — 12.5% correct on CI config against 6.0% on source code — and not on Macroscope's, which
measures no trade at all. **What the external work supplies is a mechanism someone has shipped, not
evidence that it wins.**

### What it does not fix, and the fix is trivial

**A lookup answers "does this tag exist". It never answers "what is today".** Five of our wrong
findings are date errors — the model believing 2026 is the future while running in 2026. **Inject
the current date into the prompt.** One line, 11% of wrong findings, and it should be done whether
or not a lookup ever ships.

---

## 2. The retrieval claim — our own data contradicts it

**Sourcegraph's position is that the structural fix is retrieval: a tool that sees the diff produces
diff-quality comments, one that sees the codebase produces codebase-quality comments.**

**We tested that and it did not separate.** Cross-tabulated against a mechanical marker — does the
golden comment name an identifier absent from the diff we sent? — **27% "only them" on visible
issues against 21% where the comment names nothing outside the diff.** And the twelve issues
Greptile caught that we missed contained no cross-file reasoning at all: a misspelling, invalid ERB,
a colour value.

**Sourcegraph sells a retrieval product. This is vendor positioning contradicted by our own
measurement, and it is recorded as such rather than as a finding.**

---

## 3. Three vendors have now converged on generate-wide-then-discard

**Claude Code Review shipped March 2026 with multiple specialised agents analysing the diff in
parallel, a verification step filtering false positives, and severity ranking — the same
architecture as Qodo, and Greptile's confidence thresholds are the same shape.**

**That strengthens the case that it is the field's answer and weakens it further as a
differentiator.** We already removed "we have a judge" from the differentiator list because Qodo
ships one. Three is not a gap in the market.

---

## 4. Two things we have never tried

**A "pre-existing" severity.** The emerging pattern tags findings Important / Nit / **Pre-existing**
— a true observation about code the change did not introduce. **That category is absent from our
taxonomy**, and some share of our WRONG and TRIVIAL findings may be pre-existing-and-true. Worth
checking, because those are a different product: a backlog, not a review.

**Per-category thresholds.** Our gate is single-threshold. **Our own file-kind rates differ enough
to derive one** — 65.6% wrong on CI config against 42.0% on source code — so a per-category
threshold is computable from data already on disk.

---

## 5. Discounted

**"98% precision"** — an April 2026 listicle, a vendor claim with no methodology and no benchmark.
Against Martian's offline layer, where the best measured tool is Qodo at **67.9%**, it is marketing.

---

## What none of this changes

**Our correct-rate is 3.7–12% across every form and every file kind.** A 55% cut in library false
positives **removes wrong comments; it does not create right ones.** The schema question and the
independent grader still gate whether the reviewer half can exist.

**If `--deep` ever opens, live lookup is the highest-value item here** — it targets our largest
measured class, 51% of all wrong findings. **But it arrives with no measured trade**, so it would
have to clear the same bar as everything else: false positives removed against true findings lost,
pre-registered, on a corpus it was not tuned on. **Until then it is a fix for a product we have not
decided to ship.**
