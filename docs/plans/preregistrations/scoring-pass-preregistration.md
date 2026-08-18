# Design ten — reject what the diff cannot decide, with design nine as a paired control

**Written after reading `qodo-ai/pr-agent` rather than after searching for opinions about it, and
the reading changed the design twice.**

---

## What reading their code corrected

**I claimed we had not copied "a scoring pass". That was too coarse.** Their reflection pass and
our model-free gate do largely the same work:

| their mechanism | ours | note |
|---|---|---|
| reflection cannot locate `existing_code` → `score = 0` → dropped | **G-quote** | ours is a string search, theirs a model call. **Ours is deterministic and free** |
| `existing_code == improved_code` → cleared | **G-fix** | equivalent |
| zero-score list: docstrings, type hints, imports, exception types | **G-nit** | ours is a regex, theirs a model judgment |
| *"questions … any entity … that might be done in the outer codebase"* → `score = 0` | **G-outer** | **ours only fires on backticked identifiers absent from the diff — 7.4%** |

**And two details worth recording.** Their effective threshold is `max(1, configured)`, so the
config default of 0 still drops every zero-scored finding. And on any exception their handler sets
`score = 7` — a generous default that publishes on error.

**So the gap is not "a scoring pass". It is that their outer-codebase rule is a model judgment and
ours is a regex that mostly does not fire.**

## The measured target

**87% of design nine's fifteen wrong findings rest on facts the diff cannot supply** — 13 of 15:

- *"version `==0.15.*` for ruff is invalid because no version matching this prefix has been
  released"* — requires a package registry
- *"Python 3.14 is a non-existent version"* — requires knowing today's date
- *"this assertion will fail"* on a **merged pull request with passing CI** — requires a test run
- *"the commit hash does not exist in `astral-sh/setup-uv`"* — requires the remote repository

**Our G-outer cannot catch these.** They quote no absent identifier; they assert facts about the
world. **A parser cannot decide "does this version exist on PyPI", so by this project's own rule
this is where a model is allowed to run.**

---

## The pattern in design nine's adjudicated findings — and why the number beside it is worthless

**Listing all 15 CORRECT against all 15 WRONG makes the split obvious:**

| | CORRECT | WRONG |
|---|---|---|
| file kind | 13 source, 2 CI | **0 source**, 7 test, 8 CI |
| what the claim says | **what the code IS** | **what will HAPPEN when it runs** |

Every correct finding names a property of the code's own logic — a leaked file handle on an error
path, a blocking call inside `async def`, an empty string treated as falsy by `or`, a race between
a main thread and its workers, a `relpath` that yields `..`. **Every wrong one predicts an outcome
in an environment the model cannot observe** — this test will fail, this version does not exist on
PyPI, this commit hash is not in that repository, Python 3.14 is not a real version.

**Two lexical markers separate them, and the second is much the stronger:**

| marker on the claim text | catches WRONG | costs CORRECT |
|---|---|---|
| asserts an external artifact exists or is valid | 7/15 (47%) | **0/15** |
| **predicts a runtime or test failure** | **13/15 (87%)** | 1/15 |
| either | 14/15 (93%) | 1/15 |

### THE 3.1% THIS PRODUCES IS NOT A RESULT

Applying both markers to design nine's own findings takes the wrong-rate from 34.9% to 3.1%.
**That number is meaningless and must never be quoted.** The regex was written by reading the
fifteen wrong findings it is then scored against. **A filter fitted to its own test set has no
error rate**, and this project has recorded what happens when a subgroup found that way is
reported as a finding.

**It becomes evidence only when pre-registered and run on repositories that did not shape it.**
That is what arm B below is.

**And the one CORRECT it costs is instructive:** *"an exception raised during this call will cause
a file handle leak"* — a genuine defect, phrased as a prediction. **The marker cannot tell a
prediction that follows from the code from one that reaches outside it.** That is its ceiling.

## The design

| arm | configuration |
|---|---|
| **A — control** | design nine exactly. **This is also the replication of design nine on fresh repositories.** |
| **B — treatment** | A **plus the two lexical markers above, applied as a gate**. Free, deterministic, no model call |
| **C — comparison** | A **plus a model-judged decidability gate**, asking whether the claim can be decidable from the diff alone |

| **D — added before any design-ten result was seen** | A minus any finding that predicts a test, build or CI failure. **Every pull request in the corpus is merged**, so such a claim is false by a fact we already hold |
| **E — registered, not run here** | A minus any finding whose claim is settled by a REGISTRY LOOKUP: does this version exist on PyPI, is this commit hash in that repository |

### CORRECTED BEFORE RUNNING — arm D's premise was checked and it is false

