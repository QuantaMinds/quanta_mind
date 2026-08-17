# Design eight — quote-anchored findings, mechanically gated

**Seven designs failed. `AGENTS.md` says do not add an eighth without a fresh corpus and a bar
fixed first.** This is that document. It is written before any code is run.

**Why an eighth is defensible at all:** the five anchor designs all repaired the model's line
number — snapping it to a statement (p = 0.53), replacing it with a symbol name (p = 0.644),
widening it to ±10 lines (+2.6 points). **None removed it.** Qodo, the top tool of 49 on Martian's
offline layer at 67.9% precision, never asks for a line number: it asks for a **quote** and derives
the line from it. **That mechanism has never been tested here.**

---

## Where the design comes from

**Qodo PR-Agent** (`qodo-ai/pr-agent`, commit `1eea001`) — the anchor is `existing_code`, a snippet
from the diff; a reflection pass then *"detect[s] the line numbers … that correspond to the
`existing_code` snippet"*, and validates that the snippet *"matches or is accurately derived from
code lines within a `__new hunk__` section."*

**The literature says the same thing from the other direction.** *HalluJudge* names the defect —
fine-tuned LLMs "introduc[e] misaligned or fabricated details not grounded in code changes."
*SGCR* and the grounded-review work both conclude that every comment must be anchored to a
deterministic signal. **A framework using deterministic AST analysis reports 100% precision at
detecting the hallucination itself**, which is the part a parser can decide.

**And it is this project's own principle:** *deterministic beats clever; if a parser can answer it,
a model must not.*

---

## The design

**The model is never asked for a line number.** It emits, per finding:

| field | purpose |
|---|---|
| `quote` | **verbatim** code from a line the diff ADDS |
| `claim` | one sentence naming the defect |
| `fix` | the replacement code for that quote |

**Then a gate with no model in it.** Every check is a string operation:

| gate | rejects when | why |
|---|---|---|
| **G-quote** | the quote does not appear verbatim in an added line of the diff | this is the 87.3% defect, made unrepresentable |
| **G-line** | the quote appears, so the line number is *derived* — never emitted | prose and anchor cannot disagree when one computes the other |
| **G-fix** | `fix` is absent, or identical to `quote` | a finding whose author cannot write the replacement did not understand it |
| **G-outer** | the claim's backticked identifiers are absent from the diff | Qodo's rule: never question an entity that may be defined in the outer codebase |
| **G-nit** | the claim matches the zero-score list (docstring, type hint, comment, unused/missing import, exception type) | copied from their reflection prompt |

**Publish the survivors. Nothing else.**

---

## The corpus — fresh, and it has to be

**Thirty-two repositories are already burned** across the ranker samples, the aged corpus and
Martian's five. **None may be reused.**

Six Python repositories never touched by this project, sampled from merged pull requests:
`apache/superset`, `ray-project/ray`, `pydantic/pydantic`, `fastapi/fastapi`,
`mitmproxy/mitmproxy`, `PrefectHQ/prefect`. **Ten pull requests each, sixty total.**

---

## The bars, fixed now

| # | bar | rationale |
|---|---|---|
| **G1** | the **raw** quote-failure rate must be **below 87.3%** | quoting must beat the line-citing baseline it replaces, or the mechanism does not help. **The threshold is the measured defect rate, not a round number.** The rate among PUBLISHED findings is 100% by construction and is not a result — a check whose output cannot vary is not a check |
| **G2** | **published findings under 50% WRONG** under blind adjudication | **the bar the review half failed seven times.** Unchanged, and it is the only one that decides anything |
| **G3** | yield **≥ 1 published finding per 2 pull requests** | design 7 promoted zero findings and "passed" every quality bar by saying nothing. A filter that publishes nothing is not a reviewer |
| **G4** | the gate must **reject** something, and the **joint** distribution across gates is printed | a gate that fires on nothing is not a gate. **And the gates are not independent** — a model that cannot quote accurately probably also names identifiers that are absent, so G-quote and G-outer should correlate. Five marginals would hide that one gate is doing all the work and four are decorative. **Every gate is evaluated on every finding**, not short-circuited at the first failure |

