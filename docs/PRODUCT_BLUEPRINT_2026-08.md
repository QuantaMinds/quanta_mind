# QuantaMind code review — product blueprint

**Written 2026-08-12.** A full-surface code review product built without inference, and the
evidence for and against every claim it makes. Measurements come from
`docs/findings/SIGNAL_SEARCH_LOG_2026-08.md` and
`docs/findings/HISTORY_SIGNAL_BACKTEST_2026-08.md`, both produced against live clones.

Each claim below carries a status: **MEASURED** (produced by code in this repository),
**VERIFIED** (read from a vendor's own documentation), or **UNVERIFIED** (asserted, not
tested). Nothing marked UNVERIFIED may appear in a pitch, a page, or a product comment.

---

## The idea the whole product rests on

**Every competitor spends its analysis budget uniformly across the diff. We spend ours where
a measured signal says it matters.**

The defects in this corpus are semantic. Published work reports **semantic errors account for
over 60% of faults** in model-generated code, and this corpus agrees independently: of the
breakages we could trace, **every one required re-editing a file the pull request had already
changed**, and **none** was fixed by adding a missing file alone. Judging whether logic is
correct means reading the logic, and that requires a model.

So we use one — but not the way they do. CodeRabbit and Graphite feed the whole diff to an
LLM at uniform depth, which is why they cost what they cost and why an independent audit found
**36% of CodeRabbit's comments were noise or nitpicking**. Reading everything equally is
simultaneously the source of their token bill and the source of their noise.

**We rank first, then read.** A deterministic pass computes coverage, structural breaks, and
the attention ranking. The ranking then decides where inference goes: deep, multi-pass
analysis on the one or two units the history says changes come back to, and nothing at all on
the cold files.

Three consequences, and each is a competitive property rather than a feature:

| | |
|---|---|
| **Cost** | Inference on a fraction of the diff, so lower cost per pull request at equal or greater depth on what matters |
| **Noise** | We comment where we looked hard. Not commenting on cold files is structural, not a tuning parameter |
| **Depth** | The saved budget buys a stronger model and more passes exactly where the risk concentrates |

The deterministic layer is not a substitute for the model. **It is the allocator that makes
the model affordable and quiet.**

---

## Part 1 — The form factor

A reviewer that posts on one pull request in ten looks broken next to one that posts on all of
them. So the product posts on **every** pull request, and separates two things no incumbent
separates: **what it checked** and **what it found**.

```
QuantaMind

Checked      12 of 14 files · 41 call sites resolved
Could not    dynamic dispatch in handlers/registry.py — 2 files unresolved
Found        no signature breaks, no dangling references

Read first   refunds/service.py
             changed 34 times in the last year, the most of the 6 files here
```

Three properties, none of which any shipping reviewer has together:

- **A coverage line that is honest.** What was analysed, and what was not, with the reason.
- **A findings line that is usually empty**, and says so plainly rather than padding.
- **One routing line**, never more.

**Silence discipline: at most one finding per pull request.** Research on change prediction
at function level supports this directly — method-level prediction beats coarser prediction
**specifically when the acceptable number of recommendations is small.** Firing rarely is the
regime where the technique works, not a limitation of it.

---

## Part 2 — The four pillars, with evidence and with limits

### Pillar 1 — A cost structure they cannot match, and a free tier that costs us nothing

**Status: VERIFIED on the competitor side; the allocation saving is UNVERIFIED until measured.**

CodeRabbit and Graphite bundle inference and read the whole diff, so tokens sit in their cost
of goods and scale with every line reviewed. Their pricing reflects it: CodeRabbit $24–48 per
seat with enterprise from $15,000/month at 500+ seats; Graphite $20–40 per seat.

We split the product in two, and the split is the business model:

**Free tier — deterministic only, and genuinely zero marginal cost.** Coverage line,
structural checks, attention routing. No model, no key, unlimited seats and repositories,
permanently. Our cost is compute — a clone, a parse, a git walk — which is **two to three
orders of magnitude below a token bill**, not zero. The first analysis of a large monorepo
takes minutes; after that it is incremental.

**Paid tier — inference, spent where the ranking points.** The same deterministic pass now
allocates a model budget instead of just printing a hint.

This resolves the open-core problem that free-forever products usually have: the free tier is
free **because it genuinely costs nothing to serve**, not because we subsidise it, and the
paid tier is where the only real cost lives. Adoption and cost of goods scale independently.

