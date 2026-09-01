# D6b — human context as model input

**Status: RUN 2026-08-31 AGAINST THIS DOCUMENT'S OWN INSTRUCTION NOT TO RUN IT. RESULT WITHDRAWN
2026-09-01 — it was shot noise.** → `docs/findings/reviewer/D6B_HUMAN_CONTEXT_NULL_2026-08.md`.

A control-vs-control replicate (the same prompt twice, scored identically) moved **+2 TP with
14/36 changes discordant**. The treatment moved **-3 TP with 18/36**. The same control prompt
scored 54, 51 and 53 on three runs. **The treatment moved the pipeline less than the pipeline moves
on its own**, so the run measured nothing and the result is withdrawn rather than qualified.

Everything below the line was written BEFORE the run and is unedited, except this header and the
two corrections at the foot, which record defects the run exposed in this document itself. The
power analysis below stands and is why the null is reported as uninformative about a small effect
rather than as evidence of none.

| bar | required | measured |
|---|---|---|
| effect | > 0 | **-3** (54 -> 51 golden defects) |
| McNemar exact | p < 0.05 | **0.4807** (7:11) |
| repositories positive | >= 4 of 6 | **1 of 4** -- and see correction 1, this bar was unmeetable |

---

## The exact claim under test

*Showing the model the human context behind a change — the pull request's stated goal and the text
of the tickets it names — raises the count of golden defects found, on the changes that HAVE such
context, against the same reviewer without it.*

The population is named deliberately. **On a change with no stated goal the two arms are identical
by construction**, so scoring over all 50 golden changes would dilute any real effect by a third
and report a smaller number than the truth. The unit is one golden change; the pairing is the same
change reviewed both ways.

## What is already known, and it is discouraging

- **Shape-context went PASS to NULL.** It cleared `> +2.1 points` twice, then McNemar returned
  9:15, p = 0.31, with the whole effect carried by one repository of five.
  → `docs/findings/reviewer/shape-context-result.md`. The memory recording it as passing was
  retracted.
- **Five prompt levers have moved nothing**: anchor repair, structured context, a rejection filter,
  hunk expansion, and the reviewer redesign of design fourteen.
  → `design14-model-lever-preregistration.md`.
- **Raw model findings are 66.7–82.1% wrong across four blind pools.**

**Why this one is different in kind, stated before the run so it cannot be claimed afterwards:**
every lever above varied how the diff was PRESENTED. Human context is not in the diff at any
presentation. A ticket saying *"the weights re-download on every start, we agreed to cache them"*
carries a fact no shape feature contains. That is an argument for measuring it, and it is not
evidence, and this section exists so nobody later reads it as evidence.

## The exposed population, measured before the bars were fixed

Measured with the product's own `ingest/context/issue_refs.references` and
`ingest/context/tickets.behind` over the 50-change golden corpus
(`research/phase0/bench/martian/data/golden_comments`, 5 repositories × 10 changes):

| | |
|---|---|
| carry a resolvable reference | 21 / 50 (42%) |
| carry usable context — stated goal and/or ticket titles, ≥120 characters | **33 / 50 (66%)** |
| context too thin to differ on | 17 / 50 (34%) |

**33 is the largest n any paired arm on this corpus can have.**

## The power calculation, done BEFORE the run

McNemar's exact test is a binomial sign test on discordant pairs, so power is exactly computable.
At n = 33, α = 0.05, two-sided:

| context helps | hurts | net | power |
|---|---|---|---|
| 10% | 5% | +5% | **2.9%** |
| 15% | 5% | +10% | **12.1%** |
| 20% | 5% | +15% | **27.6%** |
| 25% | 5% | +20% | 45.7% |
| 30% | 5% | +25% | 62.8% |
| 30% | 0% | +30% | 95.9% |

**The smallest net effect this corpus can detect at 80% power is +32%** — context would have to
help 37% of exposed changes while hurting 5%. No lever in this project's history has moved anything
by 32%, and the five that were measured moved nothing at all.

**So at any effect size worth believing, this corpus returns a null roughly 7 times in 8 whether or
not the effect is real.** Running it would produce an uninterpretable result that would be read as
"human context does not help" — a conclusion the data could not support and which would be hard to
undo. **That is the reason this is not being run, and it is a methodological reason, not a
resource one.**

### What a corpus would have to be

