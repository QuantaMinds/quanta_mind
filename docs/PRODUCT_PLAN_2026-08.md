# QuantaMind — product plan, August 2026

**Written 2026-08-12.** Market figures are sourced in `MARKET_POSITION_2026-08.md`,
`COMPETITIVE_LANDSCAPE_2026-08.md` and `ARCHITECTURAL_MOATS_2026-08.md`.

**Relationship to `BUILD_PLAN.md`:** that file gates every product layer on the correlation
test returning a positive verdict. It returned **RR 1.040**, below its own stop threshold of
1.5. That architecture is **not built** and this plan inherits none of the falsified claim.

---

## One sentence

**The merge gate.** It reads whatever reviewer you already run, adds the checks nobody
performs, and merges the low-risk changes so a human never sees them.

**We do not build a reviewer.** We consume one — the same shape as `AGENTS.md`'s founding
rule: *"We do not build a graph… We consume one and own the number none of them computes."*

---

## Why now

| Fact | Source |
|---|---|
| AI PRs merge at **32.7%** vs **84.4%**; wait **4.6× longer** for first review; **2.6× larger** | LinearB 2026, 8.1M PRs, ~4,800 teams |
| Largest single rejection cause is **inactivity — 17.3%**, auto-closed after a week of silence | MSR 2026, AIDev dataset |
| Senior engineers spend **8–12 hours/week** reviewing — **$10,000+/engineer/year** | industry benchmarks |
| **44% of teams** call slow review their **single biggest delivery bottleneck** | same |

**The bottleneck is not review quality — it is that nobody starts.** Every incumbent responds
by adding more text to a queue that is already too long. **The only way to shorten a queue is
to take things out of it.**

---

## Two decisions that shape everything

### No inference. No keys. No BYOK.

Kodus shipped mandatory BYOK, zero markup, open source, free for unlimited users —
**17 months, 1,306 stars.** CodeGraph, free and requiring no key, reached **66,097 in seven.**
BYOK is a **friction vector, not a growth vector**, and asking a VP Engineering to manage
model keys contradicts the one thing that drives adoption: seamless install.

**So the product runs no model at all.** Every gate condition is read from an API or computed
by a parser. Cost of goods is near zero, onboarding is one GitHub App install, and there is
no key to provision, rotate, or budget.

### The differentiator ships first, because it is the only thing we ship

An earlier draft built a reviewer first and gated auto-merge behind 20 installs. That was
backwards: **the reviewer is a commodity** — CodeRabbit at $1.5B, Kodus free with unlimited
users, Copilot bundled — so nobody would install ours to get it, and the gate would never
open. **Innovation cannot be gated behind a commodity.**

There is no reviewer in this plan.

---

## How it works

```
  PR opens
      ↓
  Their reviewer runs        CodeRabbit / Copilot / Graphite / Qodo / anything
      ↓                      → posts a GitHub check run
  QuantaMind reads:
      · that check run's conclusion          checks:read
      · the linked ticket                    Jira / Linear API
      · diff size, files, public signatures  parser
      · CI status                            GitHub API
      · tests covering changed lines         coverage report
      · call-site coverage of the diff       our parser — the only thing we compute
      ↓
  All conditions pass? → merge.    Any condition fails? → human.
```

**Everything is deterministic. No model decides whether to merge.**

```yaml
# .quantamind.yml
auto_merge:
  enabled: false                     # default OFF, always

  reviewer_check: "coderabbitai"     # whose check run to read; any app
  require:
    reviewer_conclusion: success
    ticket: true
    ticket_type:     [bug]
    ticket_priority: [low, minor]
    max_changed_lines: 50
    max_files: 3
    all_checks_green: true
    changed_lines_covered_by_tests: true
    coverage: full                   # every call site in the diff resolved

  never:
    paths: ["auth/**", "payments/**", "migrations/**", "infra/**", "*.tf"]
    changes_public_signature: true

  on_fail: manual_review
```

### Coverage is the gate, not a warning

For a year the obvious use of a coverage number was to warn a developer. That fails — six
static-analysis surveys rank *"misses too many issues"* **14th of 15** pain points. As a
warning it is noise.

**As a precondition for automation it is load-bearing:** merge only what we could fully
check. That is **not** a claim that unresolved code is riskier — our own null falsified that.
It is the machine refusing to automate what it did not understand, and it is the one moment
someone reads the number, because it is **why the robot declined.**

---

## What it looks like

```
QuantaMind auto-merged this PR

  ✓ PROJ-4821 · bug · low priority
  ✓ CodeRabbit: no findings
  ✓ 23 lines, 2 files, no public signatures changed
  ✓ all checks green · changed lines covered by tests
  ✓ 18 of 18 call sites resolved

  Policy: .quantamind.yml · undo
```

```
QuantaMind held this PR for review

  ✓ PROJ-4830 · bug · low · CodeRabbit: no findings
  ✗ 3 of 19 call sites could not be resolved · details

  Held because auto-merge requires full coverage.
```