The distribution precedent is in our market research — Kodus shipped free with a required key
and reached 1,306 stars in 17 months; CodeGraph shipped free with no key and reached 66,097 in
seven. **The friction, not the price, was the variable.** We have no key in the free tier.

**What must be measured:** the actual token saving from targeted allocation, against uniform
review of the same diffs. Until that number exists, "cheaper than CodeRabbit" is a hypothesis.

### Pillar 2 — Typed silence

**Status: VERIFIED. This is the strongest pillar and the only uncontested one.**

Checked across seven shipping reviewers: **not one can report that it failed to analyse
something.** Cursor documents the collapse in its own words — `neutral` means "found issues,
was cancelled, **or hit an internal error**" — and states outright that Bugbot emits no
`skipped` conclusion. Qodo filters "anything low-confidence before it reaches the pull
request." The one tool that typed absence correctly, BreakBot, is dead: 8 stars, last push
2023-12-16.

**Incumbents structurally cannot copy this.** Publishing a blind spot contradicts a precision
claim, and their precision claim is their marketing.

This is also the one pillar that costs nothing to build: we already emit `Unresolved(site,
reason, construct)` records, and the repository's third non-negotiable already requires that
"no edge here" and "we failed here" never be the same value.

### Pillar 3 — Attention routing

**Status: MEASURED, and narrower than it sounds.**

Rank the files a pull request changes by how many commits touched each in the prior year, and
name the top one.

| | |
|---|---|
| Events | **4,293** across **17 repositories** |
| Ranker top-1 | **85.3%** |
| Alphabetical null ranker | 72.0% |
| Random baseline | 67.5% |
| Repositories where the ranker beats its null | **17 of 17** (sign test p ≈ 1.5 × 10⁻⁵) |

On the corrected agent-pull-request labels it was 9 of 9 against a 46.5% baseline, exact
Poisson-binomial P = 0.00042, and on the noisier discovery labels 17 of 30 against 35.2%,
P = 0.00638. It is **not** "the biggest edit" — ranking by lines changed in the pull request
scores *worse* than random.

**What must never be claimed.** This predicts **where a fix lands, given that something
breaks**. It has **no power** to predict whether a pull request will break: the same history
signal tested as a breakage predictor was **null — RR 1.56, p = 0.334, firing on 36% of clean
pull requests.** Any copy that says historical data "proves this file will break" is
contradicted by our own measurement.

The honest sentence is: *"of the six files here, this is the one changes tend to come back
to."*

**And it is cheap to copy.** It is `git log --since=1.year -- <file>` counted and sorted.
There is no algorithmic moat — only that nobody puts it in the pull request. That is a
distribution claim and should be described as one.

### Pillar 4 — Deterministic structural checks

**Status: sound in principle, and "zero false positives" is false.**

Two checks a parser can decide: a changed public signature whose call sites elsewhere were not
updated, and a removed or renamed symbol still referenced.

**The zero-false-positive claim must be struck.** This company's founding premise is that
static analysis is unsound by design; claiming perfect precision contradicts the thesis we
sell. Concretely, our reference-finding proxy located a fix target **1 time in 5** while
flagging **19% of the repository's files**. Duck typing, `getattr`, decorators, keyword
arguments and dynamic dispatch make static call-site enumeration incomplete in Python — which
is exactly why the coverage line in Pillar 2 exists.

**Correct framing:** these checks are *deterministic*, meaning they never hallucinate and
always give the same answer. They are **not complete**, and the product says so on every pull
request.

---

## Part 3 — Claims removed from the draft blueprint, and why

| Claim | Why it is out |
|---|---|
| *"file `database.py` holds 84% of past churn"* | The number does not exist. 85.3% is the ranker's top-1 accuracy across 4,293 commits — a different quantity. A fabricated statistic inside the product's own output is the one place we cannot afford one |
| *"historical data proves will break"* | Contradicted by our own null: hotspot history does not predict breakage, RR 1.56, p = 0.334 |
| *"zero false positives"* | Contradicts the company premise and the 1-in-5 proxy result |
| *"< 1.2s"* | First analysis of a large repository is minutes. True once incremental |
| Rust and macro examples (`legacy_parser.rs`, `auth_macro!`) | The instrument is **Python only**. Multi-language is a roadmap item with real cost, not a property we have |
| *"Compliance ledger via Sentry/Datadog webhooks"* | Sentry and Datadog already ship suspect-commit attribution with auto-assignment. Building the same join is entering an occupied position |

