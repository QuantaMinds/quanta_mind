# The review half — the complete record

> **The corpus this rests on has a ±4-point noise floor**, measured 2026-08-26 by running the same
> arm twice: 91 against 84 of 173 defects from nothing but model nondeterminism. Compare any effect
> below to 4 points before believing it; large effects survive, small ones were never resolvable.
> → `corpus-noise-floor.md`


**Written so nothing here has to be rediscovered.** Every experiment run against the model half of
this product, what was predicted before each ran, what came back, and where the data sits. The
decision at the end is not a judgement call; it is what the pre-registered bars returned.

**The one-line answer: the review half stops.** Seven designs, seven failures against a bar fixed
in advance each time, and the field's own benchmark shows five published systems failing the same
way at the same magnitude on ten times the data.

---

## 1. What was measured, in order

Each row is a design. The bar was **under 50% of published findings wrong**, blind adjudication,
fixed before every run.

| # | design | corpus | n | wrong | correct | verdict |
|---|---|---|---|---|---|---|
| 1 | line anchors, minimal context | seen | 66 | **66.7% / 74.2%**¹ | 9.1% / 4.5% | **FAIL** |
| 2 | + parser-snapped anchors, + structured context | seen | 54 | **61.1%** | 13.0% | **FAIL** |
| 3 | reject-on-imprecise-anchor filter | unseen | 39 | **82.1%** | **0.0%** | **FAIL** |
| 4 | symbol anchors, parser derives the line | unseen | 36 | **77.8%** | 2.8% | **FAIL** |
| 5 | ±10-line anchor tolerance | unseen | 39 | **66.7%** | 2.6% | **FAIL** |
| 6 | execution gate — model writes a demonstrating snippet | easy | 18 | **27.8%** | 11.1% | passes, **did not transfer** |
| 6b | the same gate | unseen/hard | 21 | **52.4%** | 4.8% | **FAIL** |
| 7 | analyzer finds, model triages | unseen | 0 promoted | — | — | **no output at all** |

¹ two independent blind rater pools, κ = 0.82 on the binary.

**Pooled across every adjudicated finding: 207 findings, 5.80% correct, 65.2% wrong.**
→ `research/phase0/results/all_verdicts.json`

---

## 2. What was predicted, and what actually happened

**This is the part worth keeping.** Every hypothesis below was written down before its test.

| # | the prediction | the result | who was wrong |
|---|---|---|---|
| 1 | Anchors are the biggest bucket; snapping them to statements will move the number | 36.4% of anchors moved, **wrong-rate unmoved, p = 0.53** | me |
| 2 | The 77.8% "non-existent symbol" rate proves the model can't refer to code | **My `IndentationError`.** 79.6% of units are methods; `ast.parse` fails on indented source. Real rate: **0 of 36** | me, nearly published |
| 3 | Imprecise anchors are a *symptom*; rejecting them will separate good from bad | On unseen data, survivors 76.5% wrong vs rejected 86.4% — **+9.9 points, needed +15** | me |
| 4 | Removing the model's freedom to invent a line will fix it | Symbols resolve **36 of 36**, wrong-rate **77.8%**, p = 0.644 | me |
| 5 | Widening the anchor to ±10 lines will rescue the anchor failures | Anchor failures fell 43.8% → 7.7%; **wrong-rate 66.7%**. It converts WRONG into UNFALSIFIABLE, never into CORRECT | me |
| 6 | home-assistant's tie means its fix-history is flat | **False.** Its rank-1→2 gap is 15.19, larger than repos the ranker wins on. The *control* got better — alphabetical order tracks its `components/<x>/` layout | me |
| 7 | Alphabetical is a weak control, so our lift is inflated | **Backwards.** Alphabetical is +0.40 points *better* than chance pooled. The published figure **understates** | me |
| 8 | Test-file units drive the wrong-rate | **Refuted.** Source 75.9% vs test 69.0%, p = 0.29 | user's hypothesis |
| 9 | The correct findings are "comparisons", the wrong ones "simulations" | **Refuted.** Comparison-type claims are *worse*: 2.9% vs 10.0% correct | me |
| 10 | A >40-line hard gate slices the false-positive rate in half | **Refuted.** 65.2% → 59.6%, p = 0.281, and it discards **2 of 12** correct findings. At >20 lines it discards **6 of 12** | user's proposal, checked before building |
| 11 | The findings may point at the right code even when the claims are wrong | **Null.** Spoke 30.0% vs silent 40.0%, p = 0.70. The location signal is the **ranker's** | user's hypothesis |
| 12 | Model confusion may mark defective code | **Directional only.** 57.5% vs 50.5% base, +7.0, **p = 0.394 on 40 units** | user's hypothesis, unresolved |
| 13 | The execution gate raises precision | **Inverted and significant.** Where the model *proves* its claim, the code is **less** likely to be fixed: 36.5% vs 50.5%, **p = 0.003**, and **p = 0.001** controlling for length | me |

**Thirteen predictions. Ten wrong, and nine of those were mine.**

---

## 3. The mechanism, established