**I wrote that "merged" entails "tests passed". It does not.** Six design-nine pull requests were
queried against the GitHub check-runs API:

| pull request | checks |
|---|---|
| bokeh#15342, #15346 | all success |
| bokeh#15348 | success, 2 skipped |
| **bokeh#15337** | **2 failures** |
| **bokeh#15353** | **1 failure** |
| **huggingface/datasets#8363** | **3 failures, 8 cancelled** |

**Half the sample merged with failing checks.** Maintainers merge over flaky jobs, unrelated
failures and admin overrides. **A rule resting on merge status alone is an approximation, not an
entailment, and calling it entailed was wrong.**

**The rule is therefore narrowed twice:**

**One — it must read the actual check runs, not the merge flag**, and it must ask whether the
failing job plausibly covers the file the finding is about. Of four flagged design-nine verdicts,
three had failures in unrelated jobs (`Analyze (javascript)` on a Python test, `Test Log Schema` on
a postgres action, a Python job against a TypeScript test) and **one — item 32 — had a Python
unit-test job failing against a Python test file, which makes that verdict genuinely unsafe.**

**Two — it blocks PREDICTIONS OF OUTCOME, never CRITICISMS OF QUALITY.** These are blocked:

> *"this assertion will fail"* · *"will cause a syntax error when run"* · *"the mock is called
> twice so this will fail"*

**These are not, and must not be:**

> *"this test passes but does not check what it claims"* · *"this assertion is too weak"* ·
> *"this test does not cover the error path"*

**Merge status and CI status say nothing about either of the second group.** A rule that blocks
anything mentioning tests would kill real findings and would itself be fitted — to a different
pattern than arm B, but fitted all the same.

**What survives of D's advantage over B:** its rule is still derived from a property of the corpus
rather than from reading the findings, but the property must now be *measured per pull request*
rather than assumed. That is a lookup, which puts D in the same architectural family as arm E.

### The one unsafe verdict, traced to the implementation — and it holds

**Item 32 was the only verdict where a failing job plausibly covered the file.** Reading the code
rather than the CI status settles it. `tests/tools/backport/test_interactive.py`:

```python
checkpoint = MagicMock()
cases = [("s", "saved"), ("q", "discarded")]
for action, expected in cases:            # runs twice
    ... run_plan_session(MagicMock(), state, checkpoint)
checkpoint.assert_called_once()
```

The model saw a two-iteration loop and one `assert_called_once` and called it broken.
`tools/backport/interactive.py`, **in the same diff**:

```python
case "s":
    if checkpoint is not None:
        checkpoint(state)     # called
    return "saved"
case "q":
    return "discarded"        # not called
```

**Called exactly once across two iterations. The test passes and the claim is false.**

**Three routes to that verdict, and only one of them is sound:**

| route | verdict | status |
|---|---|---|
| merge status | WRONG | **unreliable — half the sample merged with failing checks** |
| failing-job name | inconclusive | the job was Python 3.14 on Windows, unrelated to this test |
| **reading the implementation** | **WRONG** | **proven** |

**This weakens arm D further than the CI check did.** The claim was decidable from the diff the
model was given — both the test and the implementation were in it. **No lookup was needed; the
model simply did not trace it.** A rule that suppresses such claims by merge status suppresses the
right answer for the wrong reason.

**Effect on design nine's headline:** at most two of fifteen WRONG verdicts are unsafe, moving
34.9% to 32.6% or 30.2%. **Both still clear the bar, so the result stands** — but the adjudication
carried an assumption it should not have, and that is recorded rather than quietly corrected.

**Arm E is the right architecture for the other half and is not implemented here.** "Does version
1.45.34 exist on PyPI" is answerable by an HTTP GET and by nothing else — not by a prompt rule, not
by more repository history, not by a model. **If a lookup can answer it, a model must not**, which
is the same rule that made the gate a string search rather than a model call. It is registered so
that building it later is a pre-registered step rather than a reaction to a result.

**What is NOT being added: a prompt rule.** "Only claim what is visible in the diff" asks the model
to police a boundary it cannot perceive — when it says a version does not exist it believes that is
a fact about code. The record is against it: design nine's prompt already banned nits and style
still came in at 0–0 against Qodo; design eight's quote requirement was obeyed by **abstaining**
rather than by anchoring better; our rejection filter moved nothing at p = 0.53; and Greptile
published the same null independently. **A prompt rule is the weakest instrument available and is
predicted to underperform the free regex.**

### On whether a hand-written marker can generalise at all

**The objection is that thirty findings from six repositories cannot produce a filter that
transfers, and that the mechanism should be dynamic rather than a fixed pattern.** That objection
is already the experiment: **arm C is the dynamic version.** It asks the semantic question — can
this claim be decidable from the diff — instead of matching the phrasing that happened to express it.

