# The evidence ledger

Every measurement this project has run, against the claim it is supposed to carry. One row per
measurement, and the last column is the only one that matters: **does the evidence reach the
claim, or is there a gap that argument is currently covering?**

This exists because the numbers were produced over months in different harnesses, and a figure
that was honest when measured drifts into carrying weight it cannot hold. `publishing-rules.md`
governs what may be said; this file governs what is *known*.

**The one-sentence summary, stated before the detail so it cannot be buried:** the half of the
product that decides *where to look* is measured and holds up; **the half that decides *what to
say* has now been measured, by two independent raters, and it failed its own pre-registered
gate.**

| the review half, adjudicated | rater 1 | rater 2 | agreement |
|---|---|---|---|
| **wrong** | 66.7% | **74.2%** | 92.4%, κ = 0.82 |
| correct | 9.1% | 4.5% | both far below the field's 49% floor |

**The threshold was 50% wrong, committed before a single finding was read. Both readings clear it,
and every disagreement between them made the result worse rather than better.** The reading is:
stop building the review half in this configuration. `docs/plans/adjudication-preregistration.md`
carries the protocol, the verdicts and the disagreements.

---

## 1. What is measured, and holds

| Measurement | n | Result | Claim it carries | Reaches it? |
|---|---|---|---|---|
| **Ranker names the repaired function** | 53 verdicts, 2 raters | 69–70% on repairs vs 47–48% on non-repairs, **+22 points**, Fisher p = 0.0151 | "We are right about where to look" | **Qualified.** Replicated by an independent rater at 92% agreement, **Cohen's κ = 0.66** (moderate, not strong), same effect size to within a point. Rests on **39 genuine repairs**; the honest claim is +22 points, **95% CI +6 to +38** |
| **Firing rate holds across velocity** | repos differing 80× | **10–12%** everywhere, via a percentile rather than a threshold | "Quiet" | **Yes.** The percentile is what makes it hold; a fixed threshold fired on 11% of one repo and 53% of another |
| **Three units cover the change** | 1,969 paired events, 8 repos | file top-3 misses **1.22%**; function top-3 misses **8.84%**; five units miss 3.50% | "Three units miss at most 8.84%" | **Yes, with a named proxy.** See the caveat below |
| **File-level allocation beats function-level** | same 1,969 | +7.62 points, McNemar exact **p < 0.0001**, discordant b = 157 / c = 7 | The allocation choice in the architecture | **Yes** |
| **The competitors' attribution rule is wrong** | 53 verdicts, 3 corpora | **67.9%** of verdicts blame a change sharing no symbol with the fix; survival 32.1%, reproduced at 36.1% and 35.7% | "Two thirds of what a file-overlap reviewer blames is not what broke" | **Yes.** The strongest result here |
| **Leaking the future degrades the ranker** | corpus-wide | top-1 moved **50.0% → 37.5%** when future commits were visible | The index is genuinely bounded by the past | **Yes — and this is a known-answer test**, not a result. It is how we know the harness measures anything |
| **Six allocation variants against controls** | 1,969, pre-specified, held-out | **V0 (file top-3) still standing**; V2 not significant (train p = 0.18, holdout p = 0.125) | That the shipped policy is the best of those tried | **Yes**, and the holdout caught V2 overfitting on its first use |
| **Bot prevalence in OSS review** | 5,195 comments, 8 repos | **31.5%** bot-written, 0.0% to 92.0% by repository; bot output **52.9%** structural vs human **5.9%** | Corpus hygiene — and the argument for schema-forced structure | **Yes**, as a floor. The detector is a login-and-marker match, so undetected bots bias it down |
| **Cost per review, billed** | 68 requests, 23 PRs, live Vertex | **$0.119 mean** per PR at a 4,096 thinking cap; **likely ~$0.131** once the 10% non-global-endpoint premium in force since 1 July 2026 is applied | "$0.140 per pull request" | **Yes — but the estimate was right by luck.** See below |

**The cost figure was right in magnitude and wrong in structure, and the structure is what
matters.** The $0.140 estimate modelled a large prompt made cheap by caching. The measurement
found the opposite shape:

| where the money goes | share of the bill |
|---|---|
| input (prompt) | **5.2%** |
| **thinking** | **91.3%** |
| answer | 3.5% |

**Two errors that partly cancelled.** The prompt is far smaller than assumed — 1,674 tokens mean,
because one function and one diff is not much text — and *thinking*, which the estimate did not
model at all, is nine tenths of the bill. Net: $0.119 measured against $0.140 derived, a 0.85×
that flatters the estimate for reasons it did not contain.

**The consequence is architectural, not financial. Prompt caching — the whole of "Step 5 — read,
with the repository cached" — would save 4.7% of this bill.** It is optimising a rounding error
against a term that dominates it twenty to one. That verdict is conditional on prefix size and
the relationship is worth stating, because the prefix here is a ~150-token stub rather than the
"repository conventions, resolved signatures, index summary" the design specifies:

| cached prefix | input share | caching saves |
|---|---|---|
| stub (as measured) | 5.2% | **4.7%** |
| 2,000 tokens | 10.7% | 9.6% |
| 10,000 tokens | 27.6% | 24.8% |
| 40,000 tokens | 57.6% | 51.9% |

