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
published**, exactly as the ranking result required one and got it at 92% agreement, κ = 0.66.

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
| **Cohen's κ** | agreement corrected for chance, the same instrument that replicated the ranking result at **κ = 0.66** |
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
independent-family check the project used on the ranking result.

**Correction, found while auditing this file:** the ranking result's replication is repeatedly
cited in this session as κ = 0.92. **It is not. Agreement was 92%; Cohen's κ was 0.66**
(`QUANTAMIND.md`, "Two raters — one with every incentive to find the effect"). The two numbers
were conflated and the error propagated. It runs against the author in both directions: **today's
κ = 0.711 is above this project's own precedent, not below it**, and the historical replication is
weaker than it has been described as. **A human rater, or one from
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


---

# WEB CROSS-CHECK — and it breaks one of my own arguments

**Checked against live sources on 2026-08-14, after the conclusions above were committed.**

## The "below the field's floor" comparison does not survive, on two counts

**One: 49% is not the field's floor.** It is CodeRabbit's precision. The board runs lower —
**Augment at 47.0% precision** on the offline benchmark, and raw models lower still (Haiku 4.5
32.6%, Sonnet 4.6 35.3%). Graphite reaches 75.0% precision at 8.8% recall, which is the shape of
a tool that almost never speaks. **So "our best case (45.5%) is below their worst" is false as
written.** 45.5% sits below the named commercial reviewers and near Augment's offline figure.

**Two, and this is the more serious error: the metrics were never comparable.** Martian defines
precision as *"what share of the reviewer's suggestions matched changes the developer made after
review"*. That is **behavioural** — it measures whether a developer acted. This adjudication
measured whether a claim is **true and correctly anchored**. A true finding a developer ignores
counts *against* Martian precision; a false finding a developer happens to act on counts *for* it.
**Putting 9.1% beside 49–76% compared two different quantities, and I did it in a commit message,
in the ledger, and in the constitution.**

## What survives, and it is the part that was always doing the work

**The decision does not depend on the comparison.** 66.7% and 74.2% of published findings wrong,
under two blind raters at κ = 0.82 on the binary, against a threshold of **50% fixed before a
finding was read**. That is a self-contained result measured against a self-set bar, and it is
unaffected by anything on anyone's leaderboard.

**The 45.5% ceiling also survives, with its comparator removed.** It is still the answer to
"pointer-snapping will fix this": the most generous imaginable repair yields ten times the
measured correct rate and remains far short of a product. It just is not a statement about
competitors.

**Corrected in `AGENTS.md`, which now says explicitly not to reach for the competitors' band to
dramatise our own number.** The temptation to borrow a rival's figure for rhetorical force is
exactly the drift that produced the withdrawn catch rate.

## What did verify

| claim | status |
|---|---|
| Greptile 76.2% precision, leaderboard 30 July 2026 | **confirmed** |
| Gemini 2.5 Pro on Vertex: $1.25 / $10.00 per 1M under 200K context | **confirmed** |
| Thinking tokens billed at the **output** rate | **confirmed** — the basis of the 91.3% finding |

**And one thing the check found that makes our own cost figure too low.** Vertex **non-global
endpoints carry a 10% premium from 1 July 2026**, and the C3 run used `us-central1`. If that
applies to this usage, **$0.1193 per pull request understates by roughly 10%** — call it
**$0.131**. Flagged rather than silently corrected, because it should be read off an actual bill
rather than off a pricing page.

*Sources: Martian Code Review Bench leaderboard and coverage; Google Cloud Vertex AI generative-AI
pricing. Re-check the leaderboard Nov 2026 — it is rolling.*


---

# THE FIX EXPERIMENT — run 2026-08-14. **STOP CONFIRMED.**

Both mechanical fixes built and tested live against the same 23 pull requests, so the comparison is
on the same code. Blind adjudication, same rubric, fresh raters who were not told this was the
improved run.

**What was changed, and only this:** every line the model returns is snapped by `ast` to its
enclosing statement; and the prompt carries the enclosing class's attribute assignments, the file's
other signatures, its imports, and the call sites of the target function — plus rules written
against the first run's actual failures. **Deliberately excluded: whether the PR merged and whether
CI passed.** Several first-run findings would die on that information, and a real reviewer does not
have it, so using it would measure a reviewer that cannot exist.

| | first run | enriched |
|---|---|---|
| CORRECT | 9.1% | **13.0%** |
| **WRONG** | 66.7% | **61.1%** |
| UNFALSIFIABLE | 7.6% | 14.8% |
| TRIVIAL | 16.7% | 11.1% |

**WRONG = 33/54 = 61.1%, Wilson [47.8%, 73.0%]. The bar was under 50%. STOP CONFIRMED.**

**And nothing moved measurably.** Wrong-rate 66.7% → 61.1%, **p = 0.53**. Correct-rate 9.1% →
13.0%, **p = 0.50**. Two fixes, aimed at the two largest failure buckets, produced no detectable
improvement.

## The finding that matters more than the headline

**The parser fixed the symptom I could measure and left the defect.** My own mechanical check said
anchors on a real line of code went from 80.3% to **98.1%**, and findings with both anchors clean
from 63.6% to **96.3%**. That looked like the largest bucket closing.

