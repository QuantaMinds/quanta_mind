# Architectural drift — pre-registration

**Written 2026-08-31, before any repository was walked for this question.** Committed before the
measurement runs, so the bars cannot move to meet the answer. Same discipline as
`blast-radius-preregistration.md`, whose bar was honoured when the result did not clear it.

## The claim being tested

D2e states it as a customer would: *"Team members implement parts of the system differently from
the original design."* That is a claim about **divergence**, and the row asserts divergence is
measurable from the import graph over time.

**THIS IS THE CATEGORY'S HEADLINE CLAIM, WHICH IS A REASON TO TEST IT AND NOT A REASON TO BELIEVE
IT.** The "deep context beats diff-level review" pitch names four things: multi-repository
dependency tracking, semantic analysis of intent, historical patterns, and **architectural drift
that simple linting rules would miss**. Two of the four we have already built and one we have
already measured:

| the claim | where we are |
|---|---|
| logic duplication the diff cannot see | **built** — D2c, and the three groups it found in `pallets/flask` are the ones the maintainers later hoisted into a shared base class |
| dependencies across repositories | **declared, not discovered** — D3a ships the declaration; D3b is gated on a design partner with a second repository |
| historical patterns | **this is the ranker**, and it is the only thing here that has replicated out-of-sample |
| architectural drift | **this document** |

**And the graph has already lost once.** Blast radius was the other deep-context signal, it was
pre-registered, and it came back INCONCLUSIVE with prior-fix history beating it 65-13 where the two
disagreed. A category consensus is not a measurement, and the same graph that failed to rank files
is the graph this proposes to compute drift from.

**The question this answers is not "can we compute drift".** We can compute a number and call it
drift; `parse/imports.py` already extracts labelled edges for any file at any commit. The question
is whether that number **separates an outcome anybody cares about**, which is the only thing that
makes it a signal rather than a story.

## The mechanical definition

For one library file, over its own commit history:

- **`churn`** — the number of commits that touched it.
- **`shifts`** — the number of those commits at which its resolved in-tree import set CHANGED.
- **`drift = shifts / churn`** — the share of edits that moved the file's dependencies.

**`drift` IS A RATE AND THAT IS THE WHOLE DESIGN.** A raw count of import changes is a proxy for
"this file was edited a lot", and a file edited a lot is more likely to be returned to by a later
fix for reasons that have nothing to do with architecture. Dividing by churn is the cheapest
available control for the confound that would otherwise manufacture the result.

## The outcome

**Defect return**, the same outcome the shipped ranker is measured against: does a later commit
whose message marks it as a fix touch this file? Reusing it is deliberate — a new signal judged
against a new outcome can be made to win by choosing the outcome.

## The population

Library files only (`parse/suite_reach.is_library`), with **`churn` ≥ 10**, in repositories with a
real history. Below ten commits `drift` is a ratio of small integers and moves in steps of 0.1 or
more.

## The bars, fixed now

| | |
|---|---|
| **B1 — enough to decide** | ≥ 200 files across ≥ 3 repositories. Below that, report INCONCLUSIVE and do not reach for a fourth repository |
| **B2 — drift separates the outcome** | fix-return rate in the top drift tertile exceeds the bottom by **≥ 10 percentage points**, Fisher p < 0.01 |
| **B3 — and not because of churn** | the same comparison **within** a churn-matched stratum must survive. If B2 holds overall and fails within strata, the finding is churn wearing drift's name and D2e is CLOSED |
| **B4 — it must beat what ships** | drift must add to prior-fix history, not restate it. Reported as the fix-return rate of high-drift files that fix history did NOT already rank in the top three |

**Any bar unmet closes D2e**, and the row records the numbers rather than staying open for a
better repository. `blast-radius-preregistration.md` is the precedent: fewer than 20 discordant
pairs was reported as inconclusive and D2d has now been dropped on it.

## What would make this worth building even if B2 fails

Nothing. A drift number nobody can act on is a paragraph in a comment about the customer's
architecture that we cannot support — the most expensive kind of sentence this product can print.

## Registered before the run

- The three tertile boundaries are computed from the observed distribution, not chosen.
- Repositories are whatever `.verify-clone` and the pinned fixtures already hold. **No repository
  is added after seeing a result**, which is the rule `research/phase0/corpus_age.py` enforces
  elsewhere and the one `check_burned_corpora.py` exists for.
- A file whose import set never resolves in-tree (`drift` undefined) is EXCLUDED and counted, not
  scored as zero.

---

## Amendment, recorded after the run — the instrument shared a denominator

**`drift = shifts / churn` and the outcome `fix_rate = fixes / churn` are both over `churn`.** Two
ratios with a common denominator move together by construction. This was not seen when the bars
were written and it is recorded here rather than quietly corrected, because a pre-registration that
edits itself after the result is not one.