**87.3% of claims that quote code, quote code that is not at the line they cite.**
→ 71 of 93 findings carrying a backticked identifier.

The model writes a plausible defect narrative naming `flat_data.view()`, then separately emits a
line number pointing at `images = flat_data.reshape(-1, 8, 8)`. **The prose and the anchors are
generated independently and nothing forces them to agree.** That single fact explains why designs
1–5 could not have worked.

**And the deeper one, from design 13:** demonstrability and defectiveness are **anti-correlated**.
The model can build a working demonstration when code is simple enough to reason about in
isolation, and such code does not break. **This is why the gate raised TRIVIAL from 7.7% to 28.6% —
the same fact measured twice.**

---

## 4. What the failures actually are

The 32 wrong findings on the unseen corpus, by the raters' own stated reasons:

| reason | share |
|---|---|
| the cited line does not contain the code described | 43.8% |
| claims a merged, passing test is broken | 21.9% |
| refuted by code one to three lines from the citation | 18.8% |
| wrong about Python itself | 12.5% |
| arithmetic it could have performed itself | 3.1% |

**Three of the "wrong about Python" claims were executed and refuted in one line each**: closing a
never-started coroutine does not raise; `list.insert` cannot raise `ValueError`; aware datetimes in
different zones compare equal. → `research/phase0/vertex/triage/execute.py`

---

## 5. The external check — this is not a local failure

