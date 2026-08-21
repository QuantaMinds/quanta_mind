# The filter: a mechanical gate, then a cross-family judge

**Written before the run. The bar is on the TRADE, not on precision.**

---

## Why the bar is not precision

**Precision rises whatever you delete, including at random.** Deleting half the pool at random takes
464 candidates to 232 and leaves precision unchanged only in expectation; any filter correlated with
anything at all moves it. A number that improves under a null operation is not evidence.

**The bar is the trade: false positives removed against true findings lost.** That is the only
quantity that says whether the filter discriminates.

## What is already known, and it is discouraging

**Filter mechanisms have failed FOUR times in this project's own record, not three.**

| # | mechanism | result |
|---|---|---|
| 1 | snap anchors to statements | 36.4% of anchors moved, **wrong-rate unmoved, p = 0.53** |
| 3 | reject imprecise anchors | survivors 76.5% wrong vs rejected 86.4% — **+9.9 points, bar was +15** |
| 10 | hard gate on units > 40 lines | 65.2% → 59.6%, **p = 0.281**, and it discarded **2 of 12** correct findings |
| 13 | execution gate | **INVERTED AND SIGNIFICANT.** Where the model proves its claim the code is *less* likely to be fixed: 36.5% vs 50.5%, **p = 0.003** |

Thirteen predictions in that record, ten wrong. **#13 is the one to keep in view: a filter can be
significantly backwards, not merely null.** Greptile independently reports LLM severity scoring as
"nearly random". Qodo and Greptile shipping working filters is proof the class can work; it is not
proof it works here.

**And two same-family judge arms have already failed**, measured 2026-08-20 on this corpus:

| judge | FPs dropped of 364 | TPs lost of 100 | discard purity | precision | F1 |
|---|---|---|---|---|---|
| `gemini-2.5-pro` | 95 (26%) | 3 | **96.9%** | 28.0% | 37.3% |
| `gemini-2.5-flash` | 121 (33%) | **16** | 88.3% | 26.7% | 34.4% |

Both discard more purely than the 78.4% base rate, so there is signal. Neither is near the bar, and
rewriting the prompt from a truth test to a materiality test changed the keep-rate from **79% to
80%** — nothing.

## Cross-family is baseline practice and is not claimed as ours

The 2026 guidance is flat: **never use the same model family as generator and judge.** An April 2026
study on IFEval — programmatically verifiable rubrics — found a judge up to **50% more likely** to
mark its own generator's failures as satisfied, and the effect persists on entirely objective
criteria. Our 34.9%-agreement result is a local instance of that, not a discovery.

**Three corrections carried into this design:**

- **Ensembling does not eliminate self-preference**, it mitigates it. A panel is better than one
  cross-family judge, not a solution.
- **The bias is not uniform in direction.** One 2026 benchmark has GPT-5.2 and Gemini-3.1 Pro giving
  their own families **75–84%** win rates while Claude Opus 4.7 *under*-rates its own at
  **10.6–41.2%**. **An under-rating judge deletes true findings.** The pairing must be measured, not
  chosen on principle — which is why arm B reports TPs lost as a first-class number.
- **Calibrate against humans.** The recommendation is agreement above **0.85** against a human
  baseline. We hold **207 hand-adjudicated findings**. That is the calibration set, and it is what
  the independent-grader debt carried across four designs finally buys.

---

## The two arms

**Arm A — the mechanical gate alone.** The decidability rule, no model: a finding whose claim needs a
fact the diff cannot supply is dropped before any inference. Measured at **0 of 14 wrong** among
decidable findings against **9 of 15** among the rest, Fisher **p = 0.0007** — with the caveat this
project already wrote down: n = 29, wide intervals, and the rater graded WRONG using reasoning
correlated with the gate's rule, so **the separation is partly structural**.

**Arm B — the gate, then a cross-family judge** on what survives.

**A is run first and reported alone.** If the rule does the work, the model judge is unnecessary
cost, and this project has twice shipped a mechanism whose credit belonged to a different one.

---

## The bars, fixed now

Let **D** = false positives removed, **L** = true findings lost, from the 464-candidate corpus
holding 100 true and 364 false.

| bar | rule |
|---|---|
| **B1 — the trade** | **D / L ≥ 15.** Every true finding lost must buy at least fifteen false ones removed. The base rate is 3.64 false per true, so a filter that discards at random scores 3.64; **B1 demands four times better than chance** |
| **B2 — volume** | **D ≥ 180**, half the false positives. Below that the arm cannot reach parity with our own suppressed arm however pure it is |
| **B3 — recall floor** | **L ≤ 15.** Losing more than 15 of 100 true findings fails outright, whatever D is — the under-rating failure mode above |
| **B4 — calibration** | judge agreement **≥ 0.85** against the 207 hand-adjudicated findings, computed BEFORE the arm is read. Below it the run measures the judge and is reported VOID |