Non-negotiable: conservative defaults, one-click undo, an audit line on every auto-merge, an
org-wide kill switch, and **a published false-merge rate**.

---

## Competition

| | Reviews | Controls merge | Merge conditions | Tracks coverage | Needs a key | Priced per |
|---|---|---|---|---|---|---|
| **CodeRabbit** ($1.5B) | ✅ best-in-class | ❌ comments only | — | ❌ | no | seat |
| **Graphite** ($52M) | ✅ ~6% bug catch | ✅ merge queue | approvals + CI | ❌ | no | seat |
| **Kodus** (1.3k★) | ✅ | ❌ | — | ❌ | **yes** | seat |
| **GitHub native** | ✅ Copilot | ✅ auto-merge | approvals + CI | ❌ | no | bundled |
| **Qodo / Greptile / Bugbot** | ✅ | ❌ | — | ❌ | no | seat / credits |
| **QuantaMind** *(planned)* | ❌ **by design** | ✅ conditional | **ticket · size · findings · coverage** | ✅ **as the gate** | **no** | **repository** |

### The cells nobody fills

1. **Merge conditions that read the change.** Every merge product in the market gates on the
   same two things — approvals and CI status. **None** gates on ticket type, diff size,
   reviewer verdict, or coverage.
2. **A coverage number at all.** Verified across seven tools: none can say *"I could not
   analyse this."* Cursor documents it — *"Bugbot does not emit a `skipped` conclusion."*
3. **Being complementary.** Every other product replaces a reviewer. **We make the one they
   already bought do something** — their CodeRabbit spend stops being advice and starts
   gating merges.

### Why it is hard for them

**To gate on coverage you must measure it, and measuring it publishes a number that only ever
lowers a precision claim.** Graphite markets *"less than 5% negative comment rate"*;
CodeRabbit markets precision. Their headline metric is their marketing.

**And a reviewer cannot credibly gate on its own verdict.** CodeRabbit auto-merging when
CodeRabbit found nothing is a vendor grading its own homework — the same conflict that
produced a 43-point perception-reality gap in AI productivity claims. **An independent gate
reading their output is a position they structurally cannot occupy.**

### Where it is thin — say it plainly

- **Graphite is weeks away.** They own the merge queue; policy conditions are not hard.
- **GitHub could add conditions to native auto-merge at any time.** Largest single risk.
- **Kodus has no structural block.** AGPLv3, forkable.

The protection is that the coverage condition requires the instrument this repository spent
six weeks building, and a willingness to publish an unflattering number. **A head start, not
a wall.**

---

## The risk this design creates, and it is real

**We inherit the reviewer's blind spots.** *"CodeRabbit found nothing"* is weak evidence of
safety — field precision runs 50–76%, and Graphite reportedly catches **~6% of bugs**. A
reviewer finding nothing often means it did not look hard enough.

**Mitigation is the design itself:** the reviewer's verdict is **one condition of eight**, and
the others are the conservative ones — bug tickets only, low priority, under 50 lines, under
3 files, tests covering the changed lines, no public signature change, denylisted paths, full
call-site coverage. **We are not trusting the reviewer. We are refusing to merge anything the
reviewer's weakness could plausibly reach.**

If that framing does not survive contact with a real repository, the gate is too loose and
must tighten before shipping.

---

## Build order

**“Merge gate” — first and alone.** GitHub App: `checks:read`, `contents:write`,
`pull_requests:write`. Reads a check run, a ticket, a diff. Merges or holds.
**Gate: 200 auto-merges with zero reverts attributable to the gate**, published with method.

**“Coverage condition” — built with it, not after.** It is a condition, not a feature.
**Gate: coverage is the deciding condition on ≥5% of held PRs.** Below that it is decoration
and gets removed rather than marketed.

**Nothing else until both pass.**

---

## Pricing

**Per repository.** Near-zero cost of goods — no inference — so the price can sit far below
per-seat review tools and still carry margin. Reviewers never sign up; they use GitHub.

---

## What we deliberately do not build

- **A reviewer** — commodity; and building one is what would delay the differentiator
- **BYOK / model routing** — friction vector; Kodus shipped it and it did not pull demand
- **A code graph** — CodeGraph, 66k stars, MIT, free
- **A general merge queue** — GitHub native is free; Mergify, Aviator, Trunk, Graphite
- **Framework resolvers, mutation testing, PR triage prediction, an MCP gateway** — all
  shipped by others, evidence in the market files
- **Any claim that unresolved code is riskier** — **falsified by our own null**

---

## What would falsify this plan

Written now so it cannot be reinterpreted later:

- **Any auto-merge reverted for a defect the gate should have caught**
- Coverage is the deciding condition on **under 5%** of held PRs
- GitHub or Graphite announcing conditional auto-merge on ticket or reviewer state
- Teams enable it and set conditions so loose the gate is ceremonial

Any one of those and publishing the research and stopping remains a real outcome. The null,
the **65–71%** of breakage verdicts sharing no symbol with the PR, and the verdict-collapse
table across seven tools stand regardless.
