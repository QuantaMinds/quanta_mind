# Competitive landscape — August 2026

**Retrieved 2026-08-12 by live web search.** Verification statuses match
`MARKET_POSITION_2026-08.md`: **VERIFIED** (vendor docs / API / primary source),
**QUOTED** (verbatim, checked), **REPORTED** (secondary source, named, not independently
confirmed), **UNVERIFIED**.

Read `MARKET_POSITION_2026-08.md` first. That file establishes the position; this one
surveys who else is in the market, what each does well, where each is weak, and the one
structural gap none of them can close.

---

## The market, in one table

| Company | Money | Price | Best at | Weak at |
|---|---|---|---|---|
| **CodeRabbit** | **$143M at $1.5B** (2026-08-12); $60M Series B Sept 2025 at ~$550M | $24 Pro / $48 Pro Plus / $40 Security | Review presentation. Ten configurable walkthrough sections, Mermaid sequence diagrams, grouped file tables, one-click fix, Change Stack (2026-05-13), Overview page (2026-06-29) | An audit of 28 PRs found **15% of comments "Useless/Noise"** and **21% "Nitpicking"**; scored **1/5 completeness, 2/5 depth**; misses intent mismatches, cross-service dependencies, subtle logic *(REPORTED)* |
| **Graphite** | $52M Series B, 2025-03-18, Accel, with Anthropic's Anthology Fund | $20 Starter / $40 Team | **Lowest noise in the category** — markets *"less than 5% negative comment rate"* | Catches **only ~6% of bugs** *(REPORTED)*; $40/user for full features; "Diamond" brand deprecated 2025-10-08 → Graphite Agent |
| **Qodo** | Series A | Credit-based | Multi-agent review across correctness, standards, architecture, risk | Credits, not flat rate — premium models cost **4–5 credits per request**, so 2,500 monthly credits deplete fast *(REPORTED)*. A judge agent **deletes** low-confidence findings |
| **Greptile** | — | ~$30/mo | Single 0–5 confidence score, P0/P1/P2 severities, sequence diagrams | `Failed` means the run broke, never that the code was unreadable |
| **Cursor Bugbot** | Cursor-funded | Usage-based | Bug-only focus; ignores style and formatting by design | Documented: *"Bugbot does not emit a `skipped` conclusion"*; `neutral` conflates found-issues, cancelled, and internal error |
| **GitHub Copilot** | Microsoft | Bundled | Distribution. Nothing else comes close | Labels unopenable files *"Evaluated as low risk"*; counter demonstrably wrong in both directions (community discussion #152385) |
| **Sonar** | Public | Enterprise | **AI Code Assurance** — natively detects AI-generated snippets, applies taint analysis, enforces a quality gate; AI CodeFix (Claude Sonnet 4 recommended) | *"its AI capabilities lag meaningfully behind AI-native tools like CodeRabbit"* *(REPORTED)* |
| **CodeGraph** | None — MIT, free | Free | The agent-facing map. 66,097 stars in 7 months; 20+ framework resolvers | Name-matched edges presented as reliable; instructs agents *"don't re-verify them with grep"* (issue #765) |

---

## What the category is collectively good at

**Presentation and workflow.** CodeRabbit's ten-section walkthrough, grouped file rows,
generated sequence diagrams, one-click fixes, and Change Stack's *"change cohorts in ordered
layers"* are genuinely good product work. Greptile's single 0–5 score is a well-designed
triage primitive. These are solved problems and should be copied, not reinvented — the adopt
list in `MARKET_POSITION_2026-08.md` covers which parts.

**Noise suppression.** The whole field has converged on precision as the metric, because
developers rank false positives far above false negatives. Graphite has optimised hardest
for it.

---

## What the category is collectively bad at

**1. Depth. The precision ceiling is real and universal.**
Martian's Code Review Bench puts the field at roughly **50–76% precision**. CodeRabbit's
independent audit found **36% of comments were noise or nitpicking** *(REPORTED)*. Graphite
buys its low noise by commenting rarely — reportedly catching **~6% of bugs**. **Nobody has
solved this**, including the company that raised $143M today.

**2. Honesty about their own limits.**
Verified across seven tools in `MARKET_POSITION_2026-08.md`: not one can say *"I could not
analyse this."* Bugbot documents that it cannot. Qodo deletes low-confidence findings before
they reach the PR. Copilot mislabels capacity failures as risk judgements.

**3. Measuring whether any of it works.**
This is the largest gap in the market and the rest of this document is about it.

---

## The structural finding: nobody independent is measuring

**QUOTED from a comparison of vendor-sponsored against independent evidence:**

> vendor-affiliated studies consistently report **21–56% improvements** on isolated tasks
> using activity metrics, while independent studies measuring system-level outcomes in mature
> codebases find **neutral-to-negative results**

**The METR randomised controlled trial:** experienced developers were **19% SLOWER** with AI
tools while believing themselves **24% faster** — a **43-percentage-point perception-reality
gap**, which invalidates every self-report in the category.

Vendors claim 2–3× productivity. Independent measurement puts it nearer **10%**. There is
now an academic paper on the pattern: *"No Silver Harness: AI Coding Tools, Vendor
Narratives, and the Latest Fashion Cycle in Software Engineering."*

### The incumbents in measurement cannot see AI code

**QUOTED** on the engineering-intelligence platforms:

> Jellyfish and LinearB provide metadata analytics built for the pre-AI era, tracking PR
> cycle times and commit volumes **without distinguishing AI contributions**

> Tools like Jellyfish and LinearB track metadata such as PR cycle times and commit counts
> but **cannot separate AI-generated code from human work or prove whether AI improves
> outcomes**

> DX captures how developers **feel** about tools and processes but **does not inspect code
> changes directly**

And the consequence they name:

> A team where 60% of merged code is AI-generated may appear highly productive on activity
> dashboards while actually **accumulating technical debt or degrading quality metrics that
> only surface months later**

### The size of the problem being unmeasured

From LinearB's own 2026 benchmarks — **8.1 million PRs, ~4,800 teams**:

| Metric | AI-assisted | Human |
|---|---|---|
| Merge rate | **32.7%** | **84.4%** |
| Wait for first review | **4.6× longer** | baseline |
| PR size | **2.6× larger** | baseline |

From Sonar's State of Code, 8 January 2026, 1,100+ developers: **96%** do not fully trust
AI-generated code, **48%** always verify it, **38%** say reviewing it takes *more* effort
than human code, and it is **42%** of committed code heading to **65%** by 2027.

---

## Our differentiation

**Not a feature. A structural position: the only party in this market that can publish a
number against its own interest.**

Every figure in this category is self-scored. Four vendors each claim #1 on the same
benchmark, whose maintainers admit their gold set is wrong *"large enough to change
rankings."* Autonoma's mutation figures are *"illustrative."* Graphite's *"negative comment
rate"* is a coinage with no external definition. Vendor-sponsored studies report 21–56%
gains that independent measurement cannot reproduce.

What we built over six weeks is the opposite instrument: 57 pre-registered amendments, a
stop rule honoured when the number went against the company, a corrections file, and guards
that fail the build when a citation does not resolve. **The measurement discipline is the
asset. The graph never was.**

Three things follow, and only the first two are verified:

1. **A cost asymmetry.** CodeRabbit and Graphite bundle inference, so tokens sit in their
   cost of goods and scale with usage. BYOK inverts that — software margin instead of
   resale margin. *(VERIFIED pricing; the enterprise-committed-spend argument is UNVERIFIED)*
2. **A credibility asymmetry.** Their headline metrics are their marketing, so honest
   error-rate publication is unavailable to them. *(VERIFIED from their own pages)*
3. **A demand hypothesis.** That a buyer wants independent measurement of AI code.
   **UNVERIFIED.** This is the thing to test before anything is built.

---

## Why big tech cannot kill this in one move

**They can build the feature. They cannot occupy the position.** The distinction matters,
and it is the only durable thing in this document.

**1. The auditor cannot be the vendor.**
Microsoft will not ship a dashboard reporting that Copilot's code merges at 32.7% against
84.4% for human code. Anthropic will not publish that Claude Code's output needs more
rework. Cursor will not grade Bugbot. Each has a P&L reason not to, and the 43-point
perception-reality gap is what that conflict produces at scale. Bond ratings, financial
audit, and clinical trials all separate the measurer from the measured for this reason.

**2. GitHub is already building adjacent, and it proves the point rather than refuting it.**
Copilot metrics GA **2026-02-27**, org dashboard **2026-02-20**, repo-level **2026-07-17**,
impact dashboard **2026-07-22**, and **GitHub Code Quality GA 2026-07-20** with org-level
maintainability and reliability scores. That is a serious, well-resourced push — and every
piece of it measures **usage and adoption of their own product**, or code quality without
segmenting by author. None of it answers *"is the machine-written portion of our codebase
safe."* They will not build the answer while Copilot revenue depends on it not being asked.

**3. Multi-vendor reality favours the independent.**
Buyers run Copilot *and* Cursor *and* Claude Code. Measurement across them
**QUOTED** requires *"tool-agnostic detection instead of vendor-specific telemetry."* Every
big-tech dashboard is vendor-specific by construction. The neutral position is the only one
that can span the tools a real engineering org actually uses.

**4. The kill shot they do have.**
Acquisition, or a credible third party doing it first — Sonar is closest, already marketing
at the verification gap, already detecting AI-generated snippets natively, and public. If
anyone takes this position, it is them. That is the risk to watch, and it is a real one.

---

## What remains unverified

- **That anyone will pay for independent measurement of AI code.** No buyer identified. This
  is the single open question and no further desk research can answer it.
- **The enterprise committed-spend argument** behind the BYOK cost asymmetry.
- **CodeRabbit's 28-PR audit, Graphite's 6% bug-catch rate, and Sonar's "lags behind"** are
  all REPORTED from secondary sources and were not independently confirmed.

## The one test

Five conversations with VP Engineering or CTOs who bought AI coding tools in the last twelve
months. One question, no pitch:

> *"You've had Copilot or Cursor for a year. How do you know it's working, and what do you
> tell your board about the code it wrote?"*

If the answer is *"I don't know"*, the position in this document has a buyer. If the answer
is *"our dashboards cover it"*, it does not, and a week was spent instead of a year.