**All four must hold. A near-miss is a fail.** Wilson intervals printed beside D/n and L/n; an
interval spanning a bar is INCONCLUSIVE and is not a pass.

**Reported whatever happens:** D, L, D/L, the discard purity against the 78.4% base rate, and
precision — **precision last, and never alone.**

## The corpus

**The 464-candidate arm is BURNED for bar-setting**: two judge arms have been read off it and the
bars above were chosen knowing its numbers. It may be used to develop the gate. **The bars are
adjudicated on a fresh corpus the filter has never seen**, drawn by the same rule as
`design14-model-lever-preregistration.md` and verified unburned before selection.

## The rival claim, and what the data can actually support

We hold every competitor's **raw candidate text** and their Claude-Opus judge's per-candidate
true/false labels. So a real measurement is available: **run our gate over Qodo's and Greptile's
known false positives and count how many it would have removed.**

**What that shows: whether a mechanical gate would have caught what their filter published.** It is
a claim about our gate on their output.

**What it does NOT show: that their judge is same-family, or that self-preference caused it.** Their
architecture is unobservable from output text. **Any pitch asserting their judge is same-family is
an assumption, and this measurement cannot license it.**

> **The benchmark data lives under `/private/tmp/.../6063c1dc-.../scratchpad/`, hardcoded in
> `research/phase0/bench/corpus.py`** — a scratchpad belonging to a dead session, on a path the OS
> may clear. This project has been bitten by exactly this before. **Copy it into the repository's
> own storage before any run depends on it.**

---

# Arm A — the result. It fails, and it fails BELOW CHANCE.

**Measured directly on the 24 candidates the gate dropped, not by differencing two judge passes.**

| | |
|---|---|
| gate fired on | **24 of 464** candidates (5.2%), zero model calls |
| **D** — false positives removed | **14** |
| **L** — true findings lost | **10** |
| **D/L** | **1.40** |
| chance value of D/L on this pool | **3.64** |

| bar | value | required | verdict |
|---|---|---|---|
| B1 trade D/L | **1.40** | ≥ 15 | **FAIL** |
| B2 volume D | **14** | ≥ 180 | **FAIL** |
| B3 recall L | 10 | ≤ 15 | PASS |

**B3 passes only because the rule barely fires.** A filter that touches 5% of the pool cannot lose
much recall; that is not a property worth crediting.

**D/L = 1.40 against a chance value of 3.64 means the gate discards TRUE findings at roughly two
and a half times the rate random deletion would.** This is prediction 13's outcome, not prediction
1's: **inverted, not null.** Of the 24 findings it removed, **10 were correct**.

## Why it inverted, and it is a failure this project has already had once

**The keyword list was tuned on design ten's failures** — `does not exist`, `no such version`,
`future date`, `assertion is incorrect` — which were Python-library findings about package
registries and dates. Recomputed on design ten's own 32 adjudicated findings the rule genuinely
separates: kept 20 at 10.0% wrong against dropped 12 at 75.0% wrong, **Fisher p = 0.0003**.

**On this corpus — cal.com, discourse, grafana, keycloak, sentry — it inverts.** The same tokens
appear inside true findings about web application code, where "will fail" describes a real defect
rather than an unverifiable claim about a registry.

**The evidence ledger already records this exact collapse:** *"the word-list filter — beautiful
in-sample, dead on fresh data at p = 0.16"*, and *"review content is not keyword-shaped"*. This is
the same failure with a different word list.

## Two corrections that follow, and both are against my own claims

**1. The mechanical gate comes OFF the differentiator list.** I put it at number one after removing
cross-family judging from that list. It fails its own bars on the first corpus it was tested against
that it was not built on. **It may not be pitched, and the p = 0.0007 figure describes the MODEL
gate, not this rule** — a second attribution error, which is the trap of crediting a mechanism with
work that belongs to another, for the third time in this project.

**2. Arm B changes shape.** It was specified as *gate, then cross-family judge*. The gate half is
now measured as harmful on this corpus, so stacking a judge on top would inherit a filter that
removes 10 true findings for 14 false ones. **Arm B is a cross-family judge ALONE**, and the gate is
withdrawn pending a rule that survives a corpus it was not tuned on.

## What survives

**The decidability CONCEPT is not refuted; the keyword implementation of it is.** The model gate
separated at p = 0.0001 on design ten and has never been tested out-of-sample. That is a different
mechanism with a different cost — it is inference, not a rule — and any future claim about it must
say which of the two produced the number.
