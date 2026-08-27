# Fixes recorded rather than built

> **The corpus under all of this has a ±4-point noise floor, measured 2026-08-27.** Two runs of the
> same arm, no change between them, scored 91 and 84 of 173 defects. Before revisiting any road
> below, compare its effect to 4 points. → `corpus-noise-floor.md`



Four measured improvements to the reviewer half, each with an effect size, each not built. They
share one reason and it is not cost: **the reviewer half is closed.** Half B failed on 0 of 45 —
the parser can refute none of the wrong findings — and the optimistic case still misses the field
floor by 37 points. A component of something that does not ship is not worth building, however
sound the measurement behind it.

They are recorded because the arithmetic is real and re-deriving it later would cost more than
writing it down. **If the reviewer half is ever reopened, start here, in this order.**

**Two of these were closed by measuring a base rate before building.** The register now records
what was closed as well as what was deferred, because "we did not build it" and "we measured it and
it cannot fire" are different facts and only one of them should be revisited.

## The screening rule — ask before you measure

> **A pinned version that does not exist fails CI on the first install, so almost none survive on a
> main branch.**

That is the mechanism behind the registry class's 0.00% base rate, and it generalises: **before
measuring a base rate, ask whether CI would already have caught the defect. If it would, expect
zero.** It would have predicted the registry result without the run.

It does **not** replace measurement where the answer is not obvious. The SHA→tag class is invisible
to CI — a workflow pinned to a real commit with a stale version comment builds perfectly — which is
exactly why its rate came back non-zero at 0.24%.

## UNTESTED and REFUTED are different states, and the register says which

Six roads are closed here. **They are not closed for the same reason, and collapsing them would
lose the only thing that decides whether to revisit one.**

| road | state | why |
|---|---|---|
| registry-existence **detector** | **REFUTED** | base rate 0.00% of 176 real pins; it would never fire |
| date injection as a **fix** | **REFUTED for this pool** | the defect did not reproduce on three live diffs |
| five prompt levers | **REFUTED** | measured, all null |
| model-authored proof gate (design 13) | **REFUTED** | inverted at p = 0.001 controlling for length |
| per-category thresholds | **UNTESTED** | never measured, deferred |
| **execution grounding** | **UNTESTED** | published evidence behind it; **this pool cannot test it** |

**A REFUTED road stays closed.** An UNTESTED one is waiting on an instrument, and execution
grounding is waiting on a specific one:

> **a corpus of semantic findings about SOURCE code covered by an existing suite, large enough that
> 7 correct findings do not collapse to 2.**

Step 0 established why this pool is not it: of the 16 semantic wrong findings, **44% are claims
about test code** — where the suite doing the adjudicating is the subject of the claim — **19% are
about configuration no test imports**, and only **31% are about source a suite touches**. Of the 7
correct findings, 2 are coverable, so the hard stop would be a bar over a population of two.

**That is the independent-grader debt with a purpose attached.** It was a general obligation; it is
now a specific one, and what it would buy is stated: the only mechanism with published evidence
that nobody here has been able to test.

## Verifier and detector are different products of the same oracle

The two are worth different amounts and conflating them hides it. Stated once here, because
"base rate 0.00%, verifier ships" reads as a contradiction without it:

| | what it does | its value depends on |
|---|---|---|
| **detector** | reads the diff and states a defect itself | how often the defect **occurs** |
| **verifier** | refutes the reviewer's claim about the diff | how often the **model asserts** it |

A class can have a zero base rate and a worthwhile verifier: registry existence never occurs in the
wild, and the reviewer claimed it three times in 45.

| fix | measured worth | evidence |
|---|---|---|
| deduplication | +4.0 points golden-level precision, 18% of the gap to Qodo | `research/phase0/bench/forensic/redundancy.py` |
| live registry lookup — **verifier BUILT, detector CLOSED** | verifier refutes 3 of 45; detector base rate **0.00%** of 176 real pins | `research/phase0/bench/forensic/registry_prevalence.py` |
| SHA→tag oracle — **BUILT, both halves** | verifier kills 31% of wrong findings; detector base rate **0.24%** of 1,244 real pins | `research/phase0/bench/forensic/pin_prevalence.py` |
| date injection | addresses 11% of wrong findings | `docs/product/reviewer/external-evidence-2026-08.md` |
| per-category thresholds | not sized; category rates differ 0%–45% | `docs/product/reviewer/greptile-gap-analysis.md` |