**So caching is worth building only if the prefix is deliberately made large, and that is a
design decision nobody has made yet.** It cannot be inherited from the Anthropic-era plan, where
prefix caching was automatic and free to assume.

**And the headline number is a parameter, not a property of the workload.** Thinking was capped
at 4,096 by the harness; **46% of requests pinned that cap**. The first run set no budget and
observed a mean of 5,744 with a maximum of 13,108 — **1.51× the cost, $0.183 per pull request**.
The price of a review is currently set by a dial, and the dial has never been tuned against
output quality.

---

## 1a. "Ten measurements" is a count, not a weight — and the count is inflated

**Written against the author's own repeated phrasing.** "Ten measurements support the ranking half"
has been said in this project many times, including throughout the session that produced the
adjudication. Audited strictly, the table above does not contain ten independent supports for the
ranking half.

| row | what it actually is |
|---|---|
| three units cover the change | **the same 1,969 events on the same 8 repositories** |
| file-level beats function-level | **the same 1,969** |
| six allocation variants | **the same 1,969** |
| ranker names the repaired function | 53 hand-labelled verdicts |
| the attribution rule is wrong | the same verdict corpus, extended to 3 corpora |
| leaking the future degrades the ranker | **a known-answer test on the harness.** It proves the instrument measures something. It is not evidence for the product |
| bot prevalence | **corpus hygiene. It says nothing about the ranking half** |
| cost, and thinking's share of it | **says nothing about either half's quality** |

**So the ranking half rests on roughly two datasets, not ten measurements: 1,969 paired events and
53 hand-labelled verdicts, both drawn from the same eight convenience repositories.** Three
analyses of one dataset are three analyses, not three replications. Counting them as ten let a
number do work the evidence does not.

**And the strictest true sentence available is worse than that.** The *only* test of the ranking
half ever run on repositories **outside those eight** — whether the ranker points where human
reviewers actually commented, on pre-2022 code — **returned a null.** The reconciliation offered
for it (human comments are 5.9% structural, so where reviewers comment is not where defects live)
is coherent and rests on an independently measured number, **and it was constructed after seeing
the null.** It is an explanation, not a defence, and it has been labelled that way from the moment
it was written.

**What that means for the position the company is taking.** The measurement-layer claim is the one
the evidence reaches — but it reaches it on two datasets from eight repositories, with one
out-of-sample test that failed and was explained. **The properly powered rerun on six fresh
repositories is therefore not a nice-to-have. It is the first real external-validity test the
ranking half will ever have faced**, and its reading was fixed in advance in
`docs/plans/ranking-rerun-preregistration.md` precisely because the temptation to explain a second
null would be very strong.

**Also corrected here.** The +22-point result's independent replication is cited across this
project as κ = 0.92. **Agreement was 92%; Cohen's κ was 0.66** — moderate, not strong. And the
effect rests on **39 genuine repairs**, so the defensible claim is *+22 points, 95% CI +6 to +38*.
A six-point product and a thirty-eight-point product are different products.

---

**The named proxy on the coverage figure.** "Where a defect exists" means *a later commit within
90 days whose message contains a fix word touched the same unit*. That is an outcome rule, not a
defect oracle, and its own limit is measured: **only 14% of the pairs it admits are genuine
repairs.** The coverage number is conditional on the rule, and the rule is a proxy. It is the
best available without hand-labelling every event, and it is not the same thing as "8.84% of real
bugs."

---

## 2. What was measured and did not survive

Kept visible because a discarded number that quietly disappears becomes a number nobody
remembers discarding.

| Measurement | Result | Disposition |
|---|---|---|
| The founding correlation test | RR **1.040** against a 1.5 stop threshold | **Null.** Killed the previous product |
| Coverage-gated merge | RR **0.916**, fires on 45% of PRs, discriminates on none | **Null** |
| Historically-buggy-file warning | RR **1.56**, p = 0.334, fires on 36% of clean changes | **Null** |
| "You forgot to change file X" | Named the right file **0 of 8** times | **Dead** |
| No-test-added flag | Backwards — untested changes broke slightly *less* | **Null** |
| Ten PR metadata signals | **Nothing survived** multiplicity correction | **Null** |
| Rank top file, then top function inside it | Worse than an **alphabetical** null ranker | **Dead** |
| Competitor catch rate, 10/65 | 15.4%, Wilson **8.6–26.1%** — spans the 23.9% comparison | **Withdrawn**, because it named a company |
| "Function ranking is a floor" | Reasoned from partition fineness, ignoring that aim differs (75.0% vs 58.9%) | **Withdrawn** |
| Claim checkability from review text | Keyword classifier, **56.5%** residual | **Discarded.** The residual *is* the result — see below |
| **Does the ranker predict where a human reviewer commented?** | 69 pre-2022 PRs. History top-3 **69.6%**, alphabetical **72.5%**, exact chance **69.1%**. McNemar p = 0.81 | **Null**, and the instrument was half the problem — see below |

