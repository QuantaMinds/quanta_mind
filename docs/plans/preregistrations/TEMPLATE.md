# Pre-registration template — copy this file, do not write one from scratch

**Why this file exists: the reviewer half has been pre-registering margins while the ranker half
pre-registered statistics, and the difference is visible in the results.**

`defect-return-external-preregistration.md` requires `CONFIRMED` to mean *effect > 0 **and** McNemar
exact p < 0.05 **and** ≥ 4 of 6 repositories individually positive*. `ranking-rerun-preregistration.md`
adds a sign test across repositories. Those are the pre-registrations behind the one claim this
company rests on.

The reviewer-side pre-registrations mostly fixed a threshold and stopped there. **A threshold with no
statistic can be passed by noise, and one was**: the shape-context arm cleared `> +2.1 points` twice,
and then McNemar returned 9:15, p = 0.31, with the whole effect carried by one repository of five.
It passed the bars it set and failed the standard the rest of the project holds.
→ `docs/findings/reviewer/shape-context-result.md`.

**A verdict table naming only a margin is not a pre-registration. It is a hope with a number in it.**

---

## The exact claim under test

One sentence, falsifiable, naming the population. Not "does context help" — *"showing the model the
change's shape raises defects found on the fifty-change golden corpus."*

## What is already known, and whether it is discouraging

State the prior honestly, including the failures. If five levers have moved nothing, say so here and
say why this one is different in kind. A pre-registration that omits an unfavourable prior is
choosing what the result will be allowed to mean.

## Method — parameters copied, not chosen

Every threshold, window and cap either copied from a prior study (cite it) or justified before the
run. A parameter chosen after seeing data is a result, not a method.

## The readings, fixed now

What is measured, by what code, written to what artefact.

## The verdict — ALL THREE ROWS ARE REQUIRED

| | condition | why it cannot be dropped |
|---|---|---|
| **direction** | the point estimate moves the right way by more than <bar> | necessary, never sufficient |
| **paired statistic** | **McNemar exact, b:c reported, p < 0.05** | 9:0 and 25:16 give the same margin and opposite conclusions. **Report b and c as integers, not only p** |
| **per-unit consistency** | **≥ <k> of <n> repositories individually positive**, each unit's b:c reported | an effect carried by one unit is that unit's property, not the method's |

| outcome | means |
|---|---|
| **CONFIRMED** | all three rows hold |
| **NULL** | direction fails, **or** p ≥ 0.05 |
| **INCONCLUSIVE** | direction and p hold but per-unit consistency fails, **or** an interval spans a bar |

**A near-miss is a NULL. An interval spanning a bar is INCONCLUSIVE and does not ship.**

### If the design is not paired, say so here and name what replaces it

Fisher, a sign test, a bootstrap over units — but name it now. "We will decide how to analyse this"
is the sentence this template exists to prevent.

## The noise floor, and which term of it the bar covers

**State explicitly whether the bar covers generation variance, judging variance, or both.** They are
different sizes. The shape arm's `2.1 points` was the *judge's* replicate spread — re-scoring the
same outputs — and a later re-judge moved one arm by 3 defects on its own, roughly 1.7 points.
Generation variance, the larger term, was never in the bar at all.

**If a same-arm replicate has not been run, the bar is a partial floor and this section must say so.**
→ `research/phase0/bench/forensic/shape/replicate.py` is the pattern: run the control arm twice,
where the true effect is zero by construction.

## The corpus, and its burn

Which repositories, how many units, and whether any has been used before.
→ `scripts/guard/records/check_burned_corpora.py` enforces reuse; declare it here anyway.

**Name the unit the statistic is computed over, and how units are grouped.** Grouping the shape
corpus by URL host rather than the corpus's own `repo_file` split one repository across two clusters
and hid a one-repository effect — in precisely the analysis that later overturned the result.

## Blinding

State what the judge or rater sees. **"Blind to arm" is not the same as "immune to the treatment"**:
if the intervention changes how findings are *phrased*, a judge can reward the phrasing without the
finding being better. Blinding closes label leakage and nothing else. Name the residual channel.

## What could still silently fail

The section that ages best. What would make this result wrong while every check still passes?

---

## After the run — append, never edit

Results go **below** the pre-registration in the same file, under a `# RESULT` heading with the date.
The bars above are never edited afterwards. If a statistic is added after seeing the data — as
McNemar was for the shape arm — **say so in the result section and say which direction it moved the
verdict.** Tightening a standard against your own favourable result is defensible; doing it silently
is not.
