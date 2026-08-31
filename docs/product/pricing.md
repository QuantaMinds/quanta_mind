# Pricing and what each tier gets

**Prices and margins are derived in `unit-economics.md`.** This file is the feature matrix.

**Every line carries a build status, and that is not decoration.** ✅ ships today. 🔨 is not built.
A pricing page that lists unbuilt features as sellable is how a company comes to promise what it
cannot deliver, and this project's own rule is that a document must not assert a state of the world
a reader cannot check.

**Nothing can be charged for yet.** `B3` (Stripe checkout and subscription webhooks) is parked, so
there is no billing rail. These tiers are a decision about what to build toward, not a live price
list.

---

| | **Free** | **Team** | **Enterprise** |
|---|---|---|---|
| | **$0** | **$29** /dev/mo | **from $60** /dev/mo |
| | ≤10 contributors | unlimited seats | unlimited seats |
| | | **BYOK: $26** | metered inference |

---

## Where we look — the ranker

| feature | Free | Team | Ent | status |
|---|:--:|:--:|:--:|---|
| Rank changed files by fix history | ✅ | ✅ | ✅ | ✅ ships |
| Depth allocation — read hard, read shallow, skip, and say which | ✅ | ✅ | ✅ | ✅ ships |
| Coverage line: what was ranked, read, and **deliberately not read** | ✅ | ✅ | ✅ | ✅ ships |
| Labelled import edges | ✅ | ✅ | ✅ | ✅ ships |

*This is the half with replicated out-of-sample evidence — 1.21% of fix-returning changes missed
against alphabetical order's 3.12%, six repositories the method never saw. It costs nothing per
review, which is why it is in Free.*

## Your standards, enforced

| feature | Free | Team | Ent | status |
|---|:--:|:--:|:--:|---|
| Rules as code in your repository (`.quantamind/rules.toml`) | ✅ | ✅ | ✅ | ✅ ships |
| Deterministic checks — forbid call, forbid import, naming | ✅ | ✅ | ✅ | ✅ ships |
| Your **existing** written standards read and enforced (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`…) | ✅ | ✅ | ✅ | ✅ ships |
| **Blocking status check** — a failing standard stops the merge | ✅ | ✅ | ✅ | ✅ ships |
| Per-repository compliance table | ✅ | ✅ | ✅ | ✅ ships |
| Unparseable and undecidable files **named, never counted as passing** | ✅ | ✅ | ✅ | ✅ ships |
| One standard defined once, enforced across every repository | — | — | ✅ | 🔨 `D1e` |
| Rules mined from your past review comments | — | — | ✅ | 🔨 `D1d` |
| Model-checked rules, separated from parser-checked ones | — | ✅ | ✅ | 🔨 `D1c` |

*Blocking requires a required status check, which GitHub gates behind a paid plan for private
repositories. On a free private repo the check posts and is visible but cannot be made to block.*

## The audit trail

| feature | Free | Team | Ent | status |
|---|:--:|:--:|:--:|---|
| Every rule, every file, every outcome — append-only | 30 days | full | full | ✅ ships |
| Four outcomes recorded apart: passed, violated, **uncheckable**, **deferred** | ✅ | ✅ | ✅ | ✅ ships |
| Provenance on every verdict — parser or model, never merged | ✅ | ✅ | ✅ | ✅ ships |
| Export | — | ✅ | ✅ | ✅ ships |
| Scheduled export to your own store | — | — | ✅ | 🔨 |

## The model reviewer

| feature | Free | Team | Ent | status |
|---|:--:|:--:|:--:|---|
| Findings anchored to the lines they concern | — | 40/dev/mo | uncapped | ✅ ships |
| Oracle gate — claims checked against GitHub and PyPI before publishing | — | ✅ | ✅ | ✅ ships |
| Cost per review, recorded and readable | — | ✅ | ✅ | ✅ ships |
| Bring your own model key | — | ✅ allowlist | ✅ any model | 🔨 `B7` |

*Sold with its measured accuracy stated, not hidden: **25.0% of published findings are correct**
(6 of 24, 95% CI 12.0–44.9%), and our gate shows no measurable improvement on that. It is included
because it sometimes finds real defects, not because it is reliable. If that number moves, this
table changes.*

## Working locally

| feature | Free | Team | Ent | status |
|---|:--:|:--:|:--:|---|
| Review before the pull request exists — uncommitted work included | ✅ | ✅ | ✅ | ✅ ships |
| `--json` for tools and agents | ✅ | ✅ | ✅ | ✅ ships |
| `/qm-review` editor command | ✅ | ✅ | ✅ | ✅ ships |
| CI integration | — | ✅ | ✅ | 🔨 `C2` |
| IDE plugin | — | — | ✅ | 🔨 `C3` |

## Operating it

| feature | Free | Team | Ent | status |
|---|:--:|:--:|:--:|---|
| Web dashboard — outcomes, compliance, cost | ✅ | ✅ | ✅ | ✅ ships |
| Sign in with GitHub | ✅ | ✅ | ✅ | ✅ ships |
| Background warm-up so a first review is not slow | ✅ | ✅ | ✅ | ✅ ships |
| We hold no source: packs carry counts, never code | ✅ | ✅ | ✅ | ✅ ships |
| No training on your code — structurally, we fine-tune nothing | ✅ | ✅ | ✅ | ✅ ships |
| SSO / SAML | — | — | ✅ | 🔨 `C4` |
| Self-hosted or on-premise | — | — | ✅ | 🔨 `D7f` |
| Data residency, DPA, SLA | — | — | ✅ | 🔨 |
| SOC 2 Type II | — | — | ✅ | 🔨 `D7e`, months of external work |

---

## What each tier is for

**Free — everything that is deterministic, forever.** Ranking, your standards, the blocking check,
the compliance table, the local tools. It never expires because it costs us nothing to run: no
model is called. Capped at ten contributors, which is where Semgrep draws the same line.

**Team — $29/dev/mo.** Everything above without the seat cap, plus the model reviewer at 40 reviews
per developer per month, the full exportable audit trail, and cost reporting. Priced against
Semgrep ($30/contributor) and SonarQube ($40–50/dev), not against AI-review tools at $24 — because
what is being bought is enforced standards with a trail, and that is the half whose verdicts
reproduce.

**Enterprise — from $60/dev/mo.** A different buyer, not a bigger quota: one standard across every
repository, SSO, self-hosting, residency, a DPA and an SLA. **Most of this is unbuilt**, and it
should be built when a deal asks for it, not before.

**BYOK — $26/dev/mo, 10% off.** Inference is 4–7% of the Team price, so a customer's own key saves
us about $2 per developer per month. The discount is for the procurement value — their rate card,
their residency terms, their model choice — not a pass-through of cost. Allowlisted models only
below Enterprise: a model we have not evaluated makes every accuracy figure above untrue for that
customer.

## Honest limits on this page

- **No billing exists.** `B3` is parked; nothing can be charged today.
- **BYOK is unbuilt** (`B7`), so its price is a plan, not an offer.
- **Enterprise is mostly unbuilt.** Four of its differentiators are 🔨, and SOC 2 alone is months.
- **The cost behind these margins is a floor** — `infer/prompt_once` does not report usage, so the
  true cost per review is higher than measured by an unknown amount.