**The verdict does not change.** A shared `1/churn` induces a POSITIVE association; B2 asked for
positive and observed negative, so the artefact could only have helped the hypothesis and it still
failed. **Any future attempt must not measure a rate whose denominator is also the outcome's** —
count shifts against a fixed window, or model the outcome per commit.

---

# Second run — a repaired instrument, registered before the clones

**Written 2026-08-31 after the first run closed D2e, and before any of the three new repositories
was cloned.**

## Why this is a repair and not a hunt

**The reason for re-running is the INSTRUMENT, not the answer**, and the two are not the same
justification. The first run's `drift` and its outcome shared a `1/churn` denominator, so part of
any association between them was arithmetic. That is a defect in the measurement, and repairing a
measurement and re-running is what `research/` is for.

**"The null was disappointing" would NOT justify this.** The first run met its own B1 — 305 files
across four repositories was registered as enough to decide — so adding repositories to see whether
the answer improves is the move this document exists to prevent, and the one D2d was dropped for
refusing. **If these bars are unmet, the prior verdict stands and D2e stays closed.**

## The repaired design: one observation per commit, no shared denominator

For each library file, walk the commits that touched it in order. For commit *i*:

- **`shifted`** — the file's resolved import set differs from what it was at the previous commit
  touching this file. Binary.
- **`fix_follows`** — any of the **next three** commits touching this file is fix-shaped. Binary.

**Neither variable is a ratio, and they share no denominator.** The unit is a commit-on-a-file, not
a file, so a busy file contributes many observations rather than one averaged number — which is
also why the first run's file-level averages were dominated by whichever files had the most history.

Compare **P(fix_follows | shifted)** against **P(fix_follows | not shifted)**.

## The bars, fixed now

| | |
|---|---|
| **B1 — enough to decide** | ≥ 5,000 commit-events across ≥ 3 repositories |
| **B2 — a shift predicts a fix** | P(fix \| shifted) exceeds P(fix \| not shifted) by **≥ 5pp**, Fisher p < 0.01. **The direction is registered**: D2e claims drift precedes trouble, so a negative gap of any size is a FAIL, not a discovery |
| **B3 — not one repository carrying it** | the gap is positive in **every** repository. `pallets/werkzeug` gave −9 to −21pp alone last time while the pool gave nothing, and that asymmetry is the whole reason for this bar |
| **B4 — it adds to what ships** | the gap survives inside strata of the file's prior-fix count, which is what the ranker already uses |

**Any bar unmet and D2e stays closed, permanently.** No fourth repository, no widened window, no
second outcome. The three are `saltstack/salt`, `keras-team/keras`, `ipython/ipython`, all confirmed
unspent before cloning, and they are named here so the set cannot grow after a result.

---

# The second run is WITHDRAWN before it ran, and the reason is that it tested the wrong thing

**Withdrawn 2026-08-31, after reading what the competition actually detects.** Not one repository
was cloned for it. **ADVISORY** — no mechanism, and the reason is stated rather than the tag being
a shrug: no guard can decide that a hypothesis is a poor description of a market claim, and one
that appeared to would be asserting more than it can test.

## What went wrong, and it was not the arithmetic

Both runs asked whether **a file whose imports churn attracts more later fixes** — a per-file
historical risk signal. That question is coherent, it was measured properly the first time, and the
answer is no.

**It is not what "architectural drift" means to the people shipping it.** Qodo's drift detection
flags: reimplementation of existing authentication and validation logic in other modules; modified
response formats consumed by other services; deviations from team standards; function-signature
violations, broken API contracts and schema drift — **read against registered consumer
repositories**. Greptile's is whole-codebase context applied to the change in front of it.

**Every one of those is a claim about THIS CHANGE against the codebase as it stands. None is a
statistic about a file's past**, and none of them predicts defects — they assert inconsistency,
which a reviewer judges directly. We picked an outcome their feature never claimed and then
measured ourselves failing to hit it.

| what they flag | where we are |
|---|---|
| logic reimplemented elsewhere | **built** — D2c |
| deviations from declared standards | **built** — D1a, D1b, D1f |
| signature and contract changes against consumers | **not built** — D3b |
| registered consumer repositories | **built** — D3a, and "registered" is our word too |

## What this means for D2e

**D2e stays closed as written**, because what it wrote down was the churn statistic and that is
measured and dead. The three things a customer means by architectural drift are D2c, D1b and D3b —
two shipped, one gated on a design partner with a second repository.

**The first run's finding stands and its value goes up**: it is now evidence that the *obvious*
formulation of drift does not work, which is worth having on record the next time somebody proposes
a churn-based risk score.

**What would have caught this earlier is a question, not a mechanism:** before registering bars,
state what the competitor's version of the feature actually asserts, and check that the outcome
being measured is one they would recognise. The pre-registration named the market claim and then
tested a proxy for it without saying it was a proxy.
