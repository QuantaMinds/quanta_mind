# Design twelve — multi-review aggregation, the one remaining technique with external evidence

**Every mechanism tried so far was invented here or copied from Qodo. This one has a published,
measured effect size and has not been tried.**

**SWR-Bench**: running the same tool several times and aggregating the reports with an additional
model call **increased F1 by up to 43.67%**, the stated aim being recall through issues flagged
consistently across independent runs.

**That is larger than anything eleven designs produced here, and it is orthogonal to every gate we
have built.** Our gates ask *can this claim be decided from the diff*. Aggregation asks *did the
model say this again when asked again*. Different question, different failure mode.

---

## Why it is worth running when the review half is closed

**It is not a reason to reopen `infer/`.** The bar is unchanged: under 50% of published findings
wrong, twice, with a rater who did not design the experiment.

**It is worth running because the cost is asymmetric.** If self-consistency separates true from
false findings, it is the first mechanism with an independent published effect behind it. If it
does not, that is a null against a published claim, measured on our corpus, and worth recording.

---

## The design

**Three independent reviews of each pull request** at temperature 0.7 — the runs must differ or
agreement measures nothing — then group findings by whether they name the same defect.

| arm | configuration |
|---|---|
| **A** | one review, design nine. The control, and a replication |
| **G2** | findings appearing in **≥ 2 of 3** runs |
| **G3** | findings appearing in **all 3** runs |

**Grouping is the hard part and it must not be a model call**, or the aggregator becomes another
unmeasured judge. Two findings are the same when their `quote` locates to the **same file and
line** by the existing string search. **That is deterministic and it under-counts agreement** —
two runs describing one defect from different lines will not group — which is stated as a floor,
not hidden.

---

## Bars

| # | bar |
|---|---|
| **L1** | **G2's wrong-rate < A's, Fisher p < 0.05** |
| **L2** | arm A < 50% with the Wilson upper bound clearing — the replication |
| **L3** | sabotage catch ≥ 75%, printed first, else VOID |
| **L4** | G2 yield ≥ 0.30 per pull request |
| **L5** | ≥ 25 unique findings per arm, else UNDERPOWERED |
| **L6** | **three runs must actually differ** — if the union of findings across runs is under 1.3× the size of a single run, temperature is not producing independent samples and the run is VOID, not a null |

**L6 exists because a null here has two causes** — agreement carries no signal, or the runs were
not independent — **and they are not the same finding.**

---

## Predictions

1. **Arm A replicates 25–45%.** Two runs at 34.9% and 31.0%.
2. **G2 beats A in direction. I do not expect p < 0.05 at n ≈ 30.**
3. **G3 is too strict to score** — it will fail L4 and L5, as arm C did at 0.25 yield.
4. **The 43.67% F1 gain will NOT reproduce.** Theirs is an F1 gain driven by RECALL — aggregating
   *more* findings across runs — and ours is a precision filter keeping *fewer*. **Opposite
   directions from the same mechanism, and citing their number as support for ours would be the
   drift this project's publishing rules exist to stop.**
5. **The model repeats its confident errors.** The version-does-not-exist claims were stated with
   certainty; **certainty is exactly what survives resampling.** If aggregation cannot remove the
   EXTERNAL class, it cannot reach 62% of our failures.

**Prediction 5 is the mechanism most likely to sink this**, and it is the reason a published effect
size elsewhere is not evidence for the effect here.

---

## Convergence with Qodo, recorded so it is never claimed as differentiation

**Every filtering mechanism this project has built already exists in `qodo-ai/pr-agent`:**

| ours | theirs |
|---|---|
| design 8's `quote` + `fix` | `existing_code` + `improved_code` |
| design 10's arm C model gate | the self-reflection pass, score 0 eliminated |
| design 11's `evidence` field | issues carry evidence and reasoning |
| the dedup problem we have | a judge agent that merges and removes duplicates at generation |
| "history as context", considered | pull-request history as a first-class signal |

**We are retracing the architecture of the tool that leads the benchmark.** Convergent design is
weak evidence the direction is right. **It is not novelty, and no document may present these
mechanisms as differentiation.**

**One difference matters and it is not in our favour:** Qodo's `existing_code` permits an ellipsis
for brevity, so their anchor is not a strict verbatim match. **Ours is stricter than the design we
copied**, which is a candidate explanation for design eleven's rejection rate and is now its own
bucket in the near-miss classifier.
