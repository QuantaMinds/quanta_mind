# Design fourteen — the model lever, with the bar fixed first

**Written before the run. Nothing below is edited after a number exists.**

This is the re-run the reserve conditions describe. `docs/plans/implementation.md` under "What would
reopen the reserved layers" requires, for `infer/` to open: G2 held **twice**, at least once by a
rater who did not design the experiment, **and** the correct-rate cleared alongside it. It has never
held once. This document fixes what would count.

---

## Why a re-run is admissible at all

The reserve conditions list what does **not** reopen the layers: a better prompt, aggregation, and
*"a stronger model alone, **without** a pre-registration fixing the bar before the run."* The
qualifier is the opening, and this document is the thing it requires. The lever being pulled is the
subject model. Everything else is held as close to design thirteen as the diagnosis permits.

---

## What design thirteen actually measured, recomputed from its own artefacts

`research/phase0/quote/adj13/verdicts.json` against `KEY_DO_NOT_OPEN.json`, blind, with ten planted
sabotage findings mixed into the pool.

**The rater caught 10 of 10 sabotage items.** The adjudication is load-bearing and it earns that.

| pool | n | W/n | Wilson 95% | C/n |
|---|---|---|---|---|
| all real findings | 86 | **52.3%** | 41.9% – 62.6% | **8.1%** |
| source code only, config excluded | 50 | **42.0%** | 29.4% – 55.8% | **6.0%** |

**Every WRONG finding falls into exactly two causes, and the third has disappeared:**

| cause | count | what it is |
|---|---|---|
| `EXTERNAL` | 28 | deciding it needs a fact the diff cannot supply |
| `TRACE` | 17 | the model traced the code and got it wrong |
| `ABSENT` | **0 of 86 real** | all ten `ABSENT` verdicts were the planted sabotage |

**The anchoring failure class is gone.** In the earlier adjudication it was 36.4% of all findings —
"the line numbers do not point at the code the claim is about" — and five designs that repaired the
line number all failed. Design thirteen removed the field: the model quotes code and
`research/phase0/quote/gate.py` derives the line from where the quote sits, so the prose and the
anchor cannot disagree because one is a function of the other. **Zero real findings mis-anchored.**
That part of the review half works and is not what is being retested.

**`EXTERNAL` is concentrated, and it contradicts a decision still live in the code.**

| bucket | n | W/n | C/n | EXTERNAL failures |
|---|---|---|---|---|
| `.github/` | 32 | **65.6%** | 12.5% | **21 of 28** |
| other config | 4 | 75.0% | 0.0% | 3 of 28 |
| source code | 50 | 42.0% | 6.0% | 5 of 28 |

`research/phase0/quote/paths.py` keeps `.github/` **on purpose**, and says so: *"CI configuration is
hand-written and produced three of design eight's eight CORRECT findings."* That was decided on
design eight. Design thirteen's own data says `.github/` is now the single largest source of
wrongness in the experiment, and the failures are a recognisable kind — the model asserting that a
pinned action SHA is not tagged what it is tagged, which no diff can settle. `AGENTS.md` already
records the same thing from another angle: *"CI-config findings are 66.7% wrong, 23 of 24
undecidable from a diff."*

---

## Design fourteen: exactly three changes

1. **The subject model becomes a current frontier model.** Design thirteen ran `gemini-2.5-pro`.
   This is the lever, and it is the only one the reserve conditions leave open.
2. **`.github/` and remaining config paths are excluded before the call**, reversing the
   design-eight decision on design-thirteen evidence. The filter runs before the request, not after,
   for the reason `paths.py` already gives: removing the findings afterwards leaves the model
   spending its attention on files it cannot reason about.
3. **A new corpus of six repositories**, each verified at zero prior mentions anywhere under
   `research/` by `scripts/guard/records/check_burned_corpora.py --check` before selection.

**Held fixed:** the quote-anchor prompt, `gate.py` unchanged, the rubric unchanged, the sabotage
items, the blind chunking, and the thresholds below.

**Not changed, deliberately:** no aggregation (retired on measurement — 4 of 5 correct findings came
from one arm, and wrong findings recur more often than correct ones), no rejection filter, no anchor
repair, no conventions file. Each was tried and moved nothing.

---

## The bars, fixed now

