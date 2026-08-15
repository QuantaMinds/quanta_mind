# Pre-registration — the properly powered human-attention rerun

**Written while the run is executing and before any count exists.** The first version of this test
returned a null on an instrument that could not have detected an effect: admitting pull requests
with four changed files put exact chance at 79.7%, and top-3 of 4 is not a test. This rerun fixes
that. It is also now **load-bearing in a way the first one was not** — it tests the half of the
product that survived the adjudication, so the reading has to be fixed before the number arrives.

## What changed from the first run

| | first run | rerun |
|---|---|---|
| repositories | the same 8 convenience clones | **6 fresh**: scikit-learn, pandas, django, ansible, scrapy, celery |
| changed `.py` files per PR | 4–15 (chance 69.1%) | **9–30** (chance ≈ 52%) |
| pages scanned | 6 | 10 |
| read failures | fatal after one attempt | **retried on 5xx, still fatal if persistent** |

**The retry is not leniency.** A 502 is not a result. What must stay fatal is a read that keeps
failing, because a dropped repository silently shrinks the denominator and reads as a smaller
sample rather than as an error — the truncated-history defect, anticipated instead of
rediscovered.

## The measurement

For each merged pre-2022 pull request carrying a human inline review comment on a `.py` file: rank
the changed files by how many commits touched them in the year before the PR, take the top three,
and ask whether a file a human chose to comment on is among them. Scored against **an alphabetical
control at the same budget** and against **exact hypergeometric chance**, computed rather than
simulated.

Pre-2022 because it predates AI reviewers, and 31.5% of this corpus is bot-written — without the
cut, the test compares us to a competitor rather than to a human.

## The readings, fixed now

Let **H** be the history top-3 hit rate, **A** the alphabetical control, **X** exact chance.

| reading | rule | what it means |
|---|---|---|
| **CONFIRMS the ranking half** | H − X ≥ 10 points **and** McNemar p < 0.05 against the control | The ranker points where expert attention went, on fresh repositories, on a selective instrument |
| **NULL** | H − X < 5 points, or the control matches within 2 points | The ranker does not predict human review attention on a test that could have detected it |
| **INCONCLUSIVE** | anything between, or n < 40 | Say so. Do not round toward either |

## The mixed case — written because it is the one that gets rationalised

The bands above are **pooled**, and a pooled figure can hide the exact failure this rerun exists to
detect. **A pooled positive driven by one repository is not external validity — it is the
eight-repository artifact happening again on different repositories.** So consistency across repos
is the real test and the pooled p-value is not.

**Primary analysis: pooled, against the bands above. Consistency guard, binding on top of it:**

| condition | reading |
|---|---|
| pooled clears CONFIRM **and** ≥ 4 of 6 repositories individually show H > X | **CONFIRMED.** The effect travels |
| pooled clears CONFIRM **but** ≤ 3 of 6 repositories are individually positive | **INCONCLUSIVE, not confirmed.** A pooled win carried by one or two repos is the artifact, not the refutation of it |
| pooled is null **and** repositories are split in direction | **NULL.** A split with no pooled effect is noise, and calling the positive half a signal is choosing a subgroup after the fact |
| repositories disagree sharply in *magnitude* while agreeing in direction | Report the **range across repositories**, and quote the range rather than the mean |

**A sign test across the six repositories is reported alongside the pooled McNemar**, and where the
two disagree, **the sign test wins**, because it is the one measuring whether the effect is a
property of ranking rather than of a particular codebase.

**Per-repository n will be small — probably 10–25 events each — and no single repository's result
is interpretable on its own.** They are counted, not individually tested. The count is the
instrument; the individual repository is not.

**And the subgroup rule, stated before any subgroup exists:** no repository may be excluded after
the fact for any reason other than a *read failure recorded in the skip ledger*. Dropping a
repository because it disagrees is the move this entire pre-registration exists to prevent.

## What a NULL would mean — decided before it can be argued about

**It would not overturn the retrospective results.** Those target *the function a later fix returns
to*. This targets *the file a human commented on*. Different quantities, and the corpus work
already gives a reason they need not coincide: only **5.9%** of human review comments assert
anything structurally checkable, so where reviewers comment is mostly not where defects live.

**But it would remove a claim the pitch currently leans on**, and that is the part worth fixing in
advance. "We allocate attention the way a good reviewer would" is not the same claim as "we point
at the function a later fix returns to", and only the second is measured. **On a null, the first
sentence comes out of every document** and the product's claim narrows to defect-return, which is
what the evidence actually reaches.

**It would also weaken, without killing, the "quiet" argument.** Firing on 10–12% of changes is
only a virtue if the 10–12% is the right 10–12%. A null here does not show it is the wrong one; it
shows one instrument could not confirm it is the right one, and the honest description becomes
"quiet, and validated against later fixes rather than against reviewers."

**A null would also mean the ranking is, on the evidence, a property of eight repositories rather
than of ranking.** What survives that is narrower and worth naming now so it is not assembled in a
hurry afterwards: **the corrected attribution rule** — 67.9% of file-overlap verdicts blame a
change sharing no symbol with the fix, reproduced across three corpora, **and independent of the
ranker entirely** — and **typed coverage**, which is a construction rather than a measurement. That
is a real thing to sell and it is a smaller company than the one currently written down.