| true net effect | exposed changes needed | golden changes needed at 66% exposure |
|---|---|---|
| +20% | 65 | ~98 |
| +15% | 95 | ~144 |
| +10% | 170 | **~258** |
| +10% with 10% harm | 250 | ~379 |

**A corpus of roughly 250 hand-labelled changes is the entry price** for a +10% effect. The
existing golden corpus took considerable hand-labelling to reach 50.

## The bars, fixed now, for whenever that corpus exists

Copied from `defect-return-external-preregistration.md`, which is the standard the ranker half
holds and the reviewer half has not:

**CONFIRMED requires all three:**
1. Effect > 0 on golden defects found over the exposed population.
2. **McNemar exact p < 0.05** on the paired discordant changes.
3. **≥ 4 of 6 repositories individually positive.** The current corpus has 5 repositories, so a
   corpus meeting the power requirement must also reach 6 — shape-context's failure was precisely
   an effect carried by one repository of five, and a margin alone would not have caught it.

**NULL** is any result failing any of the three. **A margin without the statistic is not a pass**,
which is the sentence `TEMPLATE.md` was written to enforce.

## Method — parameters copied, not chosen

- **Judge:** an isolated judge of a DIFFERENT family, per the product principle. A same-family
  judge agreed with a careful rater on 34.9%.
- **Arms:** identical prompts except for one appended block containing the stated goal and ticket
  text. Nothing else varies — not temperature, not the diff, not the cap.
- **Scoring:** golden defects found, the same measure design fourteen used, so the numbers are
  comparable to the levers that failed.
- **Exposure filter:** `tickets.behind()` returning ≥120 characters, the threshold used in the
  measurement above and fixed before any outcome was seen.

## Two things D6b needs that do not exist yet

1. **`Ticket` carries no body.** D6a fetches the title and state only, so "the same text as model
   input" has no text to be the same as. Fetching bodies is a change to D6a and more egress.
2. **Ticket bodies are an egress question.** `ingest/context/egress.py` (D6c) governs quoting into
   a comment; feeding text to a model is a third destination that consent file does not yet name.

## What would refute the design rather than the hypothesis

- If the exposed population on a new corpus falls below 66%, the power table above is optimistic
  and the required n rises.
- If the two arms produce identical output on more than ~85% of exposed changes, the discordant
  count collapses and no achievable n will help — that would say the model ignores the block, which
  is a finding about the prompt and not about context.


---

## Corrections, written after the run

**0. The largest defect is that this run happened at all.** The section below headed "The power
calculation, done BEFORE the run" concludes, in bold, that running it "would produce an
uninterpretable result" and that "this is not being run". It was run. The low-power sentences later
attached to the result are not caveats on a finding — they are a restatement of the reason the
finding should not exist. **A pre-registration that decides against a run, and is then overridden,
must record the override here rather than in the result.**

**1. Bar three could never have been met.** ">= 4 of 6 repositories individually positive" was
copied from `defect-return-external-preregistration.md` without checking that this corpus has six
repositories. It has five, and four after the discourse exclusion below. **A threshold nobody
checked was reachable is not a bar.** Same class of error as the power calculation design fourteen
skipped -- appearing in a document whose whole purpose was to avoid that class.

**2. The exposed population is 36, not 33.** The feasibility script read each golden entry's `url`;
the runner reads `original`. They differ on 13 of 50, where `url` is a synthetic pull request the
benchmark harness created and `original` is the real commit. The feasibility number was therefore
partly measuring the harness's text as the author's. The runner excludes commit-backed entries --
a commit has no description and no ticket, so no arm can be given context about it -- leaving 37
real pull requests, 36 exposed. **"Two code paths, one column", in the feasibility measurement.**


**3. There was no noise floor, and that is the defect that voided everything.** One draw per arm on
a pipeline with two stochastic stages. Neither the Method section nor the bars required a
control-vs-control replicate, and none was run until an adversarial audit demanded it. Shape-context
is cited in this document as the reason bar three exists; its actual lesson — the effect was smaller
than the noise floor — was the one not learned. **Any future arm here runs its replicate first.**

**4. Two further requirements were unmeetable, like bar three.** The Method promises "an isolated
judge of a DIFFERENT family"; the judge was `gemini-2.5-pro` scoring `gemini-2.5-pro`, because no
other capable model is reachable from this project. And "Two things D6b needs that do not exist yet"
names `Ticket` carrying no body as a blocker — the run administered ticket TITLES, so the treatment
argued for was never given.
