# Prompt direction: does re-aiming the reviewer, or letting it abstain, move anything?

**Written before the runs. Bars fixed here. A near-miss is a fail.**

## What the forensic pass established, and what it did not

Per-candidate TP/FP labels now exist for all four arms over the same 50 pull requests and the
same 173 golden comments — `research/phase0/bench/results/candidate_labels.json`, produced by
`label_candidates.py`. They did not exist before; four earlier analyses inferred them from
`gap_detail.json`'s `ours_caught`, **which holds golden comments rather than candidates**, so every
candidate tested as unmatched and the resulting splits were arithmetic on a constant. Those four
results are withdrawn.

What the labels show:

| arm | precision | cands/PR | **TP/PR** | FP per TP |
|---|---|---|---|---|
| OURS | 48.5% | 3.9 | **1.9** | 1.1 |
| qodo-extended-v2 | 66.4% | 3.2 | **2.1** | 0.5 |
| greptile-v4-1 | 56.5% | 3.4 | **1.9** | 0.8 |
| coderabbit | 43.1% | 6.5 | **2.8** | 1.3 |

**True positives per pull request are at parity.** We surface as many real defects per pull
request as Qodo does. The precision gap is entirely in what we emit *alongside* them.

And the arms behave differently as volume rises:

| arm | precision on PRs with ≤3 candidates | with ≥6 |
|---|---|---|
| OURS | 46.1% (n=30) | 52.2% (n=11) |
| qodo-extended-v2 | **83.3%** (n=33) | 51.4% (n=5) |
| coderabbit | 66.7% (n=14) | 41.9% (n=23) |

Qodo's few are very good and its many are ordinary. **Ours are the same either way** — which is
what a reviewer that does not modulate looks like. The current prompt already permits an empty
list and caps the count; it is not being taken up.

**NOT ESTABLISHED, and no longer being asked:** whether our false positives land in the wrong
file. The corpus carries no file or line metadata — goldens are free text plus `severity` and
`category` — so the question is unanswerable here, not merely mis-measured.

## The instrument does NOT move on its own — the two code paths count different things

Re-judging identical stored candidates appeared to move CodeRabbit's true positives by **+32 of
318**, and I wrote that down as judge non-determinism. **It is not.** Three replicates of our arm
over identical candidates read **47.9%, 47.4%, 49.5% — a spread of 2.1 points, sd 1.1.** The judge is stable, and the
original label run's 48.5% sits inside that band.

The +32 is a **definition difference between two judging paths in this repository**:

- `run.py:judge_arm()` counts `len(v["tp"])` — **goldens matched**, at most one per golden.
- `label_candidates.py` counts candidates not in `v["fp"]` — **candidates that matched something**.

They diverge by exactly the number of candidates that restate a golden another candidate already
covered. So the apparent noise is a real, measurable quantity, and it is the duplication rate:

| arm | goldens matched | candidates matching | redundant | rate |
|---|---|---|---|---|
| OURS | 79 | 94 | **15** | **16.0%** |
| greptile-v4-1 | 91 | 95 | 4 | 4.2% |
| coderabbit | 105 | 137 | 32 | 23.4% |

**One in six of our correct comments says something a sibling comment already said.** Greptile
does that once in twenty-four. Qodo's published counts point the other way — 106 goldens covered —
but those come from Martian's judge rather than ours and **are not comparable to this table**; a
single-judge pass over all four arms is required before Qodo appears in it, and until then no
claim is made about Qodo's duplication.

**Both metrics are legitimate and they answer different questions.** Golden-level precision asks
what fraction of the defects we named we named correctly; candidate-level asks what fraction of
our comments were worth reading. A reader of a pull request experiences the second. Every number
below is candidate-level and labelled as such.

## Arms

All four generate fresh reviews over the same 50 pull requests, so **generation** variance is
inside the comparison rather than assumed away. Judged by the same judge in the same run.

- **A0 CONTROL** — `PROMPT` exactly as it ships in `bench_reviewer.py` today.
- **A1 ABSTAIN** — control plus a stated expectation that most pull requests deserve none or one
  comment, and an instruction to emit only what the reviewer would defend in review.
- **A2 AIM** — control re-aimed at functional defects, which are **54.3% of goldens** (`bug`),
  against the breadth the current prompt lists. Our exclusive catches skew to `security`, which is
  6.4% of goldens.
- **A3 BOTH** — A1 and A2 together.

## Bars

Precision alone cannot decide this: **precision rises whatever you delete.** So an arm passes only
by dominating the control on the pair.

- **PASS** — TP/PR is not below control's by more than 0.2, **and** candidate-level precision
  rises by more than **2.1 points** — the full measured replicate spread, not its standard
  deviation. (Written first as 1.1, which was the sd; the conservative figure is the spread.)
- **INCONCLUSIVE** — the change is inside the 2.1-point spread. This is the expected outcome and is not a
  failure of the experiment.
- **FAIL** — TP/PR falls by more than 0.2, whatever precision does.

