# Design 14 — excluding the file kinds whose defects a diff cannot settle

Written before any model call. Bars are fixed here. A near-miss is a fail.

## This is not a new principle. It is the same one, applied to the last exception.

The path filter already excludes lockfiles, dependency manifests and documentation, all on the
decidability argument: **a diff-scoped reviewer should not be shown files whose claims a diff
cannot settle.** `.github/` was kept deliberately when that filter was written, and the reason was
evidential rather than sentimental — CI configuration was producing CORRECT findings at roughly
one in four, better than the corpus average at the time.

**That evidence has changed.** Design thirteen put CI-config findings at **66.7% wrong (24 of 36),
Wilson [50.3, 79.8]**, and **23 of those 24 are EXTERNAL** — undecidable from the diff by
construction. So this change is warranted by new data on a bigger sample, not by a rediscovery.
The record should read: the rule was applied, one exception was kept on evidence, and the evidence
turned over.

## The single change

`paths.py` gains `.github/**` and top-level `*.yml` / `*.yaml` to the excluded set. Nothing else
changes: same prompt, same gates, same expansion at `MAX_BACK = 20`, same conventions block.

## Corpus

Six repositories, each checked with `scripts/guard/records/check_burned_corpora.py --check owner/name` and
required to return **FRESH** — no prior mention anywhere under `research/`. That check exists
because `tornadoweb/tornado` entered design thirteen's corpus by eye and was already burned in the
aged corpus and two rater pools. Fifteen merged pull requests apiece.

## Hypotheses and bars

**H1 (primary).** Overall wrong-rate on unique published findings is **≤ 40%**, with the Wilson
upper bound also below 40% (the interval rule). Design thirteen's pooled figure was 52.6%; the
off-CI subgroup that motivates this ran 52.2 / 38.5 / 28.6% across arms.

**H1 is deliberately set ABOVE the off-CI subgroup figure it is inspired by.** That subgroup was
post-hoc, at n = 13 and n = 14, with Wilson intervals of [17.7, 64.5] and [11.7, 54.6] that overlap
arm A's [33.0, 70.8] almost entirely. **The clean monotone ordering is exactly what noise looks
like at that sample size**, and pre-registering 28.6% as the bar would be scoring a rule against
the data that produced it. 40% is the number that would still represent a real move if the
subgroup was half illusion.

**H2 (the mechanism, and the one that can falsify the reasoning).** EXTERNAL as a share of wrong
findings falls to **≤ 25%**, from design thirteen's pooled 50% (24 of 48 wrong were EXTERNAL). If
the exclusion works for the stated reason, this is where it shows. **If H1 passes while H2 fails,
the improvement came from somewhere else and the explanation in every document is wrong.**

**H3 (yield, the cost of the exclusion).** ≥ 0.25 findings per pull request, lower than design
thirteen's 0.30 bar because removing a file kind that produced 36 of 86 rated findings must cost
yield. **Below 0.25, the filter has bought accuracy by falling silent**, which is not a purchase.

**H4 (what the exclusion cannot fix, stated as a prediction).** The date error is **not** a
training-cutoff artefact and will survive this change. The model called comments dated Aug 14–17
2026 "in the future" on a run dated **Aug 18 2026** — three days in the past, not beyond any
horizon. That is a model with no reliable notion of the present, and CI config is merely where
dates cluster. **Prediction: at least one date-reasoning error appears in the surviving corpus.**
If none does, the diagnosis was wrong and the EXTERNAL class was narrower than claimed.

## What a registry lookup would and would not fix

An arm that resolves tags and commit hashes against the GitHub API was the obvious next design.
**Design thirteen has largely retired it before it was built.** Such an arm answers *does this hash
exist* and *was this tag released* — 20 or so of the 23 EXTERNAL claims. It does not answer *what
is today's date*, and it costs a network call per claim on a class of file this design removes from
scope entirely for free. **The cheap exclusion dominates the expensive lookup.** If H2 fails, the
lookup arm comes back; that is the condition under which it is worth building.

