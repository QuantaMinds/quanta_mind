# D6b — human context as model input: NULL, and the point estimate is negative

**Run: 2026-08-31.** Pre-registered before execution →
`docs/plans/preregistrations/reviewer/d6b-human-context-preregistration.md`.
Artefact: `research/phase0/bench/results/d6b_human_context.json`.
Runner: `research/phase0/bench/run_d6b.py`.

---

## The result, against the bars fixed before the run

| bar | required | measured | |
|---|---|---|---|
| effect on golden defects found | > 0 | **−3** (54 → 51) | ✗ |
| McNemar exact | p < 0.05 | **p = 0.4807** (7 better : 11 worse) | ✗ |
| repositories individually positive | ≥ 4 of 6 | **1 of 4** | ✗ |

**NULL.** All three fail, and the point estimate points the wrong way.

## What the arms actually did

36 exposed changes, 116 golden defects, identical prompts except one appended block carrying the
pull request's stated goal and the titles of the tickets it names.

| | TP | FP | candidates | precision | recall |
|---|---|---|---|---|---|
| control | 54 | 77 | 131 | 41.2% | 46.6% |
| context | 51 | 92 | 143 | 35.7% | 44.0% |

**The context arm said MORE and found LESS.** It emitted 12 more candidate findings than the
control, and every one of them plus three more was wrong: +15 false positives, −3 true positives.
Precision fell 5.5 points and recall fell 2.6.

That is a mechanism, not just a number: **the block does not make the reviewer more careful, it
gives it more to talk about.** Told what a change was for, the model appears to generate findings
about whether the change achieves it — which the golden set, being a list of defects, does not
reward.

**This does not license the sentence "human context hurts."** p = 0.48 is entirely
noise-consistent, and the pre-registered power analysis said this corpus could not detect anything
smaller than +32%. The honest claim is the narrow one: **on this corpus, adding stated goals and
ticket titles to the prompt did not raise golden defects found, and the direction was negative.**

Per repository: cal.com +4, grafana −5, keycloak −2, sentry ±0. One positive of four — and the one
positive is the same shape shape-context failed on, an effect carried by a single repository.

## This is the sixth lever, and the first to trend negative

Anchor repair, structured context, a rejection filter, hunk expansion, the design-fourteen redesign,
and now human context. Five moved nothing; this one moved slightly the wrong way, within noise.
→ `design14-model-lever-preregistration.md`.

---

## Two defects in my own pre-registration, found by running it

**1. Bar three was unmeetable from the moment it was written.** It required "≥ 4 of 6 repositories
individually positive", copied from `defect-return-external-preregistration.md`. The golden corpus
has **five** repositories, and after excluding discourse (below) it has **four**. A bar requiring six
could never have been met by any result, so it was not a bar — it was a sentence that looked like
one. **This is the same class of error as the power calculation design fourteen skipped**: a
threshold nobody checked was reachable. Copying a parameter is right; copying it without checking
the corpus can satisfy it is not.

**2. The exposed population was 36, not 33, because two code paths read different fields.**
`scripts/measure/context/exposure.py` read each golden entry's `url`; `run_d6b.py` reads
`original`. They differ on 13 of 50 entries, where `url` points at a synthetic pull request in
`ai-code-review-evaluation/discourse-graphite` created by the benchmark harness and `original`
points at the real commit. **The feasibility script was therefore partly measuring the harness's
own text as though it were the author's.** The runner excludes those 13 — a commit has no
description and no linked ticket, so neither arm can be given context about it — leaving 37 real
pull requests of which 36 are exposed.

This is the failure this repository already records as "two code paths, one column", occurring in
the feasibility measurement for an experiment about not making that kind of mistake.

## What would change the answer

- **A corpus meeting the power requirement**: ~250 hand-labelled changes across ≥6 repositories for
  a +10% effect. This run had 36 and could only have detected +32%.
- **A metric that is not a defect list.** The observed mechanism is that context produces findings
  about whether the change achieves its goal. The golden set scores defects, so such a finding is a
  false positive by construction even when it is true and useful. **If the product's value is
  "does this change do what it says", the benchmark measuring it is the wrong one** — and that is a
  question about what to measure, not about whether context helps.
- **Ticket bodies rather than titles.** `Ticket` carries no body, so the arm saw the pull request's
  own description plus ticket *titles*. The strongest form of the hypothesis was not tested.