**So design ten is a direct test of the objection, not a bet against it:**

- **B holds on fresh data** → the phrasing is a serviceable proxy for the semantics
- **B fails and C holds** → the objection is correct and the filter must be dynamic
- **both fail** → neither instrument reaches the failure mode

**I no longer expect B to win.** The ordering below was written when I expected the cheap
instrument to suffice; the argument that phrasing is model-specific and corpus-specific is a good
one, and it moves my prior toward C. **The ordering stays because the test is worth running either
way, but the expectation is recorded as changed.**

**B before C on purpose.** A regex that catches 93% at a cost of 7% — *on the data that produced
it* — must be tested on fresh data before paying for a model call that does the same job. This
project's rule is that if a parser can answer it, a model must not. **C exists to measure whether
the model earns its cost over B, and if it does not, C is deleted.**

**The gate's question, and it is not a severity rating:**

> Can this claim be decided using only the diff shown? Answer NO if it depends on a package
> registry, a remote repository, today's date, a test or build result, or a file not in the diff.

**Severity is deliberately not asked.** Two independent measurements say that is noise: our own
rejection filter moved nothing, and Greptile published that LLM severity rating is "nearly random".

**Also carried from their design, and predicted inert:** numbered diff lines, and surplus
generation across chunks. They are included because they are part of the mechanism being copied,
not because I expect them to matter — see prediction 4.

---

## Corpus

**Forty-eight repositories are burned.** Six more, verified unused: `pallets/quart`,
`aio-libs/aiohttp`, `tiangolo/sqlmodel`, `pytest-dev/pytest-asyncio`, `python-attrs/attrs`,
`psycopg/psycopg`. Ten pull requests each, sixty total.

**Both arms review the same pull requests. Paired, not two samples.**

---

## Why paired, and what it fixes

**Design nine's binding limitation is that I rated it and wanted it to pass.** A second corpus
rated by me again adds data to one bias.

**Pairing does not remove my bias; it cancels it in the comparison.** Both arms are rated by one
person, in one shuffled list, **without knowing which arm produced any finding** — blinding that
design nine could not have, because every finding there came from one design.

**The A-versus-B delta survives my bias. The absolute levels do not, and are reported as levels.**

---

## The bars

| # | bar | rationale |
|---|---|---|
| **J1** | **B's wrong-rate < A's, Fisher or McNemar p < 0.05** | the primary question. A point estimate is not enough |
| **J2** | **arm A's wrong-rate < 50%** on unique findings, Wilson upper bound clearing 50% | the replication of design nine |
| **J3** | sabotage catch ≥ 75%, **printed before J1 and J2** | below it the run is VOID |
| **J4** | B's yield ≥ 0.30 published per pull request | a gate that publishes nothing passes every quality bar by silence — design seven's failure |
| **J5** | ≥ 25 unique findings per arm | below this that arm is UNDERPOWERED |

**Unique-finding denominators throughout**, since design nine's headline moved 30.6% → 34.9% on
deduplication.

---

## Predictions

1. **Arm A replicates between 25% and 50% wrong** — anything inside design nine's 22.4–49.8%
   interval counts.
2. **B beats A in direction but NOT significantly.** The gate targets 87% of the failures, so the
   direction should be clear; at n≈30 per arm **I expect J1 to FAIL on the significance
   requirement.** Recorded now so "the direction was right" cannot later be offered as if it were
   the bar.
3. **B's yield falls below A's** and J4 is B's bar most at risk.
4. **Numbered lines and surplus generation change nothing measurable.** We already never ask for a
   line number, so numbering has nothing to attach to.
5. **Arm D removes 30–60% of A's wrong findings at a cost of under 10% of its correct ones**, and
   is the highest ratio of the four arms because its rule is entailed rather than fitted.
6. **Arm D and arm B overlap heavily but not completely** — B's "predicts a runtime failure" marker
   catches most of what D catches, plus some non-test cases. **If D is a strict subset of B, D adds
   nothing and should be dropped.**
7. **The gate will over-reject.** Some true findings do depend on outside knowledge and will be
   caught. **If B's CORRECT count falls as much as its WRONG count, the gate is a volume control
   rather than a precision filter, and that is a fail however the wrong-rate reads.**

---

## What a pass would and would not mean

**Would:** one paired comparison, one fresh corpus, one rater, blinded by arm.

**Would not:** reopen `infer/`. That needs design nine's configuration to hold with a rater who is
not the author. **This run supplies a comparison robust to the rater, which is a different thing
and must not be described as the same one.**

**A near-miss is a fail.** B at 30% against A at 34% with p = 0.4 fails J1 and will be reported as
failing.