Let **C**, **W**, **U**, **T** be the counts and *n* = C + W + U + T over **real findings only**,
sabotage excluded from every rate.

| reading | rule |
|---|---|
| **STOP** — the review half still does not work | **W / n ≥ 0.50** |
| **REBUILD** the inference step | 0.30 ≤ W / n < 0.50 |
| **PROCEED**, residual as the product | W / n < 0.30 **and** U / n < 0.50 |
| **PROCEED but the schema is wrong** | W / n < 0.30 **and** U / n ≥ 0.50 |

**And the second bar, which is the binding one: C / n ≥ 0.49**, the bottom of the independent
benchmark's 49–76% precision band for the field. Below it we are worse than the competition while
claiming to be quieter than it, and quietness is only a virtue if what breaks the silence is right.

**BOTH must clear. Neither substitutes for the other.** A design clearing W/n by finding almost
nothing is worthless, and the reserve conditions say so in as many words.

**Wilson 95% intervals are printed beside both.** At n ≈ 90 the interval is roughly ±10 points.
**A point estimate on the correct side of a threshold with an interval spanning it is INCONCLUSIVE
and will be called one — it is not a pass.**

---

## The prior, stated before the run so the result cannot be re-read afterwards

On design thirteen's source-code-only pool: **W/n = 42.0%, C/n = 6.0%, 3 correct findings in 50.**

- **W/n clearing 0.50 is likely** and would not be surprising; it is already below it once config is
  excluded, which is why excluding config is not the interesting part of this design.
- **C/n reaching 0.49 requires an eightfold increase in the correct-finding rate. I do not expect it
  to clear.** This is written down now because a null result here must not be reported as "the model
  improved but the bar was too high", and a pass must not be reported as expected all along.

**The most likely outcome of this run is REBUILD on W/n and a failure on C/n**, which leaves the
reserve closed and costs one experiment rather than a shipped reviewer that is wrong half the time.

---

## Adjudication protocol

- **Blind.** Findings are chunked with the key sealed in `KEY_DO_NOT_OPEN.json`, unopened until
  every verdict is recorded.
- **Sabotage retained**, at the same ratio. A pool where the planted items are not caught invalidates
  that rater's block rather than the design.
- **Two clearances, and one grader must not have designed the experiment.** This is the condition
  four prior designs still owe. A second pass by the same family in a fresh context is **not** the
  independent grade — it is what design thirteen already has, and `undecidable-paths-preregistration.md`
  records that it does not count toward replication.
- Rater agreement is reported as **κ and raw agreement on the binary WRONG / not-WRONG cut**, which
  is the only distinction the thresholds depend on.

## Recorded alongside, not graded

- **Findings per pull request**, against a product that promises one comment.
- **Every silence**: whether it was correct, or a defect present and missed. This is the coverage
  line's honesty tested directly, and it is the one place where being wrong is worse than being
  quiet. Design thirteen did not audit this and recorded the omission as a gap.
- **`finishReason` on every call.** Six of design thirteen's eight silences pinned the thinking cap
  first; a truncation reported without its finish reason reads as "the model found nothing", which
  is the exact failure shape this project keeps hitting.

---

# Amendment 1 — the lever this design is named after is not reachable, and the run splits

**Written after the document above was committed at `315605b`, before any review call was made.
Nothing in the bars, the corpus or the prior has been touched.**

## What was probed, and what answered

`quantamind-oss`, with a live `gcloud` token, `POST …:generateContent` and `…:rawPredict`:

| model | publisher | us-central1 | us-east5 | global |
|---|---|---|---|---|
| `gemini-3-pro-preview`, `gemini-3-pro`, `gemini-3.0-pro` | google | 404 | 404 | 404 |
| `gemini-2.5-pro-preview-06-05`, `gemini-2.5-pro-002`, `gemini-exp-1206` | google | 404 | — | — |
| `gemini-2.5-pro` | google | **200** | **200** | 404 |
| `claude-sonnet-4-5`, `claude-opus-4-1` | anthropic | 404 | 404 | — |

`ANTHROPIC_API_KEY` is not set in the environment either.

**`gemini-2.5-pro` is the only capable model this project can reach, and it is the model design
thirteen already ran.** The subject model cannot change today, so the change this design is named
after cannot be executed.

## The run splits, and only one arm is executable

