# Pre-registration — adjudicating the first 66 findings

**Written before a single finding was read.** The whole point of fixing a threshold now is that
it cannot be set backwards from whichever answer arrives, which is the failure this project
already corrected once on the model-certification rule.

Findings under adjudication: the **66** emitted by `gemini-2.5-pro` across 68 requests on 23
merged pull requests, recorded in `research/phase0/results/vertex_cost_c3.json`.

---

## The four buckets

Every finding lands in exactly one. The last two are not hedges — together they decide whether
the product is *usable* rather than merely *true*, and the field's own failure is in that gap: an
audit of one market leader found 36% noise while the same tool was 35% genuinely useful.

| bucket | test |
|---|---|
| **CORRECT** | The claim is true of the code shown, `line_a` / `line_b` point at the lines that make it true, and it is worth a reviewer's attention |
| **WRONG** | The claim is false of the code shown, or the line anchors do not support it |
| **UNFALSIFIABLE** | May be true, but cannot be decided from the function and diff alone — it needs the caller, the runtime, or the rest of the repository. **A reviewer cannot act on it either**, which is why it counts against the product and not merely against the measurement |
| **TRIVIAL** | True, anchored, and not worth a comment. This is the bucket the competitors fill |

## Blinding

**Findings are adjudicated in shuffled order with the rank hidden.** Otherwise the rank-1 deep
read gets graded generously and the allocation architecture validates itself. Rank is rejoined
only after every verdict is fixed, and the rank-1 versus rank-2 comparison is then read off — if
the two ranks produce similar quality, **the allocation architecture is not buying what it
claims**, and that is a result about the ranking half discovered inside a test of the review half.

**A finding with a correct diagnosis and wrong line numbers is WRONG.** The schema exists so the
verifier can check anchors; anchors that do not survive checking are the failure the verifier is
built to catch, and grading them generously here would hide exactly what stage four must not miss.

---

## The stop thresholds, fixed now

Let **C**, **W**, **U** be the counts, and *n* = C + W + U = 66.

| reading | rule | what it means |
|---|---|---|
| **STOP — the review half does not work** | **W / n ≥ 0.50** | Half the published findings are false. No cost optimisation, model choice, or coverage line rescues that. The company is the measurement layer alone — which the evidence ledger already supports as a position |
| **REBUILD the inference step** | 0.30 ≤ W / n < 0.50 | Worse than the field's published 49–76% precision band. Not fatal, but nothing may be published until it moves |
| **PROCEED, with the residual as the product** | W / n < 0.30 **and** U / n < 0.50 | Consistent with the field, and the majority of findings are decidable from what the reviewer is shown |
| **PROCEED but the schema is wrong** | W / n < 0.30 **and** U / n ≥ 0.50 | The model is not lying, it is speculating. The fix is the schema forcing evidence, not a better model |

**And a second binding number, against the field rather than against zero.** The independent
benchmark puts the field at **49–76% precision**. Our comparable quantity is **C / n** — findings
that are true, anchored and worth reading. **If C / n < 0.49 we are below the bottom of the field
while claiming to be quieter than it**, which is the one position the product cannot hold, because
quietness is only a virtue if what breaks the silence is right.

**The binding number is W / n, and the threshold is 0.50 for stopping and 0.30 for rebuilding.**
Wilson intervals will be printed beside each, and at n = 66 the interval is roughly ±11 points —
stated now so the result is not over-read later. **A point estimate landing between 0.30 and 0.50
with an interval spanning both is an inconclusive result and will be called one.**

---

## Two things recorded alongside, not graded

**Findings per pull request.** 66 findings across 23 pull requests is ~2.9, and the product
promises **one comment**. So the selection rule is unbuilt and undefined. Record the distribution
and whether the highest-confidence finding per PR is the one a human would have wanted — the
second is an observation, not a measurement.

**The 8 empty arrays.** For each, decide whether the silence was correct or whether a defect was
present and missed. **This is the coverage line's honesty tested directly**, and it is the one
place where being wrong is worse than being noisy.

---

## The conflict, stated

**I wrote the prompt and I am grading its output.** That is the weakest part of this exercise and
no protocol inside it fixes the incentive. Two partial mitigations: every verdict is recorded with
the specific line of code that decides it, so a second reader can overturn it cheaply; and the
thresholds above are fixed before reading. **A second rater is required before any of this is
published**, exactly as the ranking result required one and got it at κ = 0.92.

---

## What this does not do

It does not measure whether the findings are *useful*, only whether they are *true*. A correct
finding nobody cares about is a different failure, and the field's 36%-noise problem is exactly
that failure. Usefulness needs the customer, and that is C4.


---

# RESULT — read 2026-08-14, after the thresholds above were committed

**All 66 findings adjudicated, shuffled, blinded to rank.** Verdicts with the deciding line are in
`research/phase0/results/adjudication_verdicts.json`.

