# Pre-registration — adjudicating the first 66 findings

**Written before a single finding was read.** The whole point of fixing a threshold now is that
it cannot be set backwards from whichever answer arrives, which is the failure this project
already corrected once on the model-certification rule.

Findings under adjudication: the **66** emitted by `gemini-2.5-pro` across 68 requests on 23
merged pull requests, recorded in `research/phase0/results/vertex_cost_c3.json`.

---

## The three buckets

Every finding lands in exactly one. The third is not a hedge — it is the bucket that decides
whether the product is usable, because a finding a reviewer cannot act on from the diff is a
finding that costs them time whether or not it is true.

| bucket | test |
|---|---|
| **CORRECT** | The claim is true of the code shown, and `line_a` / `line_b` point at the lines that make it true |
| **WRONG** | The claim is false of the code shown, or the line anchors do not support it |
| **UNFALSIFIABLE** | The claim may be true but cannot be decided from the function and diff alone — it needs the caller, the runtime, or the rest of the repository |

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
