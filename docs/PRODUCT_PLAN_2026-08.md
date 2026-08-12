# QuantaMind — product plan, August 2026

**Written 2026-08-12.** Market figures are sourced in `MARKET_POSITION_2026-08.md`,
`COMPETITIVE_LANDSCAPE_2026-08.md` and `ARCHITECTURAL_MOATS_2026-08.md`. This file does not
re-derive them; it decides what to build.

**Relationship to `BUILD_PLAN.md`:** that file gates every product layer on the correlation
test returning a positive verdict. It returned **RR 1.040**, below its own stop threshold of
1.5. The layered architecture it describes is **not built**, and this plan inherits none of
the falsified claim.

---

## One sentence

A pull-request reviewer that can **merge low-risk changes without a human** — and only
merges what it could **fully check**.

---

## Why now

| Fact | Source |
|---|---|
| AI PRs merge at **32.7%** vs **84.4%** human; wait **4.6× longer** for first review; **2.6× larger** | LinearB 2026, 8.1M PRs, ~4,800 teams |
| Largest single rejection cause is **inactivity — 17.3%**, auto-closed after a week of silence | MSR 2026 cluster, AIDev dataset |
| Senior engineers spend **8–12 hours/week** reviewing — **$10,000+/engineer/year** | industry benchmarks |
| **44% of teams** call slow review their **single biggest delivery bottleneck** | same |
| AI is **42%** of committed code, **65%** by 2027 | Sonar, 8 Jan 2026, 1,100+ devs |

**The bottleneck is not review quality — it is that nobody starts.** Reviewers wait 4.6×
longer to begin and review 2× faster once they do. Every incumbent responds by adding more
text to a queue that is already too long.

**The only way to shorten a queue is to take things out of it.**

---

## The product

Three parts. The third is what makes the first two defensible.

### Review

Table stakes, and built as such: findings with one-click fixes, PR summary, diagrams,
setup in minutes. Plus the one thing users complain about most — **a hard cap that survives
re-runs.** Never re-raise a dismissed finding; never comment on its own prior suggestion.
*"Unstoppable in suggestions"* and endless loops are the top user complaint in this category.

### Auto-merge, opt-in and default off

Low-risk changes merge without waiting for a human. Every condition is **deterministic** —
read from the ticket API, the diff, CI status and the parser. **No model decides whether to
merge.**

```yaml
# .quantamind.yml
auto_merge:
  enabled: false                     # default OFF, always

  require:
    ticket: true                     # must link Jira / Linear
    ticket_type:     [bug]
    ticket_priority: [low, minor]
    max_changed_lines: 50
    max_files: 3
    all_checks_green: true
    changed_lines_covered_by_tests: true
    review_findings: none            # zero findings at any severity
    coverage: full                   # every call site in the diff resolved

  never:
    paths: ["auth/**", "payments/**", "migrations/**", "infra/**", "*.tf"]
    changes_public_signature: true   # computed, not inferred

  on_fail: manual_review
```

### Coverage as the gate, not as a warning

**This is the load-bearing decision of the whole plan.**

For a year the obvious use of a coverage number was to warn a developer. That fails: a
literature review of six static-analysis surveys ranks *"misses too many issues"* **14th of
15** pain points, concluding developers *"care much more about too many false positives than
too many false negatives."* As a warning, coverage is noise.

**As a precondition for automation it is load-bearing:**

> Auto-merge only if every call site in the diff resolved. If we could not check something,
> a human does.

**This is not a risk claim.** It does not say unresolved code is more dangerous — our own
null falsified that. It says the machine automates only what it fully understood. That is
conservatism about our own knowledge, and it survives RR 1.040 intact.

It is also the moment a developer actually reads the number: not as a warning they can
ignore, but as **the reason the robot declined**.

---

## What it looks like

**Merged:**

```
QuantaMind auto-merged this PR                          $0.09

  ✓ PROJ-4821 · bug · low priority
  ✓ 23 lines, 2 files, no public signatures changed
  ✓ all checks green · changed lines covered by tests
  ✓ 18 of 18 call sites resolved

  Policy: .quantamind.yml · undo
```

**Held:**

```
QuantaMind held this PR for review                      $0.11

  ✓ PROJ-4830 · bug · low priority
  ✓ 31 lines, 2 files, all checks green
  ✗ 3 of 19 call sites could not be resolved · details

  Held because auto-merge requires full coverage.
```

Safety, non-negotiable: conservative defaults, one-click undo, a full audit line on every
auto-merge, an org-wide kill switch, and **a measured false-merge rate that we publish**.

---

## Competition — what each does, and why this is hard for them

| | Reviews | Controls merge | Merge conditions | Tracks coverage | Priced per | Blocked by |
|---|---|---|---|---|---|---|
| **CodeRabbit** ($1.5B) | ✅ best-in-class | ❌ comments only | — | ❌ | seat | No merge integration; precision headline |
| **Graphite** ($52M) | ✅ low-noise, ~6% bug catch | ✅ merge queue | approvals + CI | ❌ | seat | Per-seat revenue; *"<5% negative comment rate"* |
| **Kodus** (1.3k★, AGPLv3) | ✅ BYOK, self-hosted | ❌ | — | ❌ | seat | Capacity, not structure |
| **GitHub native** | ✅ Copilot review | ✅ auto-merge + queue | approvals + CI | ❌ | seat / bundled | Won't publish that Copilot's output needs scrutiny |
| **Qodo / Greptile / Bugbot** | ✅ | ❌ | — | ❌ | seat / credits | Review-only products |
| **QuantaMind** *(planned — nothing shipped)* | ✅ capped, never re-raises | ✅ conditional | **ticket · size · findings · coverage** | ✅ **as the gate** | **repository** | Unproven demand |