| bucket | count | share | Wilson 95% |
|---|---|---|---|
| **CORRECT** | 6 | **9.1%** | 4.2% – 18.4% |
| **WRONG** | 44 | **66.7%** | 54.7% – 76.8% |
| UNFALSIFIABLE | 5 | 7.6% | 3.3% – 16.5% |
| TRIVIAL | 11 | 16.7% | 9.6% – 27.4% |

**The pre-registered STOP condition fired, and not marginally.** W/n = 66.7% against a threshold
of 50%, and **the lower bound of the interval is 54.7% — above the threshold**, so this is not a
call that turns on sampling noise. C/n = 9.1% against the field's 49% floor.

## The split inside WRONG is the whole diagnosis

| failure | count | share |
|---|---|---|
| **anchor only** — the line numbers do not point at the code the claim is about | 24 | **36.4%** |
| **semantically wrong** about the code | 20 | **30.3%** |

**These have different fixes and only one of them is a model problem.** The anchor failures are
systematic and dull: the model cites blank lines, comments, closing parentheses, and argument
lines one or two below the statement it is describing. 19.7% of all 132 cited anchors land on
something that is not a line of code at all, and 12.1% fall outside the function the model was
shown. That is a tooling problem — anchors can be snapped to the nearest enclosing statement by a
parser that already exists in this codebase.

**But fixing it does not save the product, and the bound is worth stating precisely.** If every
one of the 24 anchor failures were repaired *and every one turned out to be correct* — the most
generous assumption available — C/n reaches **45.5%**, which is **still below the field's 49%
floor**. The ceiling of the optimistic case does not clear the bottom of the competition.

## What the rank comparison says about the allocation architecture

| rank | findings | correct | wrong |
|---|---|---|---|
| 1 (deep) | 27 | 11.1% | 66.7% |
| 2 | 20 | 10.0% | 60.0% |
| 3 | 19 | 5.3% | 73.7% |

**Flat.** The rank-1 deep read is not producing better findings than rank 3. On these counts
nothing is significant and it should not be over-read — but there is no sign here that the
allocation is buying quality, which is the thing it exists to buy. Found inside a test of the
review half, about the ranking half, because the grading was blinded.

## The 8 silences

**Every one returned `finishReason: STOP`.** None was a truncation wearing the appearance of
silence — the defect from the crashed run is genuinely fixed, and the mechanism that would make
silence untrustworthy did not fire.

**One thing to watch rather than to conclude: 6 of the 8 pinned the 4,096 thinking cap and then
said nothing.** Under a lower budget that is exactly where truncation-shaped silence would appear.
**Whether each silence was *correct* — no defect present — was not independently audited**, and
that is a gap in this exercise rather than a finding.

## Findings per pull request

66 findings over 23 pull requests, **2.9 per PR**, against a product that promises **one comment**.
The selection rule is unbuilt, and this result changes what it has to do: it is not choosing the
best of three good findings, it is choosing one from a set where two of three are wrong.

## The reading

**W/n ≥ 0.50: stop building the review half in this configuration.** Not "tune the prompt" — the
threshold was fixed in advance precisely so that this reading could not be renegotiated once the
number arrived.

What this does **not** say: that the model cannot review code, that a different prompt or schema
would fail the same way, or that the ranking half is affected. The ranking half keeps its ten
measurements. **What it says is that the first honest look at the review half found it below the
floor of the field it was going to compete with, and that the company as an attention-allocation
and measurement layer — the position the evidence ledger already supports — is the one the
evidence actually reaches.**

## The conflict, restated because it now matters more

**I wrote the prompt and I graded its output, and the result is bad.** That direction is the less
suspicious one for an author-grader, but it is still one rater. Every verdict carries the line
that decided it so a second reader can overturn it cheaply. **A second rater is required before
this number is used to make the decision it implies.**


---

# SECOND RATER — protocol fixed before any verdict was returned

The result above rests on one reading by the person who wrote the prompt. This section is written
**while the second rating is still running**, so the way it is read cannot be chosen after seeing
whether it agrees.

## Setup

Six independent adjudicators, each given the same rubric and a disjoint block of 11 findings, with
the claim and the code around both cited lines. **Blind to the first rater's verdicts, to each
other, and to which rank produced each finding.** They were told the pull requests are merged, and
given the same anchor rule and the same four buckets.

## What is computed

| quantity | why |
|---|---|
| raw agreement on the 4-way verdict | the headline |
| **Cohen's κ** | agreement corrected for chance, the same instrument that replicated the ranking result at κ = 0.92 |
| agreement on the binary WRONG / not-WRONG | the only distinction the STOP threshold depends on |
| **W/n under rater 2 alone** | does the decision survive a reading that is not mine |

## The decision rules, fixed now

