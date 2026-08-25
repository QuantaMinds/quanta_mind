# What it would take to ship the reviewer, costed — and what that means for the business

Written 2026-08-23, against the two verifiers the closure named as the only things that would
reopen it. **The conclusion is that one of them is a business asset and neither is a rescue.**

## The arithmetic that binds, before any product framing

All 207 adjudicated findings, six designs, three corpora:

| verdict | n | share |
|---|---|---|
| WRONG | 135 | 65.2% |
| UNFALSIFIABLE | 36 | 17.4% |
| TRIVIAL | 24 | 11.6% |
| **CORRECT** | **12** | **5.8%** |

**A verifier deletes wrong findings. It cannot create right ones.** So the ceiling of a *perfect*
verifier for BOTH classes is fixed by what is already in the pool:

| scenario | findings left | C/n |
|---|---|---|
| today | 207 | 5.8% |
| perfect EXTERNAL **and** SEMANTIC verifier — all 135 WRONG gone | 72 | **16.7%** |
| ...also dropping every UNFALSIFIABLE | 36 | 33.3% |
| ...also dropping TRIVIAL, so only CORRECT survives | 12 | 100% |

**The field floor is C/n ≥ 49%. A perfect verifier on both classes lands at 16.7% — short by 32.3
points.** The best correct-rate any of six designs has ever produced is **13.0%**, and the design
with the best *wrong*-rate — the execution gate, 27.8% — scored **11.1% correct**, which is worse
than the line-anchor baseline's 13.0%. **It deleted; it did not create.** That is the same D/L
trade five prompt levers produced, arriving through a different door.

**Yield is the number that settles it: one useful comment per 27 to 77 pull requests.** No filter
moves that, because the filter's whole job is removing things.

## The August 2026 literature says the same thing, from outside

`Refute-or-Promote` (arXiv 2604.19049) is the closest published work: adversarial kill mandates
plus a cross-model critic, over a 31-day campaign across 7 targets.

**THE MECHANISM TRANSFERS; THE NUMBER DOES NOT, AND AN EARLIER DRAFT OF THIS PAGE QUOTED IT AS IF
IT DID.** Their 79% is a kill rate on **171 vulnerability-discovery candidates before disclosure**
— roughly five a day across seven targets — with 83% on a consolidated-protocol subset of n = 30.
Our ~85% bar is for a judge filtering **per-pull-request review findings**. Different task,
different population, **not commensurable**. Citing one as the other is the same defect as
Macroscope's 55%, which is comment volume and not a false-positive rate.

What does transfer is the mechanism, and two findings in it matter more than any rate:

- **"Ten dedicated reviewers unanimously endorsed a non-existent Bleichenbacher padding oracle...
  it was killed only by a single empirical test."** A ten-model ensemble ratified a hallucination.
  Our same-family judge agreed with a careful rater on 34.9% and ratified our reviewer's invented
  facts. **Ensembling model judges does not fix this; only running something did.** The paper
  reaches our cross-family argument independently — cross-family review catches correlated blind
  spots same-family review misses — with empirical validation as the mandatory final gate.
- **"No vulnerability was discovered autonomously; the contribution is external structure that
  filters LLM agents' persistent false positives."** Stated by the authors, about their own work.

The paper reports **no baseline precision**, so its kill rate is not a measured trade.

Its shape also confirms the campaign framing below: 31 days, 7 targets, 171 candidates → 4 CVEs,
LWG 4549 accepted to the C++ working paper, 5 merged editorial pull requests, 3 compiler
conformance bugs, 8 merged security fixes without a CVE. **That is an engagement, not a
subscription.**

## THIRD-PARTY MEASURED — what shipping at this precision does to the receiving end

**This is the strongest external evidence for the closure, and it is a consequence rather than a
score.**

- **curl permanently closed its bug bounty**, effective 1 February 2026. Confirmed-vulnerability
  rate had historically run **north of 15%; from 2025 it fell below 5%.** In the first 21 days of
  2026: **20 submissions, seven inside one 16-hour window, and zero actual vulnerabilities.**