---

### Pillar 5 — Findings a model produced, checked by a parser

**Status: UNVERIFIED, and it is the pillar most worth building.**

An LLM reviewer's central weakness is that nothing checks it. Field precision runs 50–76%, and
a confident wrong comment is indistinguishable from a right one at the moment a developer
reads it.

Some model findings are **mechanically checkable against the same deterministic layer that
allocated the budget**: a claimed signature break can be confirmed against the parsed
signature; a claimed dangling reference can be resolved or not; a claim about a caller can be
matched against the reference set. Findings that verify get posted plainly. Findings that
contradict the parser get dropped before a human sees them.

That produces something neither competitor can state: **a reviewer whose structural claims are
checked before publication.** It is also the natural home for the correction discipline this
repository already runs on itself.

---

## Part 4 — Monetisation

Free tier is the deterministic engine, unlimited, no key. Revenue comes from inference depth
and from the organisation, not the developer.

**What the draft priced at $499–$2,000/month is too low for what it contains.** Air-gapped
deployment, custom rules, and audit evidence are procurement-heavy, security-reviewed
purchases; buyers price them against a $15,000/month competitor, not against a per-seat tool.
The enterprise tier should be a five-figure annual contract.

The strongest paid offering is **not** in the draft, and it is the one thing in this
repository that has replicated three times:

> **The attribution audit.** Every dashboard a buyer uses today attributes rework with a
> file-overlap rule that is wrong on **67.9%** of its verdicts — 36 of 53 verdicts share no
> symbol with the pull request they are attributed to, reproduced at 36.1% and 35.7% survival
> on two further corpora. We can price a buyer's AI tooling spend against what it actually
> catches. **No vendor can do this about itself**, which is why the position is durable and
> the routing feature is not.

Free engine for distribution. Audit for revenue.

---

## Part 5 — Architecture

```
pull_request webhook
      │
      ├── git log walk          → prior-year churn per changed file   (Pillar 3)
      ├── tree-sitter parse     → public signatures, symbol references (Pillar 4)
      ├── resolution pass       → what could not be resolved, and why  (Pillar 2)
      │
      └── one markdown comment + one check run
```

No model. No customer key. Read-only on code, write-only on a comment. The coverage line is
produced by the same pass that produces the findings, so it can never drift from them.

---

## Part 6 — What must be measured before launch

Two numbers decide whether this is a product, and neither exists:

1. **Does a human act on the routing line?** Top-1 accuracy against historical fixes is 85.3%.
   Whether a reviewer reading that hint *before* the bug exists catches something they would
   otherwise miss is **UNVERIFIED**, and it is the entire commercial risk. Measure it in
   shadow mode on three real repositories for one month.
2. **Does symbol granularity beat file granularity?** Interim over the first five
   repositories, and it favours symbols once the right metric is used. Absolute accuracy is
   lower at symbol level because there are more candidates and a lower baseline, so the
   comparable quantity is **lift over each granularity's own null ranker**:

   | Repository | File lift | Symbol lift |
   |---|---|---|
   | 567-labs/instructor | +17.1 | +14.5 |
   | BeehiveInnovations/zen-mcp-server | +5.8 | **+18.9** |
   | DannyMac180/meta-agent | +1.2 | **+18.7** |
   | Ljzd-PRO/KToolBox | +11.3 | **+17.4** |
   | MontrealAI/AGI-Alpha-Agent-v0 | +10.3 | **+18.4** |

   Symbol lift is **consistently near +18 points**; file lift ranges from +1.2 to +17.1.
   Symbol counts are smaller, so intervals are wider, and the run is incomplete. **If this
   holds, symbol granularity is the differentiator claim and it survives** — CodeScene and
   CodeRabbit both operate at file level.

---

## What would falsify this blueprint

- Reviewers ignore the routing line in shadow mode.
- Symbol granularity fails to beat file granularity, **and** file-level routing turns out to
  be indistinguishable from what CodeRabbit's existing co-change map already provides.
- A free unlimited tier fails to convert into enterprise audit revenue, leaving a product with
  adoption and no business model.
- Someone ships typed silence first. It is the cheapest pillar to build and the only one no
  competitor can answer.
