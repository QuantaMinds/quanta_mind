# The history signal — plan

**Written 2026-08-12.** Belongs on a `feat/history-signal` branch; this file is written
before any code, per `AGENTS.md` “Plan before you edit”.

**Status: backtest first, product second.** No product code until the backtest clears the
stop rule in “Stop rule, written before the run”.

---

## The product in one sentence

Every AI reviewer reads the diff in isolation. **We read what the repository has done to this
symbol before**, and when the history says a companion change is missing, we name it.

---

## What the measurement said, and what it implies

On the reviewer draw: CodeRabbit left an inline finding on **10 of 65** pull requests that
later required a symbol-level fix, against a **23.9%** flag rate on the ones that did not.
Excluding the dominant repository the catch rate is 8 of 34. Either way the reviewer is
silent on the large majority.

Those 55 silent breakages are, by the construction of the corrected outcome rule, pull
requests where **a later commit had to fix a symbol the pull request modified**. The product
hypothesis is that a usable fraction of those symbols had already required follow-up fixes
*before* the pull request merged, and that a signal built from that history would have fired
where the reviewer did not.

**That hypothesis is testable on data already collected. It is not assumed here.**

---

## Why an incumbent cannot copy it quickly

`ARCHITECTURAL_MOATS_2026-08.md` records the architectural fact: the category reads the diff,
reasons about it, and comments. The repository's rework history is not an input to any of
them.

The barrier is not the history — anyone can run `git log`. The barrier is that **file-level
attribution is 67.9% wrong** (36 of 53 verdicts in `research/phase0/results/a54_confound.json`
share no symbol with the pull request, reproduced at 36.1% and 35.7% survival on two later
corpora). A history signal built on the file rule fires on almost everything and means
nothing. The corrected symbol-level rule is what makes the signal precise enough to put in a
comment, and it is the one piece of instrument this project owns outright.

**Prior art to state up front rather than be caught by.** Change coupling is not new —
Zimmermann et al., *Mining Version Histories to Guide Software Changes*, ICSE 2004 — and
CodeScene ships change coupling as a product today. The claims here are symbol granularity,
the corrected attribution rule, and the join to what the reviewer said. Anything broader is
overclaiming.

---

## The signals, ranked by how directly the collected data supports them

1. **Missing companion change.** Historically, when symbol X changed, symbol Y changed with
   it. X is in this diff and Y is not. **This is the only signal that yields an action rather
   than a warning**, and it is the one to build first.
2. **Symbol rework rate.** X required a follow-up fix in N of its last M changes.
3. **Agent-authored priors.** Prior machine-authored changes to X required follow-up at rate
   R. Depends on authorship detection, which is commoditising — treat as a modifier, never as
   the primary signal.
4. **Reviewer silence on a symbol with history.** The join no incumbent can compute. Ship
   last; it is the marketing artefact, not the mechanism.

---

## The backtest

The point of the backtest is that it produces a table with **the same shape and the same
denominators** as the reviewer measurement, so the product and the incumbent are compared on
one corpus.

**Population.** The pull requests already classified by the corrected rule: 65 broke, 272 did
not. Repository identity retained on every row — the reviewer result was one repository, and
this one must be reported with leave-one-out from the start rather than after someone asks.

**Replay.** For each pull request, compute the signal from the repository state at its merge
point, **using only commits reachable before that point**.

**Output.** The 2×2, the catch rate, the flag rate on the clean arm, Fisher exact, a
cluster-robust interval at repository level per `PHASE0_PREREGISTRATION.md` requirement A8,
and leave-one-out for the dominant repository. Attrition counted and reported, never coded as
a pass.

### The correctness requirement that decides whether the backtest means anything

**Lookahead is the failure mode, and it produces a spectacular fake result.** A signal that
sees commits after the merge point knows the answer. This is the class `AGENTS.md` names:
*ask what a check outputs when the thing it checks is broken; if the answer is the same
thing, it is not a check.*

Required before any backtest number is quoted anywhere:

- The replay is bounded by commit SHA, not by date. Dates are rewritten by rebases.
- **A sabotage test that breaks the whole mechanism, not the entry point.** Build the signal
  deliberately from future commits and confirm the score moves. If a future-leaking signal
  scores the same as a bounded one, the harness is not measuring what it claims and the
  number is void.
- Attrition from unbuildable or unscannable repositories reported as its own arm. The prior
  study's unanalysable arm broke at the highest rate of three, so silently dropping it biases
  the result in the flattering direction.

---

## Stop rule, written before the run

The comparison target is the incumbent on the same corpus: **10 of 65 caught at a 23.9% flag
rate on the clean arm.**

- **Proceed** — catch rate at least **double** the reviewer's at **no more than** its flag
  rate, and the result survives leave-one-out of the dominant repository.
- **Stop** — catch rate under 20%, or a flag rate above 25%, or the effect disappears under
  leave-one-out.
- **Void, do not interpret** — the sabotage test fails, or the signal fires on more than half
  of all pull requests.

A signal that fires on most pull requests is the coverage gate again: 45% firing, zero
discrimination. That failure has already happened twice in this repository and the stop rule
exists so it cannot happen a third time under a new name.

---

## Build order, after and only after the stop rule clears

1. **Missing-companion-change detection, offline.** No GitHub App, no hosting. A command that
   takes a repository and a pull request and prints the finding or prints nothing.
2. **The comment.** One finding, citing the commits it is derived from, with a rate and a
   denominator. No prose, no model, no severity taxonomy.
3. **The GitHub App.** `contents:read`, `pull_requests:write`. No merge rights — read-only
   into the repository, write-only into a comment.
4. **The reviewer join.** `checks:read`, to add the line stating what the reviewer said about
   the same symbol.

**No inference and no customer keys at any step**, per the decision recorded in
`PRODUCT_PLAN_2026-08.md` under “No inference. No keys. No BYOK.” Every number in the comment
is a query over the customer's own history.

---

## What would falsify this plan

- The backtest fails its stop rule.
- The sabotage test does not move the score — the harness is measuring lookahead.
- Missed breakages turn out to have **no prior history** on the changed symbol, which would
  mean the mechanism has nothing to fire on regardless of how it is tuned.
- Design partners disable it, which is the outcome any comment-generating tool earns when it
  is wrong often enough to become noise.

---

## Open dependency, blocking

**The reviewer measurement's outputs are not in this repository.** No files under
`research/phase0/results/` correspond to the 126-, 726-, or 337-pull-request runs, and there
are no commits carrying them. The backtest population is defined by those records, so the
first task on the branch is committing the run script and its outputs. Until then the
population above exists only in a conversation.