**On the human-attention null, two things must be said in order.** First the result: the
model-free ranker shows **no advantage over an alphabetical control, and none over exact chance**,
at predicting which file a human reviewer chose to comment on. That was a pre-specified test and
it failed.

**Second, the test was badly built, and saying so does not rescue it.** Admitting pull requests
with as few as 4 changed files put the chance baseline at **79.7%** — top-3 of 4 files is not a
selective instrument. Across the whole sample chance was 69.1%, so there were 31 points of
headroom for two policies to compete in. This is the same defect as the certification threshold:
**an instrument asked to resolve something it cannot see.** A properly powered version admits
only pull requests with enough files for top-3 to mean something, and it needs a fresh sample —
re-cutting this one after seeing the answer is the failure mode the whole project is built to
avoid.

**A post-hoc stratum, labelled as such and not usable as evidence.** Among the 24 PRs with 9–15
changed files, where chance falls to 51.9%, history scored 58.3% and alphabetical 54.2%. That is
a hypothesis. It is not a result, it was not pre-specified, and n = 24.

**What the null does not touch.** The +22-point ranking result targets *the function a later fix
returns to*. This test targeted *the file a human commented on*. They are different quantities,
and the corpus work says why they might not coincide: **only 5.9% of human review comments assert
anything structurally checkable**, so where reviewers comment is mostly not where defects live.
That reconciliation is coherent and rests on an independently measured number — **and it was
constructed after seeing the null, so it is an explanation, not a finding.**

**Seven nulls is the asset, not the embarrassment.** Every one of them is a feature a competitor
could ship tomorrow with a straight face, and each was killed here by a control the competitor
has no reason to run.

---

## 3. What no measurement touches

These are the claims currently carried by architecture or by argument. Each is defensible; none
is measured; and the distinction has to survive contact with a customer asking "how do you know".

| Claim | What currently supports it | What would measure it | Blocked by |
|---|---|---|---|
| **The coverage line is honest** | Construction. `Unresolved(site, reason, construct)` cannot be built without all three fields, and `CoverageLine` is a view over its `Ranking` so it cannot disagree with what was funded | A live run whose stated coverage is checked against what was actually read | Nothing — this is buildable now |
| **Verification catches the model's bad claims** | Design. `verify` cannot import `infer`, enforced by the layer guard | Precision and recall of the verifier against hand-adjudicated model output | **No model has ever run** |
| ~~**Our published findings are trustworthy**~~ | **MEASURED, AND FALSE.** 66.7% / 74.2% wrong across two blind raters, κ = 0.82 on the binary; 4.5% correct by consensus against a 49% field floor | — | — |
| **It makes pull requests move faster** | Nothing. The market data says review latency is the bottleneck; it does not say we fix it | One month, three teams, cycle time before and after | **No customers.** This is the VP question and it has no answer |
| **85% gross margin at 300 PRs/month** | Derived from the cost line, which is now measured | Inherits — recompute against the billed figure | Nothing; arithmetic |
| **Claude vs Gemini for the inference pass** | Nothing | Adjudicated disagreements, exact binomial at pre-specified n | Same — and the instrument resolves **22 points at n = 100**, not the 2 the rule originally asked for |

**The structural claim that replaced a measurement.** The checkability classifier failed at 56.5%
residual, and the failure carried information: review content is **not keyword-shaped**. *"i think
the return type is a dictionary"* is a structural claim with no token to key on. Human review is
**5.9% structural** by the generous pattern, on a seven-year window with bots removed. So stage
four does not try to detect structure in prose — it adjudicates the fields **the schema forces**
(`claim_type`, `file`, `line_a`, `line_b`, `relation`), which makes every finding checkable by
construction. The open question is no longer *what fraction of review claims are checkable* but
**what fraction of useful findings survive that form without distortion** — answerable from the
worked example before any model runs, and not yet answered.

---

## 4. The gap, stated once

Ten measurements support the **ranking**. Zero measurements support the **review**.

That is not an accident of sequencing — it is what made the project buildable. The ranker is
model-free, so it could be measured against seven years of history before a single API call. The
review cannot be measured that way, because it does not exist until a model runs.

**The consequence for what may be said:** every claim about *where we look* is defensible today.
Every claim about *what we find* is a claim about software that has not run. The coverage line is
the product's honest half and it is the measured half — which is fortunate, because it is also
the half being sold. But a customer who hears "we tell you what we could not read" and infers
"and what we did read, we got right" has been allowed to make an inference the evidence does not
support, and correcting that inference is on us.

**Ordered by what unblocks the most:**

1. **A configured API key.** It unblocks cost, model choice, verifier precision, and the
   published-and-wrong rate — five rows above, one dependency.
2. **One live end-to-end run with a reviewed golden file.** It converts "the coverage line is
   honest by construction" into "the coverage line was checked against what was read."
3. **The worked example through the schema**, answering what fraction of useful findings survive
   the structural form. Costs nothing and needs no model.
4. **Three teams for one month.** The only thing that answers the VP question, and the only one
   that cannot be bought with engineering time.

---

*Re-check the counts in this file whenever a measurement lands. A ledger that drifts is worse
than no ledger, because it is trusted.*