**The STOP conclusion stands only if rater 2 independently reaches W/n ≥ 0.50.** If rater 2's W/n
lands below 0.50, the first reading is not confirmed and the conclusion is **suspended, not
averaged** — a decision this consequential does not get to be rescued by pooling two disagreeing
readings into one convenient mean.

| κ | reading |
|---|---|
| ≥ 0.70 | The rubric is reproducible. Whichever way the counts fall, they mean something |
| 0.40 – 0.70 | Moderate. The result is directional; the specific percentages are not quotable |
| < 0.40 | **The rubric is the problem, not the findings.** Nothing here is usable and the exercise must be redesigned before it decides anything |

**Where they disagree, the disagreements get read, not discarded.** A systematic pattern — for
instance rater 2 accepting anchors the first rater rejected — is a finding about the *rubric* and
must be reported as one, because the anchor rule is the single most consequential judgement call
in the protocol and it was mine.

## The limitation that survives all of this

**Rater 2 is the same model family as rater 1.** Independent context, independent reading, blind —
but correlated priors. This is a genuine replication of the *reading*, and it is not the
independent-family check the project used on the ranking result. **A human rater, or one from
another family, remains the standard this has not yet met**, and any published version of this
number must say so.

Gemini is not eligible: it wrote the findings, and an author grading its own work measures
something else.


---

# SECOND-RATER RESULT

| bucket | rater 1 | rater 2 |
|---|---|---|
| CORRECT | 6 (9.1%) | **3 (4.5%)** |
| **WRONG** | 44 (**66.7%**) | 49 (**74.2%**) |
| UNFALSIFIABLE | 5 (7.6%) | 5 (7.6%) |
| TRIVIAL | 11 (16.7%) | 9 (13.6%) |

| | |
|---|---|
| raw agreement, 4-way | **86.4%** (57/66) |
| **Cohen's κ, 4-way** | **0.711** |
| agreement on WRONG vs not — the only cut the threshold uses | **92.4%** |
| κ on that binary | **0.819** |

**Against the bands fixed before the rating: κ = 0.711 clears 0.70, so the rubric is reproducible
and the counts mean something.** On the distinction that actually decides the question — is this
finding wrong — the two readings agree 92.4% of the time at κ = 0.819.

**The STOP condition is independently confirmed.** Rater 2 alone: **W/n = 74.2%, Wilson
62.6%–83.3%**, against a threshold of 50%. The interval's lower bound clears the threshold by more
than twelve points.

## Every disagreement that moved, moved against the first rater

Nine disagreements. **Five made a finding worse; none rescued one.** There is no case where rater
2 accepted a finding rater 1 called wrong.

| # | rater 1 | rater 2 | |
|---|---|---|---|
| 20 `init_model_state` | UNFALSIFIABLE | **WRONG** | anchor is the import inside the branch, not the condition above it |
| 28 `test_challenge_state…` | CORRECT | **WRONG** | anchor is the `continue`, not the `if` that performs the check |
| 42 `is_quantization_compressed` | UNFALSIFIABLE | **WRONG** | `is_quantized` *itself* dereferences `quantization_config`, so it cannot be the safe guard the claim assumes |
| 51 `load_model` | UNFALSIFIABLE | **WRONG** | anchor is an argument line, not the assignment |
| 59 `_credential_bound_workflow` | TRIVIAL | **WRONG** | anchor is inside the return call, not the return |
| 15, 17, 52, 55 | — | — | reclassified between the non-WRONG buckets |

**Two of these are substantive, not procedural.** On #42 rater 2 produced a refutation the first
rater missed entirely — the claim assumes `is_quantized` is a safe existence check, and it is not,
because it dereferences the same attribute one line earlier. And on #28 rater 2 applied the first
rater's own anchor rule more strictly than the first rater did.

**Which is the direction that matters for the conflict.** The concern was that the prompt's author
would grade generously. **The independent reading says the first rater was too generous, not too
harsh** — so the bias ran the way the conflict predicted, and correcting it makes the result worse.

## The consensus floor

**Findings both raters independently called CORRECT: 3 of 66 — 4.5%.** Those three are
`all([])` returning True on an empty worker list, a case-sensitive scan whose sibling test
lowercases, and a test forcing 32×32 tokens while its expectation string still says 64×64.

## What this settles and what it does not

**Settled: the STOP conclusion no longer rests on one reading.** Two independent adjudications, at
κ = 0.82 on the binary, both put the wrong-rate far above the pre-registered threshold and the
correct-rate far below the field's floor.

**Not settled: rater 2 is the same model family as rater 1.** Independent context, blind, disjoint
blocks, and it disagreed with rater 1 nine times — but correlated priors remain. **This replicates
the reading. It is not the different-family or human check the ranking result received, and no
published version of this number may imply otherwise.**