**Arm 1 — the config exclusion, out-of-sample. `gemini-2.5-pro`, new corpus, `.github/` and config
excluded before the call.** This is **not** the model lever and must never be reported as it.

What it buys is real and is not a consolation: **the 42.0% source-code-only figure was computed
POST HOC**, by filtering design thirteen's already-adjudicated pool after the verdicts existed.
This project's own rule is that choosing a subset after seeing a result is the same defect as
moving a threshold after seeing a number, so that figure is a hypothesis, not a measurement.
Applying the filter BEFORE the run, on a corpus the method has never seen, is what turns it into
one. If W/n does not clear 0.50 here, the model lever is moot and arm 2 need not be paid for.

**Arm 2 — the model lever. BLOCKED.** It needs a frontier model enabled in Vertex Model Garden for
this project, or an Anthropic API key. Until then it is not run, and no result may be described as
having tested it.

## What arm 1 cannot do, stated before it runs

**Arm 1 alone cannot reopen `infer/`, and a good result must not be read as though it could.**
Excluding config removes wrong findings; it creates no correct ones. Design thirteen's
source-code-only pool held **3 correct findings in 50**, and C/n has to reach 0.49. The reserve
needs both bars, and this arm can only move one of them.

**The expected reading of arm 1 is REBUILD on W/n and a failure on C/n**, which is the same
expectation recorded for the full design above, reached one lever short.

---

# Amendment 2 — the sample was silently short, and this design was underpowered before it ran

**Written before any review call. No verdict exists on this corpus. `PER_REPO_D14` changes from 15
to 50 and nothing else does.**

## `corpus.pulls()` read ONE page and stopped

The function requested `state=closed&per_page=40`, took the merged rows out of that single page,
and returned however many it found. **It never paginated and it never said it was short.**

**Design thirteen asked for 6 × 15 = 90 pull requests and ran on 80.** Re-running its own request
against the fixed function returns 90. Nothing in `quote13_run.json`, and nothing printed at the
time, recorded the missing eleven percent.

This is the silent-cap shape `AGENTS.md` names: *"if a workflow bounds coverage, log what was
dropped — silent truncation reads as 'covered everything' when it didn't."* The fix paginates to
`MAX_PAGES` and **prints a line naming the repository and the shortfall** whenever one remains, so
a corpus that cannot supply the sample says so instead of quietly supplying a smaller one.

**This does not invalidate design thirteen.** Its findings were adjudicated as they stood, and 80
pull requests is a real sample; it is simply not the sample the document says it is. Recorded here
because it was found while sizing this run, and a defect found in the instrument belongs beside the
next measurement it would have affected.

## The power calculation, which had not been done

Design thirteen reached n = 96 adjudicated findings from **three arms** over 80 pull requests.
**Design fourteen runs one arm**, correctly — hunk expansion and the conventions file each moved
nothing, and re-measuring them would triple the cost to re-answer two settled questions. But it
means the same n costs three times the pull requests, and that had not been carried through.

Measured on this corpus, before any model call:

| quantity | measured |
|---|---|
| reviewable after the strict filter | **73%** of merged pull requests |
| published findings per pull request, design thirteen arm A | **0.41** |
| at the original `PER_REPO_D14 = 15` → 90 PRs | ~66 reviewable → **~27 findings** |

**At n ≈ 27 the Wilson interval is about ±19 points.** Against a threshold of 0.50 and a point
estimate expected near 0.42, that interval spans the threshold under every outcome — and this
document already says an interval spanning a threshold is INCONCLUSIVE and not a pass. **The run
as sized could not have returned an answer, whatever the model did.**

`PER_REPO_D14 = 50` gives ~300 pull requests, ~219 reviewable, **~90 findings**, which is the n the
power statement above assumes.

**This is a change to a pre-registered parameter and it is made for one reason: the original value
made the experiment unable to answer its own question.** It is recorded before any review call, no
verdict exists on this corpus, and the repository literal is untouched — `sqlalchemy/sqlalchemy`
stays in the corpus despite supplying the fewest usable pull requests of the six, because removing
a repository after measuring its yield is selection, and its low yield is a fact to report rather
than a reason to drop it.

---

# Result — arm 1 measured nothing, because the judge was the weaker instrument