## Deduplication — the arithmetic

All four arms judged in one pass over the same 50 pull requests and 173 goldens:

| arm | comments emitted | matched something | goldens covered | redundant | rate |
|---|---|---|---|---|---|
| qodo-extended-v2 | 152 | 99 | **98** | +1 | **1.0%** |
| greptile-v4-1 | 168 | 93 | 86 | +7 | 7.5% |
| **OURS** | **194** | **98** | **81** | **+17** | **17.3%** |
| coderabbit | 318 | 140 | 106 | +34 | 24.3% |

Our 98 matching comments and Qodo's 99 are the same number. **They are not the same coverage** —
theirs land on 98 distinct defects, ours on 81. The rate orders all four arms exactly as their
published quality does.

Golden-level precision is covered ÷ emitted. Removing all 17 redundant comments, changing nothing
else:

- ours today: 81/194 = **41.8%**
- ours deduplicated: 81/177 = **45.8%** — **+4.0 points**, above the 2.1-point judge noise floor
- qodo: 98/152 = **64.5%**

**That is 18% of the 22.7-point gap.** The other 18.7 points is that Qodo emits 53 comments
matching nothing where we emit 96. Closing that means deleting about 43 more wrong comments, and
the generator cannot pick which — it retains **8.5–16.8%** of the available discrimination over its
own output. → `docs/plans/preregistrations/reviewer/prompt-direction-preregistration.md`

## Why none of these reopens the question

Deduplication moves a benchmark precision number. **It does not create a correct finding**, and the
closure was never about precision — it was that the parser cannot refute the wrong findings and the
ceiling misses the field floor by 37 points. A fix that improves the ratio without adding a true
finding leaves both of those exactly where they were.

This is the fifth measurement since the closure that confirms it rather than challenges it.


## What the noise floor does and does not change here

**Measured 2026-08-27: two runs of the same arm, differing only in model nondeterminism, scored 91
and 84 of 173 defects — a 4.0-point gap from nothing.** → `corpus-noise-floor.md`. Applied to this
register, honestly, in both directions.

**It does NOT reopen the five prompt levers, and the numbers say so plainly.** Those arms did not
fail to move; they moved hard the wrong way. `A1_ABSTAIN` took true positives per pull request from
2.16 to **0.61 — a 72% collapse** — and `A2_AIM` to 1.76. A floor of four points on a
173-defect denominator does not touch a −72% move on a different metric. **REFUTED stays REFUTED.**

**It DOES put a caveat on deduplication, the largest deferred fix.** `+4.0 points golden-level
precision` sits exactly on the floor. Two things keep it from being dismissed and neither makes it
safe:

- **The metric is not the same one the floor was measured on** — golden-level precision, not
  defects found of 173 — so the floor does not transfer arithmetically.
- **Redundancy is a structural count within a single run** (17 of 98 comments restate a sibling),
  not a two-arm comparison, so it is not exposed to between-arm variance in the same way.

**But the run it was counted on is one sample, and comment composition is now known to be
unstable**: two identical runs disagreed by 0.76 comments per change, up to 4 on one change, while
totals barely moved. **A duplicate count drawn from one run inherits that.** The +4.0 should be
re-derived across two runs before anything is built on it. That is a cheap check — the arms are
already stored — and it is not the same as doubting the mechanism, which is model-free and sound.

## Shape context — MEASURED, and it did not clear the floor

| road | state | why |
|---|---|---|
| **shape context in the prompt** | **NULL** | +9 defects on first judging, +6 on re-judging the same comments, against a **±4.0-point floor**; McNemar 9:15, p = 0.31; 2 of 5 repositories improve, 1 worsens |

**It belongs in a different row from the five prompt levers.** They were refuted by moving the
wrong way. This one was never resolvable on this corpus — the effect and the noise are the same
size. `PLAIN_A` scored 91, beating the 90 the treated arm scored in the run that produced the
headline.

**The mechanism is untouched.** The shape block states facts a diff cannot supply, and it is
wired, tested and free. What failed is the attempt to show it helps, on an instrument that cannot
resolve a six-defect effect. → `shape-context-result.md`.
