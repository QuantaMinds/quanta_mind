# Founder Briefing

> How to explain this project to someone smart who has never heard of it. Read top to
> bottom once. After that, §9 is the part you re-read before a conversation.
>
> **Rule for every conversation: never claim more than §8 allows.** The thesis is not yet
> measured. A co-founder who finds that out later trusts you less than one who hears it now.

---

## 1. The one sentence

> **Every AI coding tool tells the agent what it found. None tells it what it missed.
> We measure and report the gap.**

If you remember nothing else, remember that sentence. Everything below is elaboration.

---

## 2. The 60-second version, with the example

An AI agent is about to change a function. Before it does, it needs to know **who calls
that function.** Every tool answers by building a directory of who-calls-whom.

The directory is always incomplete. Some calls route through paths the directory cannot
see. **No tool says which ones.**

```python
class BasePaymentHandler:
    def validate(self, req): ...          # you change this

class StripeHandler(BasePaymentHandler):
    def validate(self, req):
        super().validate(req)             # ← invisible to static analysis
        self._check_stripe_fields(req)
```

The best open-source Python call-graph tool does not put `super()` calls in the graph
**at all.** Your agent searches, finds 3 callers, edits them, and ships confidently.
There were 9.

With us:

```
callers_of("BasePaymentHandler.validate")

  RESOLVED     3   direct
  FRAMEWORK    6   super() chain — StripeHandler, PaypalHandler, +4
  UNRESOLVED   1   plugins/legacy.py:88 — getattr(mod, cfg["handler"])
                   → cannot be determined. A human must check this.

  coverage(payments/) = 91%
```

The agent now says: *"I updated 9, not 3. One I could not verify — check `legacy.py:88`."*

**The last line is the product.** Every competitor would have returned 3 and sounded
certain.

---

## 3. Why this happens at all — the root cause

The interesting question is not "why is analysis hard." It is **"why is Google's
2-billion-line codebase easier to analyse than a 200,000-line Django app?"**

Because Google made dependency declaration a **build-time invariant**. From
*Software Engineering at Google*: Blaze detects when a target references a symbol without
declaring a dependency on it, and **fails the build**. Rolling that out across their
codebase and refactoring millions of build targets took **multiple years**.

At Google, "what does this depend on" is a **fact you can read**.
Everywhere else, it is a **guess you have to reconstruct** — because of dynamic imports,
dependency-injection containers, config-driven wiring, reflection, string-based routing.
The information was never written down.

**Everyone else has to reconstruct the graph, and reconstruction is lossy in a way nobody
measures.** That unmeasured lossiness is our entire product.

---

## 4. How we build it — six steps, cheapest first

The design principle: **the model is the last thing we reach for, never the first.**

| Step | What | Cost | Ours? |
|---|---|---|---|
| 1 | **Borrow a graph.** Adapter over CodeGraph / Graphify / PyCG | free | ❌ borrowed |
| 2 | **Count call sites** — tree-sitter census | seconds | ✅ **ours** |
| 3 | **Type resolution** — pyright / LSP | minutes | ❌ borrowed |
| 4 | **Framework resolvers** — Django URLs, Celery tasks, `super()` chains, SQLAlchemy | fast | ✅ **ours** |
| 5 | **Feature scan** — find `eval`, computed `getattr`, metaclasses | seconds | ✅ **ours** |
| 6 | **Label + coverage** — confidence per edge, coverage per directory | instant | ✅ **ours** |

Roughly **800 lines of our own code.** Everything else is borrowed, and that is deliberate.

### Why we don't build the graph

Three free MIT projects in this category hold roughly **165,000 GitHub stars** between
them. One went from zero to 47,000 stars in five months, built largely by one person.
They ship weekly. We would lose that race, and losing it would consume the entire team.

So we consume their graph as a dependency. **Every improvement they ship improves our
product.** We compete on the one number none of them computes.

### Why no LLM in the core pipeline

Three reasons, in order of importance:

1. **Determinism.** Run it twice, get the identical answer. You cannot version, diff, or
   attest to something that changes between runs.
2. **Verifiability.** "tree-sitter says line 40 imports `AuthBase`" is checkable in one
   second. "The model says this file handles auth" is not checkable at all.
3. **Margin.** Competitors burn tokens on every review. Our marginal cost is close to
   electricity. That is why we can price at half of theirs and still make money.

---

## 5. Why not just use the existing tools