**All four are reported. G2 decides.**

### A second pre-registered test, because the corpus is not neutral

**Function size predicts wrong-rate in this project's own data** — 45.9% wrong at ≤10 lines against
89.3% above 80. `ray` and `superset` are large mature codebases; `fastapi` and `pydantic` skew
shorter. **So the pooled number is a mixture, and a favourable result could be composition rather
than design.**

**Recorded before the run, and reported stratified:** the median added-lines-per-hunk for each
repository, and each published finding's own hunk size. **Hunk size is a proxy for enclosing
function length and is labelled as one.**

**This converts a confound into a test of the parked function-size hypothesis.** If the design
works *and* the length gradient flattens, that is a stronger result than either finding alone. If
the design only works on the short-function repositories, the pooled number is composition and must
be reported as such.

---

## Cross-referenced against the existing data before running

**The ceiling is known and it clears the bar.** Of design 1's 44 WRONG findings, the raters
recorded **24 as anchor-basis and 20 as semantics-basis**. If every anchor failure became CORRECT,
the wrong-rate falls to **30.3%** — under the 50% bar — and correct rises to 45.5%. **So a perfect
anchor fix is sufficient in principle. Semantics alone would leave 30.3% wrong, not 66.7%.**

**But the one experiment that relaxed anchoring says the conversion does not go that way:**

| design | anchor rule | WRONG | UNFALSIFIABLE | CORRECT |
|---|---|---|---|---|
| 2 — line, hard | strict | 82.1% | 10.3% | 0.0% |
| 4 — window, hard | ±10 lines | 66.7% | **20.5%** | 2.6% |

**The 15.4 points that left WRONG went 10.2 to UNFALSIFIABLE and 2.6 to CORRECT.**

### The distinction this design rests on, stated so it can be wrong

**Design 4 changed the SCORING RULE. Design 8 changes the GENERATION TASK.** Design 4 accepted a
looser anchor on findings produced exactly as before. This one forbids the model from emitting a
line number at all and requires it to copy code verbatim out of the diff.

**The hypothesis is that being forced to quote changes what the model says, not merely how it is
judged.** If that is false, this design is design 4 with extra machinery and will fail the same way.

**The discriminator, pre-registered:** if the published findings come back with **UNFALSIFIABLE
above 25%**, the design is relabelling rather than improving, **and that is a FAIL regardless of
the wrong-rate.** Converting WRONG into UNFALSIFIABLE is the failure mode design 4 already
demonstrated, and a wrong-rate that clears 50% by that route has not cleared anything.

---

## Predictions, written before the run

1. **The raw quote-failure rate is between 20% and 60%** — lower than 87.3% because quoting is an
   easier task than counting lines, but far from zero.
2. **G-outer fires more than expected**, above 10% of raw findings.
3. **Published wrong-rate lands between 35% and 55%** — i.e. genuinely near the bar, decided by
   which side of 50% it falls. **This prediction is uninformative by construction**: its range
   straddles the bar, so it cannot be wrong in a useful way. It is recorded so that nobody later
   reads it as a successful forecast. Prediction 1 is the one with a mechanism behind it.
4. **Yield is the binding constraint, not correctness.** I expect G3 to be the bar most at risk.
5. **UNFALSIFIABLE stays below 25%.** This is the prediction that separates the two mechanisms, and
   it is the one I would most expect to be wrong — design 4's 20.5% came from a weaker intervention
   than this one.

---

## What a pass would and would not mean

**Would:** one configuration cleared, on one fresh corpus, at n small. It licenses a **replication**,
not a product.

**Would not:** reopen `infer/`. Shipping requires this to hold on a second fresh corpus with the
bar fixed again, and the deterministic half is the roadmap either way.

**And a near-miss is a fail.** 52% wrong is a fail. This project has adjusted a threshold after
seeing a number exactly zero times, which is the only reason any of its figures are worth quoting.
