# Published-finding correctness, measured — 25.0%

**Labelled 2026-08-29 by a human against `research/phase0/data/labelling/findings_pack.md`
(24 items, seed 20260828). Scored by `phase0.findings.scoring`.**

A6 reported 0.686 findings published per change and said the error rate behind it *"has NOT been
re-measured on this pipeline"*. This is that measurement.

## The result

| | | |
|---|---|---|
| TRUE | 6 | |
| FALSE | 11 | |
| UNKNOWN | 7 | |
| **correct over all items** | **6/24 = 25.0%** | 95% 12.0–44.9% |
| correct over decided items | 6/17 = 35.3% | 95% 17.3–58.7% |

**Every one of the 24 verdicts cited a deciding line present in that item's own diff.** That is
the admissibility check that replaced the planted control arm, and it passed 24 of 24.

## What it means: the gate is not buying correctness

Raw findings measured **66.7–82.1% wrong** across four blind pools — that is **17.9–33.3%
correct**. Published findings here are **25.0% correct, interval 12.0–44.9%**.

**The published interval contains the whole raw band.** There is no evidence that anything
between the model and the comment raises correctness. That is exactly what
`docs/findings/oracles/WHY_THE_ORACLES_NEVER_FIRE_2026-08.md` predicted: on source-code findings
the gate is the anchor check and nothing else, the refutation oracles are structurally
unreachable, and across 65 changes they dropped one finding — which was probably an unresolvable
mislabelled as a refutation.

**So "published" and "raw" are, on this evidence, the same population minus the ones whose quote
was not in the diff.**

## Correct findings per change

At the replicated rate of 0.686–0.733 published per change, 25.0% correct gives **0.17–0.18
correct findings per change**, interval 0.08–0.33.

`AGENTS.md` records the historical figure as **0.013–0.037 correct per pull request**. This is an
order of magnitude higher, and the comparison should be made carefully rather than claimed: that
figure came from different corpora and a different pipeline, and 24 items on one repository is a
first measurement, not a replication.

## The seven UNKNOWNs are a finding, not a gap

**29% of published findings could not be judged from the diff the reviewer was shown.** The
labeller's reasons name what was missing: werkzeug's multipart semantics, whether `send_file`
accepts bare bytes, where `default_config` is defined, whether `Blueprint` initialises `cli`.

That is an argument about **what the reviewer is given**, and it is measured rather than assumed.
A finding the reader cannot check from the same context the model had is not a finding they can
act on. It also vindicates making UNKNOWN a first-class verdict: forced into TRUE/FALSE, an
isolated judge produced confident FALSEs on recalled facts, one of them verifiably backwards.

## The isolated judge was too harsh, and now we know by how much

Run over a comparable draw from the same 38 harvested findings, an isolated different-family
judge returned **FALSE on all 24 items**. A human on this draw returns TRUE on 6. **The judge's
0% was not a measurement of the findings; it was a property of the judge**, which is why that run
was retracted rather than reported. This is the first calibration of a machine judge against a
human rater on this pipeline, and the direction is over-rejection.

## A protocol conflict, recorded because it shaped the labels

Mid-session I told the labeller to *"cross-reference with the internet if required"*. That
instruction was about the judge run; the pack says *judge from the diff shown and nothing else*.
**The labeller followed the pack and flagged the conflict**, on the grounds that searching would
make these labels incomparable with any rater who obeyed the sheet. That is the correct
resolution and it is recorded here rather than left in a transcript. Several UNKNOWNs would
likely resolve with a werkzeug source read — **that is a different instrument and would answer a
different question**.

## What this does not say

**One repository, one language, 24 items, unstratified**, drawn from consecutive recent commits
on `pallets/flask`. The ranking half's own claim required six repositories the method had never
seen and n = 2,400. This is a first measurement of a quantity that had none.

**It does not say the model cannot review code.** It says that on this corpus, with this prompt,
after this gate, one published finding in four was judged correct by one careful reader.

**One rater.** The hand-labelling protocol requires a second before a number like this is leaned
on, and `adjudication-preregistration.md` says the same: *"A second rater is required before any
of this is published."*