## Power, stated before the numbers exist

At an expected 30–45 unique findings the Wilson half-width is roughly 15 points. **This detects a
large effect and nothing smaller.** A null on H1 is not evidence the exclusion does not help.

## Adjudication

Blind, arm labels held in a sealed key, sabotaged controls (a real quote paired with a claim from a
different pull request) at a known rate. **A rater pool that does not catch the controls is
discarded before its ratings are read.** Design thirteen caught 10 of 10.

**And this design still does not count toward replication** unless the rater did not design it.
Four designs now owe an independent grader.

## What could still silently fail

- Excluding `.github/` removes the file kind that produced 4 of the 11 CORRECT findings in design
  thirteen. If the CORRECT-rate falls with the wrong-rate, the filter is trading signal for noise
  at an unknown exchange rate — H3 is the only thing watching for it, and it watches volume, not
  quality.
- `*.yml` at the repository root is a heuristic, not a file-kind detector. A project that keeps
  application configuration in root YAML loses reviewable surface for a naming reason.
- The conventions arm's apparent 12.6-point gain in design thirteen was **almost entirely the
  UNFALSIFIABLE bucket absorbing claims** — CORRECT rose by 1 while UNFALSIFIABLE rose by 4. If the
  same hedging happens here, the wrong-rate falls without the reviewer becoming more useful, and
  **H1 would pass for a reason nobody should be happy about.** The CORRECT-rate is therefore
  reported beside it every time, never on its own.

---

# AMENDMENT, before any model call: the exclusion trades the wrong way

Recomputing design thirteen's adjudication by file kind AND bucket — not just by wrongness —
inverts this design's premise. It is recorded here rather than quietly fixed, because the original
bars above would have passed while the reviewer got less useful.

**CI config has a HIGHER correct-rate than everything else.**

| slice | n | CORRECT | correct-rate | wrong-rate |
|---|---|---|---|---|
| CI config | 36 | 4 | **11.1%** [4.4, 25.3] | 66.7% |
| everything else | 50 | 3 | **6.0%** [2.1, 16.2] | 42.0% |

**Excluding CI config removes 24 of 45 wrong findings (53%) and 4 of 7 correct ones (57%).** It
takes out a larger share of the correct findings than of the wrong ones, and a larger share of the
correct findings than of the corpus (42%). The intervals overlap, so this is not a significant
reversal — but there is **no evidence the exclusion improves the correct-rate, and the point
estimate goes the wrong way.**

**Off CI config, every arm produced exactly ONE correct finding across 80 pull requests.**

| arm | CORRECT, all files | per PR | CORRECT off-CI | per PR |
|---|---|---|---|---|
| A | 2 | 0.025 | 1 | **0.013** |
| B | 2 | 0.025 | 1 | **0.013** |
| C | 3 | 0.037 | 1 | **0.013** |

**That is one useful comment per 77 pull requests.** Design thirteen's data therefore predicts H1
passes — off-CI pooled wrong-rate is already 42.0%, and arms B and C sit at 38.5% and 28.6% — while
the reviewer produces almost nothing. **H1 passing on its own would be arithmetic on a shrinking
denominator, and this document would report an improvement that no maintainer would feel.**

## Revised bars: the correct-rate is a BAR, not a note

**H0 (new, primary, and it gates every other result).** **Correct findings per pull request ≥ 0.10**
— one useful comment per ten pull requests, against design thirteen's best arm at 0.037 and its
best off-CI arm at 0.013. This metric is chosen because **it cannot be improved by removing wrong
findings.** Excluding a file kind can only lower it.

**H1 is demoted to secondary** and may no longer be reported alone. A pass on H1 with a fail on H0
is written up as **the exclusion working exactly as predicted and not producing a reviewer.**