**The blind raters disagree, and they are right.** Anchor failures are **57.6% of the remaining
wrong findings — a larger share of the wrong bucket than before the fix (54.5%).** In their words:

> *"line 978 is the assignment inside the `if`, not the `if` itself"*
> *"line 419 is the `def` line, not the 425-427 configuration the claim rests on"*
> *"line 574 is the `if` guard, not the clearing at 579"*

**Snapping moved anchors off blank lines and onto plausible-but-wrong statements.** The model was
never confused about brackets; it was pointing at the wrong *place*, and a blank-line anchor was
merely the visible tail of that. **Worse, the fix made the defect harder to see** — a blank-line
citation is obviously broken, a wrong-statement citation reads as fine.

**This is exactly the rule about checks: ask what a check outputs when the thing it checks is
broken. My anchor check outputs 98.1% either way.** It measured a property that correlates with
correctness rather than correctness itself, and I built it, believed it, and reported it before the
adjudication corrected me.

## What context did

**Nothing detectable, and possibly the opposite.** UNFALSIFIABLE rose from 7.6% to 14.8% — given
more surrounding code the model made *more* claims that could not be decided from what it was
shown. Small numbers and a different rater pool, so this is not a finding, but there is certainly
no sign of the reduction the hypothesis predicted.

**The model did get quieter**: 19 requests returned nothing against 8, and 54 findings against 66.
It suppressed volume without improving accuracy.

**And cost is not the obstacle**: $0.1211 → $0.1278 per pull request, +5.5%, on a 76% larger
prompt — because thinking is 91% of the bill and input barely registers. If context had worked,
its price was never the problem.

## The confound, stated

**The two runs were graded by different rater pools.** A 5.6-point difference in wrong-rate is well
inside that variation, which is another reason to read this as "nothing moved" rather than as a
small improvement.

## What this closes

The stop decision rested on one configuration. **It now rests on two, the second built specifically
to fix the first's two largest, most mechanically tractable failure modes.** Both failed to clear a
bar fixed in advance.

**The remaining honest position on the review half:** its failures are not a pointer problem and not
a context problem. They are the model asserting relationships between lines of code that are not
there — and the two cheapest, most obvious interventions have now been tried and measured.


---

# GOING DEEP ON THE ANCHOR PROBLEM — the pattern, and why the repair was backwards

One failure mode, taken alone and pushed until it gave up a pattern. The anchor bucket was chosen
because it is the largest: 57.6% of the enriched run's wrong findings.

## What the data says about where anchors land

| property of a finding | n | wrong | correct |
|---|---|---|---|
| **an anchor falls outside the function the model was shown** | 9 | **100.0%** | **0.0%** |
| the parser had to move an anchor | 29 | **72.4%** | 3.4% |
| the parser did not have to move it | 25 | 48.0% | **24.0%** |
| line_a equals line_b | 17 | 58.8% | 11.8% |
| model self-reported confidence "low" | **0** | — | — |

**Two findings, and the first inverts what I built.**

**Anchor imprecision is a symptom of a bad finding, not a cause of one.** A finding whose anchor
needed snapping is wrong 72.4% of the time; one that did not is wrong 48.0% and correct seven times
as often. **The model that cannot point at the line is the model that does not know what it is
talking about — so repairing the pointer preserves exactly the findings that should have been
thrown away.** The fix and the failure had the same input, and I chose the wrong response to it.

**And citing a line outside the shown function is a perfect negative signal here: 9 of 9 wrong,
none correct.** That is the model reasoning about code it was never given.

**Self-reported confidence carries zero information.** The model said `"high"` on all 54 findings,
including every one of the 33 that were wrong. A confidence field that never varies is not a
signal, and any design that gates on it is gating on a constant.

## What rejection does that repair did not

| filter | kept | wrong | Wilson |
|---|---|---|---|
| none | 54 | 61.1% | [47.8%, 73.0%] |
| drop anchors outside the function | 45 | 53.3% | [39.1%, 67.1%] |
| drop findings the parser had to snap | 25 | 48.0% | [30.0%, 66.5%] |
| **drop either** | **20** | **35.0%** | **[18.1%, 56.7%]** |

**And it keeps 0.87 findings per pull request — against a product that promises one comment.**
The filter and the product specification arrive at the same number from opposite directions.

## Why this is a hypothesis and not a result

**Eight filters were tried on n = 54, and every one of them is listed above rather than only the
winner.** With eight looks, one landing below 50% by chance is expected. Bonferroni puts the
required alpha at 0.05/8 = 0.00625. **No filter's interval excludes 50%** — the best one spans it,
[18.1%, 56.7%].

**It was also found by searching the same data it is scored on.** That is precisely the failure the
holdout caught on variant V2, and the honest label for this is *tuned on noise until shown
otherwise*.

**So it does not reverse the stop and must not be reported as if it did.** What it does is name a
specific, cheap, pre-registerable test: **does a reject-on-imprecise-anchor rule hold on a fresh
set of pull requests?** That test needs new repositories, a bar fixed in advance, and it is the
next thing to run — not the thing to build on.
