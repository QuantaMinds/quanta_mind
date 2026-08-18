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

Six repositories, each checked with `scripts/guard/check_burned_corpora.py --check owner/name` and
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