**H5 (kill condition).** If H0 fails and the correct-per-pull-request figure has not risen above
design thirteen's, **no further path-filter design is warranted.** Filters move the ratio; the
binding constraint is that the model rarely says anything correct. Three filters have now been
tried on this half.

## What this implies about running design 14 at all

Design thirteen's data already predicts most of design 14's outcome, and a fresh six-repository
corpus is a scarce resource — **38 repositories are spent.** Running an exclusion-only design to
confirm arithmetic we can already do is a poor use of one.

**So design 14 should not run as an exclusion-only test.** It runs only paired with a mechanism
that could raise H0 — and the last remaining candidate has now been measured on design thirteen's
own data and does not.

### Multi-review aggregation, retired on measurement rather than argument

**This document previously claimed aggregation "targets the correct-rate rather than the
wrong-rate". That was wrong and is withdrawn.** Aggregation keeps findings that recur across
independent runs. It is a filter: it can only remove. Against a correct-rate of 0.013–0.037 per
pull request, the problem is not that correct findings are diluted by noise — it is that there are
almost none to keep.

Design thirteen's three arms are a **proxy for independent runs** — three configurations over the
same 80 pull requests, matched on `(repo, pr, path, line)`.

| aggregation rule | CORRECT kept | per PR |
|---|---|---|
| union of all three | 5 | 0.062 |
| **single best arm** | **3** | **0.037** |
| keep if in ≥ 2 of 3 | 1 | **0.013** |
| keep only unanimous | 1 | 0.013 |

**Four of the five correct findings were produced by exactly one arm.** Aggregation by recurrence
does not cap the correct-rate at the single-run figure — **it lands below it**, discarding four of
five. And recurrence points the wrong way: **wrong findings recur across arms at 37%, correct
findings at 20%.** An aggregator keeping what repeats preferentially keeps the wrong ones.

**The proxy's limit, stated:** these are three different configurations, not three samples of one.
Different configurations should disagree more than identical ones, so the true effect is milder
than this table. It is not milder enough to matter, and there is a harder blocker below.

**And the reviewer runs at `temperature: 0.0`.** Five runs of one configuration are five identical
outputs. Aggregation requires abandoning determinism first, in a project whose stated principle is
that deterministic beats clever. **The technique is a precision instrument against a recall
problem, it costs the one property we are not willing to trade, and it is retired.**

The TRACE prediction that would have tested it is kept as a record of what was going to be asked:
design thirteen's dominant failure was the model not following code it already had, and
independent runs would likely repeat that error rather than disagree about it.

## The pattern these mechanisms keep showing

Named because it has now happened three times. The ±10-line window converted WRONG into
UNFALSIFIABLE. The conventions file did the same — WRONG −2, UNFALSIFIABLE +4, CORRECT +1. The
decidability gate did it by construction. **Several mechanisms move findings toward "cannot be
decided" rather than toward "correct."** That is honest output and it is worth having, but a
reviewer that reliably says "I cannot tell" is not a reviewer.

## External corroboration, with its caveat

Two published results reported by the reviewer of this work and **not independently verified here**:

- **AACR-Bench** (200 pull requests, 50 projects, 10 languages) reports that context retrieval is
  not universally beneficial and that naive retrieval can degrade strong models — an effect named
  *Contextual Backwardness*. **That is design thirteen's H1/H2 split described from outside**, which
  makes our result less likely to be a local artefact.
- Agent-based methods there show high precision (Claude-4.5-Sonnet 39.90%) with low recall
  (10.10%). **That is arm C's shape**, suggesting the yield failure is a property of gated-agent
  architectures rather than our configuration.

**The caveat belongs beside any citation of it:** AACR-Bench's ground truth is 391 real review
comments augmented with 1,114 LLM-generated ones, verified by senior engineers. Machine-generated
then human-checked is not the same object as a human-authored gold set, and this project does not
quote a number without saying what produced it.
