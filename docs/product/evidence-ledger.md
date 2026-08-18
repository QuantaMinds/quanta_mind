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
| correct | 9.1% | **4.5%** | 3 of 66 by consensus |

**The threshold was 50% wrong, committed before a single finding was read. Both readings clear it,
and every disagreement between them made the result worse rather than better.** The reading is:
stop building the review half in this configuration. `docs/plans/preregistrations/reviewer/adjudication-preregistration.md`
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

**The rerun has now run, and it returned a second null.** 44 pull requests, five fresh
repositories, an instrument selective enough to detect an effect (chance 36.6%): history 40.9%
against an alphabetical control at 50.0%. Pre-registered reading: **NULL**.

**Which fixes the sentence this ledger has to carry, and it is the sharpest one in the file:**

**That question has now been run, and it CONFIRMED.** 2,400 events across the six fresh
repositories, every parameter copied from the original harness rather than re-picked, reading
fixed in advance:

| | history | alphabetical control | lift |
|---|---|---|---|
| original 8 repositories, n = 1,969 | 1.44% | 3.31% | +1.87 |
| **fresh 6 repositories, n = 2,400** | **1.21%** | **3.12%** | **+1.92** |

**McNemar exact p < 0.000001, discordant b = 62 / c = 16, and 6 of 6 repositories positive.** The
two lifts differ by **0.05 points**. This is the first result in the project to reproduce
out-of-sample.

**With the honest qualifier attached: scrapy roughly doubles the effect.** Excluding it the lift is
**+0.90** and p = 0.011 — still significant, and the conservative end of the range to quote. Only
scrapy is individually significant; at a ~1% miss rate 400 events give too few discordant pairs to
test a single repository, so repositories are counted rather than tested.

**So the sentence this ledger carried an hour ago is now wrong and is replaced:** the ranker beats
an alphabetical control at defect-return **on fourteen repositories across two disjoint samples,
one of them pre-registered and out-of-sample**. It still predicts nothing about where human
reviewers comment, which failed twice — those are different targets and only defect-return is
claimed.

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
| **…rerun, properly powered, 5 fresh repos** | 44 PRs, 9–30 files each (chance 36.6%). History **40.9%**, alphabetical **50.0%**, H−X **+4.3**, McNemar p = 0.48 | **NULL**, pre-registered. Second null, and history lost to alphabetical **both** times |

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

---

## 1b. The pooled pattern across all 207 adjudicated findings

**Six designs, three corpora, one table, computed without a hypothesis first.**

| factor | spread in wrong-rate | p |
|---|---|---|
| **repository** | pandas 96.3% → ansible 36.4%, **+59.9 pts** | < 0.0001 |
| **design** | line anchors 82.1% → execution gate on easy 27.8%, **+54.3 pts** | 0.0001 |
| **corpus** | hard 71.9% → easy 27.8%, **+44.1 pts** | 0.0002 |
| **claim type** | wrong_order 73.9% → resource_leak 33.3%, **+40.6 pts** | 0.0016 |
| **function size** | >60 lines 85.7% → ≤20 lines 57.6%, **+28.1 pts** | 0.0032 |
| test vs source | 68.5% vs 61.5%, +7.0 pts | 0.29 — **nothing** |
| lines touched | +4.4 pts | 0.61 — **nothing** |

**Function size is the one actionable factor and it was never tested for.** Finer buckets:

| function length | wrong | correct |
|---|---|---|
| ≤10 lines | **45.9%** | 10.8% |
| 11–20 | 66.7% | 4.2% |
| 21–40 | 62.3% | 6.6% |
| 41–80 | 69.7% | 3.0% |
| **>80 lines** | **89.3%** | 3.6% |

**And the repository effect is largely function size wearing a repository's name**: correlation
between a repository's median function length and its wrong-rate is **r = +0.65**. pandas has a
median funded unit of 98 lines and a 96.3% wrong-rate; scrapy has 22 lines and 51.4%.

**It is not monotonic in the middle**, and within the hard corpus the ≤20 band (73.6%) is worse than
21–60 (63.2%), so this is a real effect at the extremes rather than a clean dose-response. **It is
a diagnosis, not a detector.**

**Two factors that carry nothing**, recorded because both were plausible and one was proposed
explicitly: whether the unit is a test (p = 0.29) and how many lines the change touched (p = 0.61).

## 1c. The published benchmark says the same thing, at ten times the sample

