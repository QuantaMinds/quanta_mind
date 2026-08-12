# Architectural moats — who can reach what, August 2026

**Retrieved 2026-08-12 by live web search.** Verification statuses as in
`COMPETITIVE_LANDSCAPE_2026-08.md`: **VERIFIED**, **QUOTED**, **REPORTED** (secondary
source, named), **UNVERIFIED**.

This file answers one question the other two do not: **what can a competitor build in a
week, and what is their architecture physically unable to reach?** A capability anyone can
copy is not a wedge. The only durable positions are the ones behind an architectural wall.

---

## The market has split, and one of the players says so

**QUOTED**, Lightrun:

> “A static reviewer and a runtime verifier are **not competing tools**; they cover
> **different halves** of the same review.”

**Half one — static.** Read the diff, reason about it, comment. CodeRabbit, Graphite,
Greptile, Qodo, Bugbot, Copilot. Commoditized, well funded, precision-capped at 50–76%.

**Half two — runtime.** Observe the code actually running. Launched June 2026. One player.

The pain numbers in half two are the largest found in any of this research — though both are
**REPORTED** from Lightrun's own State of AI-Powered Engineering report and should be treated
as directional:

- **43%** of AI-generated code requires manual debugging in production **even after passing
  QA and staging**
- **Incidents per PR up 242.7%** in 2026

---

## What each player can physically reach

### CodeRabbit — the diff reader

| | |
|---|---|
| Runs where | GitHub App. Webhook on PR open, then **QUOTED** *"spins up a fresh, isolated sandbox environment specifically for that review"* |
| Sees | The diff, repo history, an AST code graph, linked tickets, prior PRs, outputs from 40+ linters and SAST tools |
| Controls | Nothing. It comments; humans decide |
| Cannot reach | The merge decision, the developer's machine, production |

**Important correction to an earlier assumption in this repository:** CodeRabbit **already
has sandbox infrastructure**. The claim that "they cannot execute anything" is wrong. What
is unproven is whether they run the customer's *tests* or only analysis tooling.

### Graphite — the workflow owner

| | |
|---|---|
| Runs where | **Local CLI** on the developer's machine, plus a cloud app, plus a **stack-aware merge queue** |
| Sees | The diff, and uniquely **the dependency structure between PRs** in a stack |
| Controls | **The merge itself.** The queue batches stacks, runs **CI on all PRs in a stack in parallel**, and fast-forward merges. **REPORTED**: median merge time 24 hours → 90 minutes |
| Cannot reach | Production runtime |

**Graphite is architecturally stronger than CodeRabbit and this is under-appreciated.** They
hold three positions CodeRabbit does not: the developer's local machine before a PR exists,
the merge decision point, and the inter-PR dependency graph.

**Their exposure:** GitHub shipped stacked PRs in public preview, April 2026 *(REPORTED)*.
The platform is commoditizing their original differentiator.

### Lightrun — the runtime half

| | |
|---|---|
| Runs where | A **Runtime Sensor deployed inside the customer's production environment** |
| Sees | **QUOTED** — *"variable values, branch decisions, and downstream service behavior at the exact line the PR modifies"*, against live traffic |
| Controls | Emits a risk score, risky → safe |
| Cannot reach | Nothing in this comparison — it sees the most |

**Why this took a different company to build:** a production sensor needs deployment inside
customer infrastructure, permission to observe live traffic, an enterprise security review,
and a data-handling agreement. That is a months-long enterprise motion, not a GitHub App
install. Lightrun could ship it in one move only because they already had production
debugging sensors deployed for a different product.

---

## The copyability matrix

For each candidate product: who can build it, and how fast. **This is the table that decides
strategy.**

| Candidate product | CodeRabbit | Graphite | Verdict |
|---|---|---|---|
| Better review comments | Owns it | Owns it | **Dead.** Their core |
| Typed uncertainty on findings | ~1 week | ~1 week | **Dead as a feature.** They won't, because it lowers their marketed precision — but "won't" is not "can't", and won't evaporates the moment demand is proven |
| Auto-approve low-risk PRs | ~1 sprint | **Days** — they already own the merge queue | **Dead.** Graphite is closest to this of anyone |
| Published false-approval rate | ~1 month | ~1 month | **Weak.** They can publish one too. Less credible ≠ a business |
| Diff-scoped mutation testing | Weeks | Weeks | **Dead.** Already shipped by PIT, CircleCI, Autonoma, The Mutating Company |
| PR triage / risk prediction | Weeks | Days | **Dead.** GitHub ships it natively; Circuit Breaker published AUC 0.957 |
| Sandbox execution in CI | **Weeks** — they already sandbox | **Days** — they already orchestrate parallel CI | **Thin.** Thinner than assumed one turn ago |
| **Production runtime evidence** | **Cannot** without becoming a different company | **Cannot** without becoming a different company | **The only real wall** |

---

## Where the wall actually is

**Not sandbox execution.** CodeRabbit already spins up isolated sandboxes per review.
Graphite already runs CI across whole stacks in parallel. Adding targeted execution is an
extension of what both do, not a new capability. The middle-ground gap identified before
this research is **thinner than it looked**.

**The wall is production observability.** Seeing real variable values, real branch decisions,
and real downstream behaviour under live traffic requires an agent deployed inside customer
infrastructure. Neither a GitHub App nor a merge queue can get there without a different
security posture, a different sales motion, and a different company.

**And the same wall excludes us.** We have no deployed sensors, no enterprise install base,
and no production access. Lightrun's advantage is precisely the asset we would need years to
build.

---

## The principle this research produced

**A moat you can build in a week is one they can cross in a week. The cost *is* the moat.**

Every candidate on the matrix that was cheap to build was already built, already shipped, or
buildable by an incumbent in days. The only entry that holds is the one that is expensive,
slow, and requires access a GitHub App will never have.

That is a genuine strategic choice rather than a dead end: **build something heavy, or don't
build.** What has failed repeatedly is building something clever.

---

## What remains unverified

- **Whether CodeRabbit's sandbox runs customer tests** or only analysis tooling. This decides
  how thin the sandbox-execution gap really is, and it is the single most load-bearing
  unknown in this file.
- **Lightrun's two pain figures** (43%, +242.7%) are vendor-sourced and unaudited.
- **Graphite's 24h → 90min merge-time claim** is REPORTED, not independently confirmed.
- **Whether any buyer pays for runtime evidence** as a separate line item, or treats it as an
  observability-budget extension.

## The question this file cannot answer

Nothing here identifies a buyer. It establishes only which doors are open and which are
walled. The five customer conversations remain the only step that can distinguish a wall
worth climbing from one with nothing behind it.