### The four cells nobody else fills

1. **Merge conditions that read the change, not just the checkboxes.** Every merge product
   in the market gates on the same two things: approvals and CI status. None gates on
   **ticket type, diff size, review findings, or coverage.**
2. **A coverage number at all.** Verified across seven tools — none can say *"I could not
   analyse this."*
3. **Review and merge in one product without a second app.** Graphite does both and makes
   every reviewer sign up. CodeRabbit, Kodus, Qodo, Greptile and Bugbot comment and stop.
4. **Per-repository pricing.** Everyone in the market charges per seat.

**Row three is the combination that matters.** Any single cell above is copyable. What is
awkward for them is holding all four at once, because each one costs a different incumbent
something they sell.

### Why the coverage gate is hard for all of them

**1. To gate on coverage you must first measure it — and none of them does.** Verified
across seven tools: not one can say *"I could not analyse this."* Cursor documents the
opposite outright — *"Bugbot does not emit a `skipped` conclusion."* Qodo's judge agent
**deletes** low-confidence findings before they reach the PR. Copilot labels files it could
not open *"Evaluated as low risk."*

**2. Measuring it means publishing a number that makes them look worse.** Graphite markets
*"less than 5% negative comment rate."* CodeRabbit markets precision. A coverage figure is
the one statistic that can only ever reduce a precision claim. **Their headline metric is
their marketing**, which is why "won't" has held for as long as it has.

**3. The review vendors have no merge integration and the merge vendors have no depth.**
CodeRabbit, Qodo, Greptile and Bugbot comment and stop. Graphite merges but reportedly
catches **~6% of bugs**. GitHub's native auto-merge fires on *"required checks passed and
approvals met"* — no condition on ticket type, diff size, findings, or coverage.

### Where the protection is thinner than it looks — state this plainly

- **Graphite is closest.** They already own the merge queue; adding policy conditions is
  weeks. Only the coverage condition would be built from scratch, and it fights their metric.
- **GitHub could add conditions to native auto-merge at any time.** This is the largest
  single risk in the plan.
- **Kodus has no structural block at all** — they are AGPLv3 and small. They could build
  any of this, and anyone can fork them.

**The protection is not the merge mechanic.** It is that gating on coverage requires having
measured coverage, which requires the instrument this repository spent six weeks building
and a willingness to publish an unflattering number. That is a head start, not a wall.

---

## Build order, with gates written before the work

**“Review” — first.** GitHub App, BYOK, findings with one-click fixes, hard cap, per-PR cost.
**Gate: 20 repositories still active after 30 days.** Under that, stop.

**“Auto-merge” — second.** Policy file, deterministic conditions, undo, audit line, kill
switch. **Gate: 200 auto-merges with zero reverts attributable to the gate**, published with
the method. A single bad merge in a customer's production path ends that account.

**“Coverage gate” — built with auto-merge, not after.** It is a condition, not a feature.
**Gate: the share of held PRs where coverage was the deciding condition.** If that is near
zero, the gate is decorative and should be removed rather than marketed.

---

## Pricing

**Per repository, not per seat.** Reviewers never sign up; they use GitHub.

Customer brings their own model key. **Sell control and data residency, never savings** — a
per-token review runs $15–25 against CodeRabbit's effective ~$1.20 per review at 20 PRs a
month. Any CFO who does that arithmetic walks if we pitched savings.

**Note:** Kodus already ships mandatory BYOK with zero markup and a token dashboard, free
for unlimited users. **BYOK is not differentiation.** It is table stakes and must be priced
as such.

---

## What we deliberately do not build

Each closed on evidence gathered 2026-08-12:

- **A better review engine as the differentiator** — precision is capped at 50–76%; a $1.5B
  incumbent was funded that morning
- **A code graph** — CodeGraph, 66k stars, MIT, free
- **Framework resolvers** — already in their `python.ts`
- **Diff-scoped mutation testing** — PIT, CircleCI, Autonoma, The Mutating Company
- **PR triage prediction** — GitHub ships it; a published model reports AUC 0.957
- **An MCP gateway** — 13 vendors
- **A general merge queue** — GitHub native is free; Mergify, Aviator, Trunk, Graphite
- **BYOK as a wedge** — Kodus, shipped, open source, free tier with unlimited users
- **Any claim that unresolved code is riskier** — **falsified by our own null**

---

## Risks

| Risk | Note |
|---|---|
| **One bad auto-merge ends an account** | Conservative defaults, undo, kill switch, published false-merge rate |
| **GitHub adds policy conditions to native auto-merge** | Would end this. Largest single risk |
| **Graphite adds policy gates to its merge queue** | Weeks of work for them |
| **Kodus builds it** | No structural block; AGPLv3, forkable |
| **Demand for coverage is unproven** | One issue, one reaction, against 44 for packaging requests. The gate design is what makes it survivable — it costs nothing if nobody cares |
| **BYOK review has not pulled demand** | Kodus: 17 months, 1,306 stars. CodeGraph reached 66k in 7 |

---

## What would falsify this plan

Written now so it cannot be reinterpreted later:

- Fewer than 20 active repositories 30 days after “Review” ships
- Any auto-merge reverted for a defect the gate should have caught
- Coverage is the deciding condition on **under 5%** of held PRs — the gate is decoration
- GitHub or Graphite announcing conditional auto-merge on ticket or finding state

Any one of those, and publishing the research and stopping remains a real outcome rather
than a failure. The null, the **65–71%** of breakage verdicts sharing no symbol with the PR,
and the verdict-collapse table across seven tools stand regardless of what happens here.