[SWR-Bench](https://arxiv.org/html/2509.01494v1) — 1,000 pull requests, five automated code-review
techniques:

| technique | precision |
|---|---|
| PR-Review | 15.39% |
| LLM-Reviewer | 9.22% |
| SWR-Agent | 9.11% |
| CR-Agent | 6.23% |
| Hybrid-Review | 2.79% |

**Ours: 5.80% across all 207 findings, 2.22% on the hard corpus, 12.96% at the best single
design. We land inside their range, near the middle.**

Their conclusion, in their words: *"A primary factor limiting higher F1 scores for all techniques
is their low precision, indicative of a high false positive rate… SOTA ACR techniques, when paired
with SOTA LLMs, are not yet ready for real-world code review deployment."*

**This is the single most important external check in this document.** Six designs failed here, and
the field's own benchmark shows five published systems failing the same way at the same magnitude
on ten times the data. **The review half is not badly built. It is a problem nobody has solved**,
and the evidence that we are not merely incompetent is also the evidence that we should not be
spending on it.

---

## 1d. Is the model's ATTENTION worth anything, even when its claims are wrong?

**The question every adjudication was unable to ask.** A rater judges whether a sentence is true of
the code in front of them. None of them can see whether that code later broke. So a reviewer whose
claims are 65% wrong might still be *pointing at the right code* — and that would be shippable with
the prose thrown away.

**The aged corpus can answer it**, because every pull request in it predates the outcome window by
more than a decade.

| | funded units | a later fix returned within 90 days |
|---|---|---|
| the model **spoke** | 30 | **30.0%** |
| the model was **silent** | 10 | **40.0%** |

**−10.0 points, Fisher exact p = 0.70. Null, and pointing the wrong way.**

**The instrument is weak and that is stated rather than buried**: with 30 against 10, the smallest
detectable difference is roughly **+40 points**. A real but modest signal would be invisible. This
is a null on a test that could only have seen something very large.

**But the number underneath it is the useful one.** All 40 units were *ranker-funded*, and **13 of
40 — 32.5% — had a later fix return to them.** That is the ranker's hit rate on this corpus. The
model's decision to speak moves it to 30.0%.

> **The location signal belongs to the ranker. The model adds nothing on top of it.**

That is the cleanest statement of the split this project has been circling: **the model-free half
selects the code that later breaks, and the model half neither improves that selection nor
describes it correctly.** Which is precisely why the product is the allocator and the coverage
line, and not the reviewer.

---

**Seven nulls is the asset, not the embarrassment.** Every one of them is a feature a competitor
could ship tomorrow with a straight face, and each was killed here by a control the competitor
has no reason to run.

---

## 2a. Expansion removed its failure class; a second class dominates the total

Design thirteen, pre-registered in
`docs/plans/preregistrations/reviewer/expansion-conventions-preregistration.md`, added the two
mechanisms Qodo ships and this project discarded. Six unused repositories, 80 reviewable pull
requests, three arms, blind adjudication, **10 of 10 sabotaged controls caught.**

| claim | what was measured | verdict |
|---|---|---|
| Expansion removes the "did not follow shown code" failure | 73.3% → **18.8%** of wrong findings | **HOLDS** (H1, bar ≥15 points, got 54.6) |
| Expansion lowers the overall wrong-rate | 51.7% → **59.3%** [40.7, 75.5], bar ≤30% | **FAILS** (H2) |
| A rules file makes convention-policing worse | arm C **12.6 points better**, not worse | **THE HARM DID NOT APPEAR** (H3) |
| …and that gain is accuracy | **it is not** — WRONG −2 but UNFALSIFIABLE +4, CORRECT +1; CORRECT-rate 6.9 → 7.4 → 10.0% with overlapping intervals | **HEDGING, NOT ACCURACY** |
| Either mechanism starves the reviewer | yield 0.41 / 0.40 / 0.46, bar ≥0.30 | **HOLDS** (H4) |

**H1 and H2 are different lessons and must not be collapsed.** Expansion did the one thing it was
built to do; the total did not move because **CI-config findings are 66.7% wrong [50.3, 79.8] and
23 of those 24 are EXTERNAL** — undecidable from a diff by construction. **Every one checked
against GitHub was false.** The "future" dates read Aug 14–17 2026 against a run on **Aug 18 2026**
— three days in the past, which is a model with no notion of the present rather than a stale
training cutoff, and no path filter ends it.

**Excluding CI config is the third application of the decidability rule, not a discovery.**
Lockfiles, manifests and docs went first. `.github/` was kept deliberately at ~25% CORRECT; the
evidence turned over, not the principle.

Off CI config the wrong-rate runs 52.2 → 38.5 → 28.6%, but that is **post-hoc with intervals that
overlap almost completely at n = 13 and n = 14** — consistent with the mechanisms working and
equally consistent with noise.

**This does not count toward replication.** The rater designed the run. Arm labels were blind and
every planted control was caught, but designer bias is unguarded — **four designs now owe an
independent grader.** Design 11's arm R cleared yield at 0.40/PR but is unadjudicated, so the
**replication count stays at two**; arm E failed yield at 0.22/PR before adjudication ran.

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

**Two datasets support the ranking. The review was measured and failed.**

That is the corrected form of a sentence this project repeated for weeks as "ten measurements
support the ranking and zero support the review". The count was inflated — see *"Ten measurements"
is a count, not a weight* above — and the second half is now out of date in the worse direction:
the review half is no longer unmeasured, it is measured and below its own pre-registered bar.

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
