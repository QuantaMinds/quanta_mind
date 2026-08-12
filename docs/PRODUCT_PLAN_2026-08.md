# QuantaMind — product plan, August 2026

**Written 2026-08-12.** Every market figure here is sourced in
`MARKET_POSITION_2026-08.md`, `COMPETITIVE_LANDSCAPE_2026-08.md`, and
`ARCHITECTURAL_MOATS_2026-08.md`. This file does not re-derive them; it decides what to
build.

**Relationship to `BUILD_PLAN.md`:** that file gates every product layer on the correlation
test returning a positive verdict. It returned **RR 1.040**, below its own stop threshold of
1.5. **The layered architecture it describes is not built.** This plan is a different
product with a different thesis, and it inherits none of the falsified claim.

---

## One sentence

A pull-request reviewer and merge queue that installs **once per repository**, runs on the
customer's **own model key**, and is the only one that will tell you **what it could not
check**.

---

## Why now

| Fact | Source |
|---|---|
| AI PRs merge at **32.7%** vs **84.4%** human; wait **4.6× longer**; **2.6× larger** | LinearB 2026, 8.1M PRs, ~4,800 teams |
| The single largest rejection cause is **inactivity — 17.3%**, auto-closed after a week of silence | MSR 2026 cluster, AIDev dataset |
| Senior engineers spend **8–12 hours a week** reviewing — **$10,000+/engineer/year** | industry benchmarks |
| **44% of teams** call slow review their **single biggest delivery bottleneck** | same |
| AI is **42%** of committed code, **65%** by 2027; **96%** don't fully trust it, **48%** verify | Sonar State of Code, 8 Jan 2026, 1,100+ devs |

**The bottleneck is not review quality. It is that nobody starts.** Reviewers wait 4.6×
longer to begin and review 2× faster once they do. Every incumbent adds more text to the
queue that is already too long.

---

## The leverage: three things their revenue model forbids

Not features they haven't built — **things that cost them money to build.**

| Their constraint | Why it is structural | Our inversion |
|---|---|---|
| Everyone needs a **Graphite account** — review lives in their app | Revenue **is** seats. Reviewers on plain GitHub takes a 50-seat team to ~10 | **Install once per repo.** Reviewers never sign up |
| **Bundled tokens**, no cost visibility | The spread between wholesale inference and $24/seat **is** the margin | **Bring your own key.** Per-PR cost shown |
| **Never reports what it could not check** | Their headline is precision. Disclosure lowers the number they market | **One grey line, behind a link** |

Any one of these they can match. **All three at once is a different company** — and Graphite
raised $52M, CodeRabbit $143M, on the model that forbids it.

**This is protected by their P&L, not by technology.** That buys time, not permanence. The
question is whether we reach enough users before repricing becomes worth it to them.

---

## What users already love — build all of it, claim none of it as differentiation

From real reviews, not vendor pages:

- Bug findings **with one-click suggested changes**
- A PR summary and diagrams — users volunteer that these become **running documentation**
- **Setup in minutes**
- Graphite's **stacked PRs** and **automatic rebasing**
- **Parallel CI on the merge queue: 1.5× faster merges, up to 2.5× with heavy stacking**

These are table stakes. Shipping them is the cost of being considered, not a reason to be
chosen.

## What users hate — and which parts are ours to fix

| Complaint | Fixable by them? |
|---|---|
| Support is a chatbot that pre-fills an email | Yes — hiring |
| Dashboard lag, 15–30s stale after CLI merge | Yes — engineering |
| **"Unstoppable in suggestions"** — comments on code it suggested last round, endless loops | Yes — already shipping persistent comments |
| Can't read the Jira ticket, so doesn't know **why** | Yes — integration work |
| **Everyone needs an account** | **No** |
| **No cost visibility** | **No** |

Fixing the first four is table stakes too. **Only the last two are leverage.**

---

## The product surface

What an author sees on a PR:

```
QuantaMind reviewed this PR                                    $0.14

🔴  payments/refund.py:41    refund_eligibility signature changed
     7 callers — 6 updated, 1 missed                       [apply fix]

🟡  payments/rules.py:88     unscoped query, missing tenant filter
                                                            [apply fix]

  2 findings · capped at 5 · 3 minor suppressed
  Checked 47 of 56 call sites · details
```

Four deliberate choices:

1. **Cost is on the PR.** Nobody else shows it. It is the visible proof of the BYOK model.
2. **A hard cap that survives re-runs.** Never re-raise a dismissed finding; never comment on
   its own prior suggestion. This is the #1 user complaint about CodeRabbit.
3. **`details` is a link.** Coverage is invisible to whoever doesn't care and available to
   whoever does. **This is the only design that survives the evidence** that developers rank
   missed issues 14th of 15 pain points.
4. **Reviewers use GitHub.** No second app, no account.

---

## Build order, with gates written before the work

**“Review” — first, and weeks not months.**
GitHub App. BYOK. Findings with one-click fixes, PR summary, hard cap, per-PR cost.
**Gate: 20 repositories installed and still active after 30 days.** Under that, stop — the
merge queue is a large build and does not deserve funding by hope.

**“Merge queue” — second, with parallel CI.**
Where the measured speed actually is. Must work through native GitHub UI.
**Gate: measured merge-time reduction on real customer repos, published with the method.**
If it doesn't beat Graphite's 1.5×, say so.

**“Coverage line” — last.**
Deterministic, local, zero tokens. Ambiguity first: *"4 functions share this name; a
name-matched caller list is not reliable here."*
**Gate: click-through rate on `details`.** If nobody clicks, the line stays and the roadmap
stops there.

---

## Pricing

**Per repository, not per seat.** This is the inversion, so it must be visible in the price
list.

Customer pays their own inference. **Sell control and data residency, never savings** — a
per-token review runs $15–25 against CodeRabbit's effective ~$1.20 per review at 20 PRs a
month. The first CFO who does that arithmetic walks if we pitched savings.

---

## What we deliberately do not build

Each closed on evidence in the market files:

- **A better review engine as the differentiator** — field precision is capped at 50–76% and
  a $1.5B incumbent was funded on 2026-08-12
- **A code graph** — CodeGraph, 66k stars, MIT, free
- **Framework resolvers** — already shipped in their `python.ts`
- **Diff-scoped mutation testing** — PIT, CircleCI, Autonoma, The Mutating Company
- **PR triage prediction** — GitHub ships it; a published model reports AUC 0.957
- **An MCP gateway** — 13 vendors
- **Auto-approval as the wedge** — Graphite owns the merge queue and is days away from it
- **Anything claiming unresolved code is riskier** — **falsified by our own null**

---

## Risks

| Risk | Severity |
|---|---|
| **Demand for coverage disclosure is unproven.** One issue, one reaction, against 44 for packaging requests | Known and priced in — it is one line behind a link |
| **Kodus already ships open-source model-agnostic review** | Check before “Review” ships |
| **GitHub ships per-repo review with native merge queue** | Would end this |
| **They reprice.** The leverage is P&L, not technology | Time-limited by construction |
| **A merge queue is a large build.** Graphite raised $52M for that half | The staged gate exists for this reason |

---

## What would falsify this plan

Written now, so it cannot be reinterpreted later:

- Fewer than 20 active repositories 30 days after “Review” ships
- Any incumbent announcing per-repo pricing
- Merge-time improvement below Graphite's published 1.5×

Any one of those and the honest move is to publish the research and stop — which remains a
real outcome, not a failure. The null, the **65–71%** of breakage verdicts sharing no symbol
with the PR, and the verdict-collapse table across seven tools are contributions regardless
of what happens to the product.