**And a null would put the measurement-layer company on a narrower base than yesterday** — three
measured pillars, one of which (attribution) is the strongest and least contested. That is still a
business. It is a smaller claim than the one currently written down, and the documents would need
to say so.

## What a CONFIRM would mean

That the ranking half replicates on **fresh repositories** — the first result outside the eight
that have now carried six variants, a holdout, a corpus study and a cost run. That is worth more
than its effect size, because external validity is the thing every number in this project has been
short of.

**It would not resurrect the review half.** Knowing where to look and being right about what you
see are separate, and the second was measured at 4.5% correct by consensus.

## Stated in advance so it cannot be claimed afterwards

**A result that lands between the bands is inconclusive and will be reported as inconclusive**,
not as "directionally positive". The first version of this test was reported as a null with its
instrument criticised in the same breath; that was only credible because the criticism was made
against my own result. The same standard applies here in whichever direction it falls.


---

# RESULT — 2026-08-14. **NULL.**

| | |
|---|---|
| n | **44** pull requests (above the n < 40 inconclusive floor, barely) |
| history top-3 | **40.9%**, Wilson [27.7%, 55.6%] |
| alphabetical control | **50.0%** |
| exact chance | **36.6%** |
| **H − X** | **+4.3 points** — the pre-registered quantity |
| **H − A** | **−9.1 points** |
| McNemar vs control | b = 7, c = 11, **p = 0.48** |

**Against the bands fixed in advance: NULL.** The rule was *"NULL if H − X < 5 points"*. It is 4.3.
CONFIRM needed ≥ 10 points and p < 0.05 and got neither.

**And the direction is worse than a null.** History did not merely fail to beat the alphabetical
control — it **lost to it by 9.1 points**. Not significant at n = 44, and it must not be reported
as if it were. But an informed policy losing to alphabetical ordering is not the shape of a weak
effect; it is the shape of no effect plus noise.

## Per repository, and the consistency guard

| repo | n | history | chance | H − X | alphabetical |
|---|---|---|---|---|---|
| pandas | 15 | 53.3% | 42.9% | **+10.4** | 60.0% |
| scikit-learn | 14 | 28.6% | 34.5% | −5.9 | 28.6% |
| ansible | 6 | 16.7% | 24.1% | −7.4 | 66.7% |
| scrapy | 6 | 33.3% | 32.1% | +1.2 | 33.3% |
| celery | 3 | 100.0% | 49.3% | +50.7 | 100.0% |

**3 of 5 positive, sign test p = 1.00.** The guard required ≥ 4 of 6 for CONFIRMED and the pooled
reading is null regardless. **celery's +50.7 points is three events and means nothing** — it is
listed because the pre-registration forbids dropping a repository that disagrees, and the same rule
forbids promoting one that agrees.

**It is five repositories, not six. Django contributed zero of its 114 candidate pull requests** —
not a read failure, which would have refused to report, but its historical patch-and-Trac workflow
means most Django PRs were never merged *through GitHub*. "Not merged" is the largest skip bucket
at 373. **Recorded because a repository that silently contributes nothing is exactly the
denominator defect this harness was hardened against**, and here it is visible rather than assumed.

## The cross-run observation, which is more informative than either run

**This is the second null on human attention, and history lost to alphabetical both times, on
disjoint repository sets.**

| | history | alphabetical | gap |
|---|---|---|---|
| first run — 8 original repos, n = 69 | 69.6% | 72.5% | **−2.9** |
| this run — 5 fresh repos, n = 44 | 40.9% | 50.0% | **−9.1** |

Neither gap is individually significant. **Two independent samples pointing the same way is worth
more than either**, and the way they point is: the history ranker does not predict where human
reviewers look, and an alphabetical ordering does at least as well.

## What this does and does not establish

**It does NOT show the ranker fails at what it was built for.** The +22-point result targets *the
function a later fix returns to*. This targets *the file a human commented on*. On the original
eight repositories the ranker **does** beat alphabetical at defect-return — 1.44% miss against a
3.31% control across 1,969 events.

**What it establishes is the precise gap, and it is the important sentence in this document:**

> **The ranker has been shown to beat an alphabetical control at defect-return on eight
> repositories, and at nothing on any repository outside them.** Every out-of-sample test it has
> faced — two of them now — has returned a null against the same trivial control.

**So the open question is no longer "does the ranker predict human attention".** It is
**"does the ranker beat alphabetical at DEFECT-RETURN on repositories it was not developed on"** —
and that has never been run. It is the single most important untested claim the company has, it
needs full-object clones rather than the GitHub API, and it should be pre-registered before it is
attempted.

## Consequences, applied as pre-registered rather than argued now

- **"We allocate attention the way a good reviewer would" comes out of every document.** It was
  never measured and it has now failed twice.
- **The claim narrows to defect-return**, which is what the evidence reaches, and which is itself
  unreplicated outside eight repositories.
- **"Quiet" becomes "quiet, and validated against later fixes rather than against reviewers."**
- **What is independent of all of this and survives untouched: the corrected attribution rule** —
  67.9% of file-overlap verdicts blame a change sharing no symbol with the fix, reproduced across
  three corpora, **and computed without the ranker** — **and typed coverage**, which is a
  construction rather than a measurement.