[SWR-Bench](https://arxiv.org/html/2509.01494v1), 1,000 pull requests, five published automated
review systems:

| technique | precision |
|---|---|
| PR-Review | 15.39% |
| LLM-Reviewer | 9.22% |
| SWR-Agent | 9.11% |
| CR-Agent | 6.23% |
| Hybrid-Review | 2.79% |

**Ours: 5.80% pooled, 2.22% on unseen code, 12.96% at the best single design.** Inside their range.

Their conclusion: *"SOTA ACR techniques, when paired with SOTA LLMs, are not yet ready for
real-world code review deployment."*

**The review half is not badly built. It is a problem nobody has solved.**

---

## 6. What survives, and it is the product

| asset | evidence |
|---|---|
| **The ranker** | 1.53% miss against alphabetical's 2.97% and chance's 3.37% — **20 repositories, 7,989 events, three disjoint samples, p = 1.3 × 10⁻¹⁴, 17 of 20 positive.** Against chance the lift is **+1.84 points**, so the published figure is conservative |
| **The corrected attribution rule** | 67.9% of file-overlap verdicts blame a change sharing no symbol with the fix. Three corpora, **computed without the ranker** |
| **Typed coverage** | A construction, not a measurement. `Unresolved(site, reason, construct)` cannot be built without all three fields |

**And the location signal is the ranker's alone**: on the aged corpus, ranker-funded units hit
50.5%, and the model's decision to speak moves that to 49.3%.

---

## 6b. Form does not predict truth — a road closed for an hour and no model calls

**Nothing here had ever measured FORM.** Every number in this record is about truth: is the claim
correct, does it point at the right line, can a parser confirm it. Whether a finding is one line or
six, concrete or hedged, names a fix or waves at a problem, had never been looked at.

**n = 152, two designs, two corpora, every finding that still has its text joined to its blind
verdict.** → `research/phase0/quote/form_vs_truth.py`

| form feature | n | WRONG | vs rest | Fisher p |
|---|---|---|---|---|
| *(all findings)* | 152 | 58.6% | | |
| **hedged** | 27 | 59.3% | 58.4% | **1.0000** |
| definite wording | 63 | **66.7%** | 52.8% | 0.0971 |
| has a code token | 120 | 59.2% | 56.2% | 0.8408 |
| names a fix | 25 | 48.0% | 60.6% | 0.2715 |
| short (≤ 20 words) | 19 | 47.4% | 60.2% | 0.3258 |
| long (> 40 words) | 16 | 81.2% | 55.9% | 0.0623 |

**HEDGING IS NOT A FILTER. 59.3% against 58.4%, p = 1.0000** — a perfect null on the headline
feature, and the one everybody assumes will work.

**THE INVERSION IS THE USEFUL PART: `definite wording` is the WORST of the confident forms at 66.7%
wrong.** That is the mechanism behind this project's most memorable failures, measured rather than
anecdotal — *"Version 1.45.34 of awscli does not exist on PyPI"* is one line, specific, unhedged,
and false. **Somebody will eventually propose publishing only the confident findings. This is the
answer.**

**The trends are not nothing, and they are not usable.** Short is 47.4% against 60.2%, names-a-fix
48.0% against 60.6%, long 81.2% — all pointing where the intuition says they should. **The direction
is consistent with the intuition and the effect sizes are within noise at this n.** The closest to
significance, `long` at p = 0.0623, is a reason to CUT long comments rather than a way to find true
ones.

**AND THE CORRECT-RATE IS THE SENTENCE THAT CLOSES IT: 3.7% to 12.0% across every form.** Even the
best-formed slice tops out at one in eight. Unlike a wrong-rate, that is a number **no deletion can
improve** — the same argument that killed design fourteen's exclusion, applied to a different lever.

**This is the third attempt to find truth in the surface of the text**, beside the anchor repairs
and the lexical marker. The corpus study concluded review content is not keyword-shaped; this
concludes findings are not form-shaped either.

**Which leaves the schema as the only lever, and for a reason worth stating precisely: it does not
reward good form, it makes bad form INEXPRESSIBLE.** A model cannot hedge inside five typed fields.
That is why **≥ 39% surviving** matters, and why **150 hand-graded findings by someone who did not
write the definition** is the last thing standing.

---

## 7. How to move forward

**Do now:**
1. **Build the deterministic half** — `store/`, `ingest/`, `parse/`, `rank/`, `render/`. No `infer/`.
   Every component is measured; none needs a model.
2. **C4 — three teams, thirty days.** The only untested question is whether anyone wants it, and no
   amount of compute answers it.

**Do not do:**
- **A seventh review design.** Seven have failed against pre-registered bars, and the field's
  benchmark is the prior.
- **A function-length hard gate.** Refuted under "What was predicted, and what actually happened" before it was built.
- **Publishing findings, or locations derived from findings.** the section "What survives, and it is the product" shows the locations are the
  ranker's.

**Open hypotheses, pre-registered for whenever the review half is picked up as a separate project:**
- **Model confusion as a defect locator** — `preregistrations/ranker/future-fix-preregistration.md` "The inversion the data supports, and the one it does not". Needs ~80 confused units against a 50.5%
  base ≈ 3× the current aged corpus. **Must beat the ranker, which is free.**
- **Function size as a moderator** — `evidence-ledger.md` "The pooled pattern across all 207 adjudicated findings". Real at the extremes — 45.9% wrong
  at ≤10 lines against 89.3% above 80 — but not monotonic, and found by sweeping 207 findings, so
  it needs a fresh corpus and a bar fixed first.
- **Complementarity with an incumbent reviewer** — `greptile-gap-analysis.md` "The union result —
  parked, not claimed". On Martian's offline layer our arm and Greptile's overlap at only 43.7%
  Jaccard, and between them cover 68.8% of the golden set against 52.0% for Greptile alone — above
  the ~63% ceiling no single tool of 48 has passed. **The bar is not a benchmark score.** A
  complementarity product publishes findings, so it must first clear the one the review half failed
  seven times: **under 50% of published findings wrong, under adjudication that checks anchors** —
  which this benchmark does not. And the union may be an artefact: the self-preference correction
  already removes ~4 of our 29 unique catches.

---

## 7b. Five measurements have confirmed the closure, and none has challenged it

**A closure is only as good as what came after it.** Five measurements have been taken since Half B
closed on 0 of 45, and every one confirmed it. None was designed to; three were attempts to reopen
it.

| # | measurement | result | direction |
|---|---|---|---|
| 1 | schema survival on the 207 | recall floor ≥ 39%, ceiling unknown | did not reopen |
| 2 | expansion and conventions (design thirteen) | moved nothing | confirmed |
| 3 | isolated judge, different family | same-family judge agreed with a careful rater on 34.9% | confirmed the judge, not the parser |
| 4 | form versus truth | null — form does not predict truth | confirmed |
| 5 | three prompt-direction arms | all FAIL; generator retains 8.5–16.8% of the discrimination over its own output | confirmed |

**The fifth is the strongest, because it measured the thing the closure assumed.** The closure said
the parser cannot refute a wrong semantic finding. Measurement five says the *generator* cannot
either — asked to keep only what it would defend, it deleted three-quarters of its findings and
closed 10% of the distance to a perfect cut, with 130 false positives available to delete.

**Five confirmations after a closure is the pattern that distinguishes a correct closure from a
premature one.** A premature closure is contradicted by the next thing measured; this one has
survived every attempt, including the ones built to overturn it. Recorded here so a later reader
proposing to reopen the half can see what reopening would have to beat.

Four fixes measured since are recorded rather than built, for one shared reason — they improve a
ratio without creating a correct finding. → `docs/findings/reviewer/recorded-not-built.md`

## 8. Where everything is

| what | where |
|---|---|
| every adjudicated verdict, unified | `research/phase0/results/all_verdicts.json` |
| per-design verdicts | `results/{adjudication,enriched,fresh,symbol,window,execution_*}_verdicts.json` |
| the aged corpus scored against git | `results/future_fix_scored.json` |
| ranker replication, three samples | `results/defect_return_{external,third}.json`, `discriminability_*.json` |
| pre-registrations, one per design | `docs/plans/preregistrations/{ranker,reviewer}/` |
| design thirteen: expansion, conventions | `research/phase0/quote/results/quote13_run.json`, `quote/adj13/` |
| **every number recomputed from its artefact** | `research/phase0/claims/verify.py` — **108 checks, 108 passing** |

**Run `python3 verify.py` from `research/phase0/claims/` before quoting any figure in this
document.** This project has shipped a wrong number three ways — a cost table that priced one call
for three, a κ of 0.66 reported as 0.92, and an anchor check reading 98.1% while the anchors were
still wrong.