Have the specific answer ready for each. Vague answers lose this conversation.

| They ask | The answer |
|---|---|
| **"CodeGraph is free"** | It is, and we *use* it. It is a graph builder — it reports what it found and stays silent about what it missed. We add the silence. |
| **"Cursor already indexes the codebase"** | Cursor's own docs: on large monorepos the index "may not include all files if the index size limit is exceeded… add them explicitly with @-mentions." **The fix is the human noticing.** That is the problem. |
| **"Claude Code just greps"** | By deliberate design — no index, for security and staleness reasons. It fails on "I don't know the name" queries: ask *where does rate limiting happen* when the code calls it `throttleMiddleware`. Anthropic's own docs concede degradation as codebases grow. |
| **"Augment raised $252M"** | Closest competitor and the strongest objection. Static + embeddings, server-side. Same blind spots, no coverage number, and **your code goes to their servers.** |
| **"Greptile/CodeRabbit already review PRs"** | They do, and the independent benchmark shows the #1 tool at **49.2% precision** — roughly one comment in two leads to a change. They optimise for finding more. Nobody optimises for knowing when to stay quiet. |
| **"Why hasn't someone done this?"** | Someone did — for **Java**, as academic research, in 2019. It works. It has **10 GitHub stars.** The method was proven and never packaged. That is the gap. |

**The universal one-liner, for when you only get one sentence:**

> *Every one of them tells your agent what it found. None tells it what it missed.*

⚠️ **Precision required if you are talking to someone technical.** Researchers *do*
measure misses — SWE-PRBench finds frontier models detect 15–31% of human-flagged issues;
CR-Bench, Atlassian (1,900+ repos) and independent planted-bug studies all publish
denominators. The defensible claim is narrower:

> *Researchers measure misses on curated benchmarks. No vendor reports one, and nobody
> measures it per-repository at runtime — because that needs a call-site count, and none of
> them count.*

Do not say "nobody measures what they missed." It does not survive contact with anyone who
reads arXiv. See `PROJECT_CONTEXT.md §3`.

---

## 6. Why anyone pays

### The buyer is not the developer

Developers do not buy epistemics. **The buyer is whoever eats the cost when an
agent-authored change breaks production** — platform engineering, with security sign-off.

### The number that makes the case

A study of 7,191 agent-authored PRs against 1,402 human ones (arXiv 2603.27524, MSR 2026)
found agents introduce **fewer** breaking changes when writing new code and **more** when
changing existing code. The authors name a **"Confidence Trap"**: highly confident agentic
PRs still break things — and the breaking rate is flat across confidence levels.

**Quote the unit, always.** Their headline rates are per *patch*; the per-*PR* rates are
roughly three times larger, and mixing them is the fastest way to lose an investor who
opens the paper:

| | Agent | Human |
|---|---|---|
| Breaking changes per **patch** (code generation) | 3.45% | 7.40% |
| Breaking changes per **PR** | 11.3% | 21.18% |
| Refactoring, per patch | **6.72%** | 4.36% |
| Chore, per patch | **9.35%** | 4.95% |

Say that out loud and let it land:

> **Agents are already safer than humans at writing new code, and roughly one and a half to
> twice as risky at changing it. Enterprises spend most of their engineering time changing
> it.**

*(Not "three times." Three-times compares agents to **themselves** — 9.35% on chores against
3.45% on generation. Against humans on the same maintenance work it is 6.72% vs 4.36% and
9.35% vs 4.95%, so 1.5×–1.9×. The weaker number is the defensible one, and it is still the
whole argument.)*

### The best sentence anyone else has written about us

From that paper's own Threats to Validity:

> *"We measure 'Potential Breaking Changes' based on syntactic-level modifications, even
> though some changes may affect functions with no downstream users."*

They detect that a signature changed. They never check whether anything calls it. **That
gap is the product**, named by a peer-reviewed paper as its own limitation.

Two more things about their tool, both of which cut our way. It was validated for
**precision only** — 95.7% and 93.6% agreement on 94 sampled patches, Cohen's κ = 0.79 —
with **no recall validation**, so the false-negative rate of AST-based breaking-change
detection is unmeasured. And 66% of patches were discarded before analysis. Their number is
a floor, not an estimate.

Independent support for the market rather than the mechanism: a causal study (staggered
difference-in-differences with matched controls) found agent adoption raises
static-analysis warnings ~18% and cognitive complexity ~39%, and calls for **provenance
tracking** by name.

