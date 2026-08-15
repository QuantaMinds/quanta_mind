# The evidence ledger

Every measurement this project has run, against the claim it is supposed to carry. One row per
measurement, and the last column is the only one that matters: **does the evidence reach the
claim, or is there a gap that argument is currently covering?**

This exists because the numbers were produced over months in different harnesses, and a figure
that was honest when measured drifts into carrying weight it cannot hold. `publishing-rules.md`
governs what may be said; this file governs what is *known*.

**The one-sentence summary, stated before the detail so it cannot be buried:** the half of the
product that decides *where to look* is measured and holds up; the half that decides *what to
say* has never run. Everything below elaborates that split.

---

## 1. What is measured, and holds

| Measurement | n | Result | Claim it carries | Reaches it? |
|---|---|---|---|---|
| **Ranker names the repaired function** | 53 verdicts, 2 raters | 69–70% on repairs vs 47–48% on non-repairs, **+22 points**, Fisher p = 0.0151 | "We are right about where to look" | **Yes.** Replicated by an independent rater at 92% agreement, Cohen's κ = 0.92, same effect size to within a point |
| **Firing rate holds across velocity** | repos differing 80× | **10–12%** everywhere, via a percentile rather than a threshold | "Quiet" | **Yes.** The percentile is what makes it hold; a fixed threshold fired on 11% of one repo and 53% of another |
| **Three units cover the change** | 1,969 paired events, 8 repos | file top-3 misses **1.22%**; function top-3 misses **8.84%**; five units miss 3.50% | "Three units miss at most 8.84%" | **Yes, with a named proxy.** See the caveat below |
| **File-level allocation beats function-level** | same 1,969 | +7.62 points, McNemar exact **p < 0.0001**, discordant b = 157 / c = 7 | The allocation choice in the architecture | **Yes** |
| **The competitors' attribution rule is wrong** | 53 verdicts, 3 corpora | **67.9%** of verdicts blame a change sharing no symbol with the fix; survival 32.1%, reproduced at 36.1% and 35.7% | "Two thirds of what a file-overlap reviewer blames is not what broke" | **Yes.** The strongest result here |
| **Leaking the future degrades the ranker** | corpus-wide | top-1 moved **50.0% → 37.5%** when future commits were visible | The index is genuinely bounded by the past | **Yes — and this is a known-answer test**, not a result. It is how we know the harness measures anything |
| **Six allocation variants against controls** | 1,969, pre-specified, held-out | **V0 (file top-3) still standing**; V2 not significant (train p = 0.18, holdout p = 0.125) | That the shipped policy is the best of those tried | **Yes**, and the holdout caught V2 overfitting on its first use |
| **Bot prevalence in OSS review** | 5,195 comments, 8 repos | **31.5%** bot-written, 0.0% to 92.0% by repository; bot output **52.9%** structural vs human **5.9%** | Corpus hygiene — and the argument for schema-forced structure | **Yes**, as a floor. The detector is a login-and-marker match, so undetected bots bias it down |

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
| **Our published findings are trustworthy** | Nothing yet | Published-and-wrong rate on real PRs | Same |
| **It makes pull requests move faster** | Nothing. The market data says review latency is the bottleneck; it does not say we fix it | One month, three teams, cycle time before and after | **No customers.** This is the VP question and it has no answer |
| **$0.140 per review, $28/repo/month** | Token arithmetic on real diffs — but priced, not billed | The same diffs through a real API with billing attached | **No key configured** |
| **85% gross margin at 300 PRs/month** | Derived from the line above | Inherits | Same |
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
