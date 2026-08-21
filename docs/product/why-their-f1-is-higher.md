# Why Greptile and Qodo score higher, what the metric actually rewards, and whether our thesis closes it

> **INTERNAL.** Figures governed by `docs/product/publishing-rules.md`. Recomputed from
> `research/phase0/bench/results/` — not read off the prose.

**The short answer: we are not worse at finding issues. We are worse at throwing away our own bad
ones.** Our recall already equals Qodo's. Our precision is half theirs because we emit three times
the candidates to get there, and nothing downstream discards the wrong ones.

---

## 1 · How the score is actually computed

`research/phase0/bench/judge.py` implements Martian's aggregation verbatim:

- every (golden comment, candidate issue) pair is judged **semantically** by an LLM — "same
  underlying issue", different wording fine
- a golden is a **true positive** if **any** candidate matches it
- a candidate is a **false positive** if it matched **no** golden

**So every candidate that does not map to a human's written comment is counted against you, whether
or not it is true.** The metric does not ask "is this correct?", it asks "did a human write this
down?". Precision here is a **selectivity** measure, and volume is punished linearly.

That single property explains the entire leaderboard.

## 2 · The measurement that settles it

Two arms of our own reviewer, same 50 pull requests, same 173 golden comments, same judge:

| arm | candidates | TP | FP | **precision** | **recall** | **F1** | noise/PR |
|---|---|---|---|---|---|---|---|
| ours, nits **suppressed** | 181 | 79 | 102 | 43.6% | 45.7% | 44.6% | 2.0 |
| ours, nits **allowed** | **464** | **100** | **364** | **21.6%** | **57.8%** | 31.4% | 7.3 |
| greptile-v4-1 | 161 | 91 | 70 | 56.5% | 52.6% | **54.5%** | 1.4 |
| qodo-extended-v2 | 152 | 99 | 53 | **65.1%** | **57.2%** | — | 1.1 |
| coderabbit | 288 | 105 | 183 | 36.5% | 60.7% | 45.6% | 3.7 |

**Read the two bold rows together. Our nits arm finds 57.8% of the golden issues; Qodo finds
57.2%. We are AT their recall.** We take 464 candidates to get there; they take 152.

**The gap is not detection. It is selection.**

### The nit hypothesis is refuted, and it was the obvious one

The category cross-tab said we catch **0%** of `style` issues where a rival catches 50%, and our
prompt bans exactly those categories. So: remove the ban. Recall rose 45.7% → 57.8%, and
**precision collapsed 43.6% → 21.6%, F1 44.6% → 31.4%, noise 2.0 → 7.3 per pull request.**

**Emitting the nits does not make us Greptile. It makes us much worse.** Suppression is the better
of our two arms — and that it is the better one is the diagnosis: our only lever is a *prior*
filter, applied before the model looks.

### The repository-context hypothesis is also refuted

The first theory was that rivals index the whole repository while we read one diff, so the gap
should sit in issues whose evidence is outside what we were shown. Cross-tabulated against a
mechanical marker — does the golden comment name an identifier absent from our diff? — it does not
separate: **27% "only them" on visible issues against 21% where the comment names nothing.** A
cause that does not separate outcomes is a story.

## 3 · What Greptile and Qodo actually do

**Qodo** runs **more than a dozen specialised agents** — backend bugs, UI, runtime failures, rule
violations, security, performance, accessibility — and then a **judge agent that resolves
conflicts, removes duplicates and filters low-signal results**, so only findings over a confidence
and relevance threshold reach the pull request. They ship two operating points, *Precise* and
*Exhaustive*. Their own framing:

> *"Precision can be tuned through filtering and prioritization once issues are found. **Recall
> cannot.** If a system fails to detect an issue, no amount of post-processing can recover it."*

> *"A single LLM trying to catch everything catches nothing reliably."*

**Greptile v4** does **multi-hop investigation** — reads the diff, finds affected dependencies,
**checks git history**, traces impact across files in a reasoning loop — then attaches a
**confidence score 0–5** and P0/P1/P2 severities, with customer-authored directives and severity
thresholds to tune the signal-to-noise ratio. It is openly the highest-false-positive tool of the
majors; the thresholds are how teams tame it.

**Both generate wide and then discard. We narrow before generating and never discard.** That is the
architectural difference in one sentence.

## 4 · Does our thesis close this gap?

**No — and it is important to say so, because the thesis attacks a different axis.**

The ranker reduces **what is read**. By Qodo's own argument, and by arithmetic, a mechanism that
reads *less* can only ever lose recall; it cannot raise precision on what it did find. Its measured
cost is a **1.21%** miss rate, which is small — but it is a *cost* line and a *latency* line, not a
quality line.

**And "we use git history" is not a differentiator either.** Greptile's v4 agent calls git history
as a tool inside its investigation loop. CodeRabbit scans commit history for files that change
together. CodeScene has done file-level change coupling since 2004. What is ours is using it
**deterministically, before the model, to bound what gets read** — a cost and predictability
property, not an accuracy one.

## 5 · What would close it, as a number

Take our widest measured net — the nits arm, 100 true and 364 false — and put a judge on it that
keeps every true finding:

| judge discards | FP left | precision | F1 | |
|---|---|---|---|---|
| 50% | 182 | 35.5% | 44.0% | |
| 75% | 91 | 52.4% | 54.9% | beats our suppressed arm |
| **85%** | **55** | **64.7%** | **61.0%** | **beats Greptile (54.5%), beats Qodo's own 60.1% F1** |
| 90% | 36 | 73.3% | 64.6% | |

**The product bet, stated as a number: the isolated judge must discard about 85% of false positives
while keeping the true ones.** That is demanding but it is the *only* lever on this metric, and it
is the lever both rivals are already pulling.

## 6 · So what is the differentiator

**Not the ranker, on quality.** It is a cost and latency mechanism with a measured 1.21% recall
cost. Keep it, sell it as economics, do not sell it as accuracy.

**Not "we have a judge" — Qodo already ships one.** Any evaluator disproves that claim in a minute.

**Three things survive:**

1. **A MECHANICAL gate BEFORE the model judge.** The decidability label is a rule, not a model:
   findings decidable from the diff were **0 of 14 wrong**, findings needing an outside fact were
   **9 of 15 wrong**, Fisher **p = 0.0007**. It costs no inference and removes exactly the class a
   model judge is worst at. Rivals' filters are model-only. **The caveat is in our own record: at
   n = 29 the intervals are wide, and the rater graded WRONG using reasoning correlated with the
   gate's rule, so the separation is partly structural.**

   **Cross-family judging is NOT on this list, and putting it here was an error.** The 2026
   guidance is flat: never use the same family as generator and judge. It is baseline practice, and
   anyone who reads the field says so. Our 34.9%-agreement result is a local measurement of a
   documented effect — on IFEval, where rubrics are programmatically verifiable, a judge is up to
   **50% more likely** to mark its own generator's failures as satisfied. That is the literature's
   finding, not ours.
2. **Typed silence and the coverage line** — verified unavailable to all seven competitors.
   Greptile's `Failed` means the run broke, not that analysis was incomplete.
3. **Bounded, predictable cost per repository** rather than per seat, because the ranker caps what
   is read.

**The honest strategic reading: we are one mechanism away from competitive, and it is the mechanism
we have just decided to build. Nothing else on the list closes an F1 gap.**