- **HackerOne paused the Internet Bug Bounty** to new submissions from **27 March 2026**, citing
  AI-expanded discovery outpacing maintainers' capacity to remediate, with valid submissions
  likewise falling from ~15% to below 5%.

**PROVENANCE, AND IT MATTERS:** what these measure is **a bug bounty programme's confirmed rate** —
the share of *submissions* that were real vulnerabilities — **not a review tool's precision.**
Different population, different task, and the numbers are not ours to quote as a like-for-like
comparison. That is exactly the provenance error this project has made three times.

**What they do establish is the consequence.** Our correct-rate on 207 adjudicated findings is
**5.8%**, and sub-5% is the number that closed a bug bounty permanently and paused another.
Maintainers described the influx as a denial-of-service attack. **A reviewer shipped at our
measured precision is not a weak product; at volume it is a burden on the people receiving it** —
observed in the wild, at scale, with named consequences. The cause, in the literature's own
framing: **LLMs are optimised for plausibility, not correctness.**

## The CEO constraint, and it is the one thing here that is an asset

**The external-fact verifier cannot be built generically, because we do not have the facts.** For a
business customer, "a fact outside the code" is not *does this npm tag exist* — it is *which team
owns this service, what its SLO is, whether this endpoint is deprecated, which incident this path
caused, what the ticket actually asked for.* **Only the customer has those, and they arrive as
their Jira, their Datadog, their internal docs.**

Three consequences, and they run in opposite directions:

1. **It cannot be measured before an engagement.** No public benchmark contains a company's
   internal facts. Neither ours nor anyone else's numbers can be quoted for it.
2. **It is a moat precisely because it does not generalise.** A generic reviewer cannot do this at
   any model quality. A reviewer wired into a customer's systems is doing something no benchmark
   score is available to beat.
3. **It is 28 of 45 wrong findings and it does not touch the other 17.** `TRACE` is semantic, and
   the August 2026 result stands: LLMs fail to re-localise a fault they had localised correctly in
   **78%** of cases under semantic-preserving rewording.

**So the external verifier is a real differentiator and a partial fix. It is not a rescue, and the
16.7% ceiling above already assumed it works perfectly.**

## What a CEO should actually sell

**Do not sell a per-pull-request reviewer.** One useful comment per 27–77 pull requests is not a
subscription; it is noise with a bill attached, and the arithmetic above says no amount of
verification changes that.

**Sell the ranker, which is measured and replicated** — 1.53% miss against alphabetical's 2.97%,
20 repositories, three disjoint samples, p = 1.3 × 10⁻¹⁴. It is the only thing here that reproduced
out-of-sample.

**Take the customer's Jira and Datadog for what the record says they are worth — validating the
ranker, not rescuing the reviewer.** The ranker is currently validated against a proxy where
**the label is known to be contaminated** — roughly **86% of symbol-overlap pairs** are not
genuine repairs by blind labelling. **85.3% is the ranker's top-1 hit rate, not a contamination
rate.** → `docs/CORRECTIONS.md` entry 11 Datadog incidents are the outcome itself.
Jira bug-links are a label independent of commit-message wording. **The founding correlation test
died on a proxy (RR 1.040)**; an independent label is what stops that recurring. This is the
on-thesis use and it upgrades the half that works.

**If the reviewer ships at all, ship it as a campaign, not a subscription.** That is the shape the
literature's yield actually supports: point the engine at one repository, kill ~80%, surface a
handful of real defects, charge for the engagement. Refute-or-Promote's own output was 4 CVEs,
5 merged pull requests and 3 compiler bugs — valuable, and nothing like a per-PR product.

## The one measurement worth buying, and it is not a verifier

**Execution.** It is the only mechanism in either our record or the August 2026 literature that has
ever killed a false finding no model judge would kill — the padding-oracle case was killed by a
test, and our execution gate produced the best wrong-rate of six designs. **It is also the only
candidate for the `TRACE` class, which nothing else touches.**

It has never been measured as a trade here: our execution arm ran on n = 18 with 2 correct
findings, which is too small to say anything. **Pre-register it with a bar fixed first, and require
it to beat the ranker — which is free.**