Four prompt levers have already moved nothing on this corpus: anchor repair, structured context, a
rejection filter, and hunk expansion. **The prior here is that prompts do not move it.** This
experiment is worth running because it tests a different quantity from those four — not what the
model is told to look at, but how many things it is told it is allowed to say.

## What could still silently fail

The judge scores a candidate against golden text without seeing the diff, so a candidate that is
correct about a real defect the goldens do not record scores as a false positive. That penalty
falls on every arm equally and cannot explain a difference **between** arms — but it does mean no
arm's absolute precision here is that arm's precision in the field.

---

# RESULT — all three arms FAIL. Recorded after the run; nothing above was edited.

| arm | candidates | precision | TP/PR | FP/TP | verdict |
|---|---|---|---|---|---|
| A0_CONTROL | 238 | 45.4% | 2.16 | 1.20 | — |
| A1_ABSTAIN | 59 | 50.8% (+5.4) | **0.61 (−1.55)** | 0.97 | **FAIL** |
| A2_AIM | 185 | 47.6% (+2.2) | **1.76 (−0.40)** | 1.10 | **FAIL** |
| A3_BOTH | 66 | 50.0% (+4.6) | **0.67 (−1.49)** | 1.00 | **FAIL** |

The bar allowed TP/PR to fall by 0.2. Every arm fell by more, and A2's precision gain of 2.2
points sits on the 2.1-point noise floor — a near-miss, which is a fail.

## Why it failed, which is the finding

Precision rises whatever you delete, so the arms were scored on what the deletion cost. Given the
control's 108 true positives in 238 candidates, an arm that cuts to N has a floor (the cut carried
no information, 45.4%) and a ceiling (it deleted only wrong findings):

| arm | kept | blind cut | perfect cut | observed | **discrimination retained** |
|---|---|---|---|---|---|
| A1_ABSTAIN | 59 | 45.4% | 100.0% | 50.8% | **10.0%** |
| A2_AIM | 185 | 45.4% | 58.4% | 47.6% | **16.8%** |
| A3_BOTH | 66 | 45.4% | 100.0% | 50.0% | **8.5%** |

**Asked to keep only what it would defend, the model threw away three-quarters of its findings and
closed 10% of the distance to a perfect cut.** It is very nearly blind to which of its own findings
are wrong. A1 deleted 179 candidates; had it been choosing well, nearly all 130 false positives
were available to delete and it would have finished near 100%. It finished at 50.8%.

This is the measured case for the isolated judge, and it was previously only asserted. **A prompt
can ask the model to exercise judgement it does not have; it cannot supply the judgement.** That is
why the lever has to sit outside the generator.

**Five prompt levers have now moved nothing on this corpus** — anchor repair, structured context, a
rejection filter, hunk expansion, and these three. The direction of the ask is not what is wrong.

## What is left, and it is not a prompt

True positives per pull request are at parity with Qodo (2.16 against 2.1). We find the defects.
The two mechanisms with measured evidence behind them are the isolated judge, which sits where the
discrimination is missing, and **redundancy** — one in six of our correct comments restates a
golden a sibling comment already covered, against Greptile's one in twenty-four. Redundancy is a
deduplication problem, is model-free, and does not require the generator to know anything it has
just been shown it does not know.

## Redundancy, all four arms on ONE judge

The earlier version of this table put our judge's count beside Martian's published one for Qodo.
That is two instruments in one column and it is withdrawn. `redundancy.py` scores every arm in a
single pass:

| arm | comments emitted | that matched something | goldens covered | **redundant** | rate |
|---|---|---|---|---|---|
| qodo-extended-v2 | 152 | 99 | **98** | **+1** | **1.0%** |
| greptile-v4-1 | 168 | 93 | 86 | +7 | 7.5% |
| **OURS** | **194** | **98** | **81** | **+17** | **17.3%** |
| coderabbit | 318 | 140 | 106 | +34 | 24.3% |

**Qodo covers 98 defects with 152 comments and repeats itself once. We cover 81 with 194 and repeat
ourselves seventeen times.** The rate orders the four arms exactly as their published quality does.

Our 98 matching comments and Qodo's 99 are the same number. **They are not the same coverage** —
theirs land on 98 distinct defects, ours on 81.

### What deduplication is worth, stated before building it

Golden-level precision is covered ÷ emitted. Removing all 17 redundant comments and changing
nothing else:

- ours today: 81/194 = **41.8%**
- ours deduplicated: 81/177 = **45.8%**  (+4.0 points, above the 2.1-point noise floor)
- qodo: 98/152 = **64.5%**

**Deduplication closes 4.0 of the 22.7-point gap — 18% of it.** The other 18.7 points is that Qodo
emits 53 comments that match nothing where we emit 96. Closing that means deleting about 43 more
wrong comments, and A1 established the generator cannot pick which 43. That residue is the judge's
work, not the prompt's.

**Recorded, not built** — the fourth such fix, and for the same reason as the other three. It moves
a benchmark ratio without creating a correct finding, and the reviewer half is closed on 0 of 45
and a 37-point miss, neither of which a ratio touches.
→ `docs/product/reviewer/recorded-not-built.md`