### The gap in our own evidence — say it before they find it

Phase 0 tests whether unresolved call sites predict breakage in agent-authored Python
changes, on a corpus that is **65% OpenAI Codex and 1.4% Claude Code** (459 PRs). The
mechanism is agent-agnostic — it is about what the codebase makes knowable, not which model
is reading it. But the evidence is Codex evidence, and the product's first integration is
Claude Code. **That gap is real and Phase 0 does not close it.**

Two things make it survivable rather than fatal, and both should be said in the same breath:

- Codex has the **lowest** breaking rate of the five agents measured (2.62%, against Claude
  Code's 5.10%). The corpus is two-thirds the safest agent, so an effect that shows up
  anyway shows up under unfavourable conditions.
- If the mechanism is real, agent **retrieval strategy** should moderate it — Claude Code
  greps without an index, Cursor embeds, Devin indexes. That prediction is registered before
  the run, so if it appears it is evidence rather than a story.

An investor who reads the source paper finds the 1.4% in ten minutes. Better that it is
already in the deck, with the two mitigations attached.

### Willingness to pay is already demonstrated

An enterprise deployed language servers **org-wide**, at their own cost, before rolling
out Claude Code — because their codebase was too large for grep to stay useful. They built
a worse version of our layer 3, with no vendor and no coverage number.

### The pitch

> *You are running coding agents against a codebase where refactors break things ~6.7% of
> the time and the agent is confident every time. We tell it — and you — exactly which
> parts of a change it could verify and which it could not. Per PR. With a receipt.*

### Pricing (draft — validate before publishing)

| Tier | Price | Scope |
|---|---|---|
| Free | $0 | 2 private repos, 1 dev; unlimited public repos |
| Team | $12/dev/mo annual | unlimited repos, resolvers, PR comments |
| Business | $29/dev/mo | SSO, org rollup, audit attestation |
| Enterprise | custom | air-gap, SLA, resolver development |

Market comparison (June 2026): CodeRabbit $24, Greptile $30, Qodo $30, Cursor BugBot $40,
Augment $60. **We sit at the floor deliberately** — we are unknown, and price must not be
an objection we have to answer. Our zero-LLM pipeline is what makes the floor profitable.

---

## 7. The minute differentiators — the things you will forget

These are small, technical, and they *are* the moat. Learn them.

### 7.1 Absence is a typed value

Every tool has this shape:

```python
def callers_of(symbol) -> list[Edge]: ...
```

An empty list means two different things — *nobody calls this* and *we could not tell.*
**The type system erased the distinction.** Ours:

```python
def callers_of(symbol) -> tuple[list[Edge], list[Unresolved]]: ...
```

The second return value is the product.

### 7.2 `Confidence` has no default

A dataclass field with no default means the type-checker **forces** every code path to
decide. A default is how a guess silently becomes a claim.

### 7.3 We compute a denominator; nobody else does

Everyone emits edges. **Nobody emits how many call sites there were to begin with.**
Without the denominator, coverage is not computable — which is why no competitor reports
one. Not a choice they made; an architecture that never counts.

### 7.4 Builtins are excluded from both sides

`"abc".strip()` is a call. It accounts for roughly **59%** of the apparent gap between
static and runtime graphs. Counting it makes coverage look catastrophic and tells a
developer nothing. Excluding it is why our number means something.

### 7.5 Capability × prevalence — we never need the right answer

We cannot know your true call graph. Nobody can. We don't need to:

| Measurement | Where | Needs ground truth on your code? |
|---|---|---|
| **Capability** — what can our resolvers handle? | our fixtures | No |
| **Prevalence** — which of those appear in your repo? | cheap AST scan | No |
| **Unsoundness map** = capability × prevalence | derived | No |

If our fixtures prove we cannot resolve computed `getattr`, and the scanner finds 47 of
them in `payments/`, **we know exactly where we are blind without knowing the answer.**
That is why three people can build this.

### 7.6 Coverage is per-directory, never global

A repo is not uniformly knowable. `billing/` might be 94% and `plugins/` 41%. One global
number hides exactly the thing the developer needs.

### 7.7 Every response carries `pack_sha`

If it does not match `git rev-parse HEAD`, the answer is marked stale rather than served
silently. Stale context that looks fresh is the failure mode we exist to prevent — we do
not get to commit it ourselves.

### 7.8 The source never leaves their network

Architectural, not a setting. It is why there is no three-month security review, no FDE,
and no data-residency conversation. **Say this early in every enterprise call.**

### 7.9 Their compute, not ours

Indexing runs in their GitHub Actions runner. Free-tier users cost us essentially nothing,
and their code still never moves. Competitors running inference on their own servers cannot
copy this without gutting their margin.

### 7.10 We refuse to build a "smarter" analyser

The research is explicit that soundness → imprecision → unscalability is a **causal chain**.
More completeness means more over-approximation means more memory means timeout. The best
Python call-graph tool exceeded a six-hour timeout on 6 of 50 real projects and 60GB of RAM
on 3 more.

We escape the chain by not entering it. Framework resolvers work because Django
*guarantees* the `urls.py` → view mapping — that is **reading a declaration, not inferring
one.**

---

## 8. What is not yet true — say this before they ask

**The core assumption is unmeasured.** We believe an unresolved call site predicts
breakage. **Nobody has shown that**, including us.

Phase 0 is a one-week pre-registered study — ~3,300 agent PRs plus ~1,000 human ones,
relative risk with a confidence interval, thresholds fixed **before** the data is touched:

| Result | What we do |
|---|---|
| RR ≥ 3.0 | Build. The pitch above holds. |
| RR 1.5–3.0 | Build, but we sell **review prioritisation**, not breakage prevention. Different price, different buyer. |
| RR < 1.5 | **Stop.** Publish the null. It is a real contribution and it closes the question honestly. |

**And the mechanism itself is under pressure.** SWE-PRBench (arXiv 2603.26130) measured 8
frontier models across three context configurations and found all of them get *worse* as
structured context is added — including AST-extracted function context and import graph
resolution, which is our pipeline. The identified cause is attention dilution, not content
quality. Their guidance: *"adding file content does not help and actively harms performance
across all tested models."*

Our defence is that they tested *pushing* context into a prompt while we have the agent
*pull* via tool calls — a different position and volume in the context window. **That is a
hypothesis and it is untested.** Phase 0c tests it against their public harness before any
product code is written. If you are asked "why will your context help when the benchmark
says context hurts," this is the honest answer: *we don't know yet, and it is the next thing
we measure.*

What is on our side: their Type3 Latent category — issues in files that import or depend on
the changed files — is our thesis verbatim, sits near zero for every model at every
configuration, and *"Python has the highest absolute Type3 count (32 of 43, 74.4%),
consistent with Python's dynamic import patterns."*

Two more honest points:

- The often-quoted "static analysis misses 51% of edges" is **misleading**. About 59% of
  those misses are builtins and 12% are naming artefacts. **The real actionable signal is
  closer to 15%.** We corrected this ourselves before anyone caught it, and it is written
  in our corrections log.
- This is a **productisation play, not a research play.** The method was published in 2015,
  the measurement built in 2019, and extended to Python. Nobody turned it into a running
  service. Our moat is execution — resolvers, incremental updates, developer experience —
  not novelty. An investor who reads the papers will check.

**Volunteering §8 is what makes §1–§7 credible.** A founder who has already found the holes
in their own thesis is trusted more than one who hasn't looked.

---

## 9. The five questions, and your answers

**"What are we building?"**
The layer that tells an AI coding agent what it does not know about your codebase. It reads
your repo, works out which parts it can verify and which it cannot, and hands the agent both
answers so it stops guessing confidently.

**"Why hasn't Google or Anthropic done this?"**
Anthropic ships grep by design — no index, for security and staleness reasons. Google
doesn't need it: they made dependencies declared by force over multiple years. And the
academic version exists for Java with 10 stars, because researchers publish and move on.
Somebody has to package it.

**"What stops CodeGraph adding this in a month?"**
The scan, nothing. The scan is not the product. Forty tested framework resolvers, each
pinned to framework versions, each with fixtures, is two years of grinding. And every
improvement they ship to the graph improves us — we are their consumer, not their rival.

**"Why would anyone pay when free tools exist?"**
Free tools report what they found. When your agent breaks a refactor — which happens ~6.7%
of the time — nothing tells you the tool was blind to that call site. We do, before the PR
merges, with a receipt.

**"What if you're wrong?"**
Then Phase 0 tells us in one week for about $25, and we publish the null. That is a real
result and it costs us a week instead of a year.