**The run happened. The headline it produced is withdrawn by the check that follows it, and the
check was run because the headline was too good.**

## What arm 1 scored

300 pull requests, 194 reviewable, 148 raw findings, **104 published after the gate**, 102 unique.
Graded blind against the unchanged rubric with 12 sabotaged controls.

| | W/n | C/n | TRIVIAL |
|---|---|---|---|
| arm 1, first grading | 24.5% | 62.7% | **0.0%** |
| arm 1, second grading (temperature 0 replication) | 28.4% | 59.8% | **0.0%** |
| design thirteen, as reported | 52.3% | 8.1% | 18.8% |

**C/n went from 8.1% to 62.7% on a change that only REMOVES findings.** Excluding CI config cannot
manufacture correct findings, and the pre-registration above says in as many words that C/n reaching
0.49 needed an eightfold increase and was not expected. **A result that far past its own written
prior is an instrument change until proven otherwise**, and the judge was new.

**TRIVIAL = 0 of 102 was the tell.** Design thirteen's rater used that bucket on 18.8% of findings.
A grader that never reaches for one bucket is not grading the same way.

## The check: hold the judge fixed, vary the design

`judge_compare.py` re-graded **design thirteen's own pool** with arm 1's judge.

| design thirteen's pool | W/n | C/n |
|---|---|---|
| as its own rater graded it | **52.3%** | **8.1%** |
| as arm 1's judge grades it | **29.1%** | **57.0%** |

**Raw agreement between the two raters on the same 86 findings: 34.9%.** Read off one instrument,
design thirteen and design fourteen are indistinguishable — W/n 29.1% against 24.5–28.4%, C/n 57.0%
against 59.8–62.7%. **The config exclusion moved nothing. The entire apparent improvement was the
rater.**

## Which rater is right, and it is not the new one

27 findings design thirteen called WRONG were called CORRECT by arm 1's judge, tagged `EXTERNAL`
(18) and `TRACE` (9). The disagreements are not close calls:

| design thirteen's rater | arm 1's judge |
|---|---|
| `actions/checkout` v7.0.1 exists and `3d3c42e5` carries that exact tag | "no such release exists" |
| the comment reads Aug 16 2026 and today is Aug 18 2026, so the date is past | "the comment contains the future year 2026, which is a typo" |
| the `open` has no `O_TRUNC`, so the truncation the claim rests on cannot occur | "a race condition where an existing file could be..." |

**The judge is the same family as the subject, and it ratifies the subject's own blind spots.**
Design thirteen's rater went and checked whether a pinned SHA carries the tag the reviewer disputed;
arm 1's judge could not, and accepted the reviewer's claim. It repeated the reviewer's belief that
2026 is in the future — while running in 2026. **A judge that shares the subject's training cutoff
and its inability to reach outside the diff will grade the subject's hallucinations CORRECT**, and
that is precisely the failure class design thirteen measured as `EXTERNAL`.

## The sabotage control has a blind spot, and this is the first time it has been seen

**12 of 12 planted findings were caught. 10 of 10 on design thirteen's pool. The judge was wrong on
a third of the real ones anyway.**

Sabotaged controls pair a real quote with a claim about entirely different code — grossly,
structurally wrong. Catching them proves a pool is not rubber-stamping. **It does not prove the pool
can tell a confident, well-formed, false claim about an external fact from a true one**, which is
the failure that actually dominates this corpus. The control measures a proxy for rater quality and
reads 100% while the quantity it stands for is failing — the defect `AGENTS.md` rule 14 names, found
in the project's own adjudication protocol.

**A same-family judge is disqualified as an instrument for this task.** A future adjudication needs
a rater from a different family than the subject, or one that can check a claim against the
repository and the network, and the sabotage pool needs items that are subtly rather than grossly
wrong.

## Standing conclusion

**`infer/` and `verify/` stay closed. Design thirteen's numbers — W/n 52.3%, C/n 8.1% — remain the
operative measurement**, because that rater demonstrably checked facts this one demonstrably did
not. Arm 1 cleared no bar: it produced no comparable number.

**Arm 2, the model lever, is untouched by all of this and remains blocked** on a frontier model
being reachable. When it runs, it must be graded by an instrument that has been calibrated against
design thirteen's pool first — which is now a thing this repository can do, and could not before.
