# Allocation and gate 3c — the measurement record

**Moved out of `docs/plans/implementation.md` unchanged.** It is a record of what was measured,
pre-registered and rejected while deciding the ranker's unit and budget — not a build instruction,
and it was making the build plan unreadable as a plan.

**Nothing here has been edited.** The pre-registrations, the two tuned-on-noise diagnoses, the
matched-coverage re-run and the variants that failed are the evidence the budget decision rests on,
and a record edited to read better is not a record.

**`gate 3c` is defined here**, and `research/phase0/allocation_variants.py`,
`research/phase0/extraction_completeness.py` and `research/phase0/gate3c_paired.py` name this
document as their consumer.

---

### How gate 3c gets measured, given the clones we have

**Not as an absolute rate on a reduced population.** 27 of 35 clones are `blob:none`, and
symbol extraction needs patch bodies. Running only on the 8 complete clones cuts events roughly
proportionally, and a ~2% rate on a few hundred events carries an interval whose upper bound is
several times its point estimate — the run would be spent and still not distinguish one missed
change a month from six. **Worse, those 8 are not a random subsample**: they are the clones
already completed for symbol-level work, selected for reasons correlated with the analysis.

**Measure the paired difference instead.** The load-bearing question is not the absolute rate —
it is whether function-level allocation loses *more* than the file-level analogue. That is a
paired comparison on identical events: same pull requests, same defects, file-top-3 against
function-top-3, **McNemar on the discordant pairs**. Only events where the two rankers disagree
carry information, and a paired design is far more powerful than two independent proportions, so
8 repositories can plausibly establish sign and rough magnitude even where they cannot pin a
rate.

### Does a gap measured on those 8 travel? The free check, run first

**The 8 are a convenience sample and the selection is confirmed, not assumed.** All four
repositories used for the earlier symbol-level work — Skyvern, browser-use, cartography, opendbc
— are in the full-object set. They have complete objects *because* someone previously wanted
patch content from them.

So before any fetch, compare the 8 against the other 17 on everything `--name-only` measures
identically in both. **This cannot prove transfer** — the mechanism driving file-versus-function
divergence is within-file variance in touch counts, invisible without blobs — **but it can
falsify it for free, and a check that only fails one way is worth running first.**

| | repos | events | ≥4-file miss rate (95% CI) | share of events touching ≥4 files |
|---|---|---|---|---|
| **Full-object** | 8 | 2,630 | 54/1,131 = **4.77%** (3.7–6.2%) | **43.0%** |
| **Partial** | 17 | 4,863 | 79/1,762 = **4.48%** (3.6–5.6%) | **36.2%** |

**Transfer is not falsified.** The miss rates are within 0.3 points with heavily overlapping
intervals, and per repository the 8 sit spread through the distribution of the 17 rather than
clustered — from 0.65% (Skyvern) to 10.48% (opendbc), inside a partial range running 0.00% to
14.57%.

**One systematic difference, and its direction is knowable — but name the mechanism, not the
correlate.** The 8 carry larger changes: 43.0% of their events touch four or more files against
36.2% for the partials.

**Change size raises the miss rate on BOTH arms**, because a larger change holds more files *and*
more functions, so top-3 files also covers proportionally less of it. For a paired comparison
what matters is not that size hurts each side — it is whether size hurts the **function** side
faster. **The claim carrying the direction is that functions-per-change grows faster than
files-per-change**, so the function partition inflates faster as changes grow.

That is an additional claim, not a restatement, and it is what the direction rests on. **Stated
properly: a gap measured on the 8 likely overstates, because functions-per-change grows faster
than files-per-change** — not merely because the changes are bigger.

**That partial test has been run**, binning the file-level events by files touched. The file arm
is steep:

| files touched | 2–3 | 4 | 5 | 6 | 7 | 8 | 9 | 10–12 |
|---|---|---|---|---|---|---|---|---|
| events | 4,600 | 899 | 609 | 401 | 280 | 197 | 161 | 346 |
| miss rate | 0% *(by construction)* | 2.22% | 3.28% | 4.24% | 6.43% | 7.11% | **11.18%** | 7.51% |

**Miss rate rises roughly linearly in the number of UNCOVERED files** — about 1.4 to 2.2 points
per file beyond the three the budget funds, near-flat across the range. So the file arm is
already steep, and the ratio argument needs the care that steepness implies: it survives only
because the *function* arm's uncovered count grows faster than the file arm's with change size,
which is the functions-per-change claim above and not something these bins establish.

**The reversal at the top bin was tested, not left as a hypothesis.** A mechanical sweep — a
lockfile bump, generated code, a mass rename — touches many files uniformly, so its prior-touch
counts should be **flat across the change**: low variance. Composition would show as an unusually
low coefficient of variation in that bin.

| files touched | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10–12 |
|---|---|---|---|---|---|---|---|---|---|
| median CV of prior-touch counts | 0.529 | 0.707 | 0.773 | 0.849 | 0.908 | 0.972 | 0.993 | 0.961 | **1.016** |

**It is the opposite.** The 10–12 bin has the *highest* dispersion of any bin, not the lowest, so
it is not sweeps. **The reversal is noise, and the intervals say so**: k=9 is 11.18% (95% CI
7.2–17.0%), the 10–12 bin is 7.51% (5.2–10.8%), and they overlap across a wide range. **Two
independent lines agreeing on noise is stronger than either alone.** Reported rather than
smoothed.

**The residual this discriminator cannot see, named rather than run.** A change touching files
that are individually hot *and* similarly hot passes the dispersion check. Those two conditions
together describe something specific — a cross-cutting refactor of comparably active core modules
— and **if that pattern is real it is not an artefact to filter out. It is a change type where
the ranker has no signal, because every unit looks the same.** The test, for whenever it is worth
running: within the top bin, split by coefficient of variation and compare miss rates. **If the
flat-and-hot changes miss more, that is a case the allocator handles badly**, which is worth more
than a cleaner histogram. And the harness raised on
serialisation after printing this table; the bins sum to **7,493, matching the known total
exactly**, which is what establishes the computation completed before the crash.

**What makes that assertion work is that 7,493 is independently known** — it comes from a prior
run, not from this one. **Bins summing to each other would prove nothing.** That is the
difference between this check and the dead hotspot check that returned clean zeros at every
threshold: one compares against an outside quantity, the other was internally consistent and
wrong.

**Two miss rates now live in this document on different populations, and they must be labelled
everywhere they appear:** **4.77% and 4.48% are ≥4-file rates**, and **1.77% is pooled across all
changes**. An unlabelled 4.6% beside an unlabelled 1.8% is the next `$15`.

### The random draw is the second step, not a contingency

**The free check cannot rule out a mechanism-level difference, by construction.** File and
function rankings diverge exactly when a file's touch total is concentrated in one function
rather than spread across many. Two repositories can match on events, change size, velocity and
file-level accuracy while differing entirely on whether their hot files are hot because of one
function or ten. **That is within-file touch variance, it is invisible without blobs, and blobs
are the thing the other 27 do not have.**

So the free check ruled out gross non-representativeness and nothing more. **The random draw is
promoted from fallback to planned second step**, because it is the only thing that tests transfer
at all.

**Draw 5 of the 27 at random, and pre-specify the draw now, while the answer is still
unobservable.** Fetch blobs for their event sets only and run the same paired comparison — not to
pin the gap there, but to check the sign and rough magnitude hold outside the set that selected
itself.

**And say the scope in the same sentence as the result**: *measured on 8, checked against 17 on
shared metrics, not established on the remaining 22.* 13 of 35 is not 35, and the transfer claim
stays an inference.

### Pre-specified decomposition — write this down before the numbers exist

The near-flat normalisation above is not just a slope, it is a **model**: misses ≈ `c·(k−3)`
with `c` about 1.4–2.2 points per uncovered file. If the function arm follows the same form with
its own uncovered count, misses ≈ `c′·(m−3)` where `m` is functions per change, and **the
expected gap is `c′(m−3) − c(k−3)`.**

`c′` and `m` are unobservable without blobs — **and both are measurable on the 8 once the run
happens.** So 3c reports the **constant**, not only the gap.

**That reframes the transfer question into a much narrower one.** If `c′ ≈ c`, the entire
difference between the arms reduces to the unit-count ratio `m/k`, and what has to generalise is
no longer "the gap" but **"is functions-per-file stable across repositories"** — which the
random-5 draw can actually answer, where it could never have answered the broader question.

**This decomposition is pre-specified here, before the numbers exist**, because added afterwards
it is indistinguishable from post-hoc fitting.

**Two caveats that travel with the model, not footnotes to it.** Linearity is fitted over k = 4
to 9 and the top bin reverses. And `c` is estimated on the 8 clones, which carry larger changes
than the 27 — **so `c` is measured where the arm is steepest.** Neither breaks the decomposition;
both belong beside it.

**Pre-specify the discordance criterion before the run, in writing.** McNemar counts only the
events where the two rankers disagree, so that definition *is* the test: a discordant pair is one
where the defect unit is inside file-top-3 and outside function-top-3, or the reverse. **Deciding
what counts after seeing the counts is how a null becomes a finding.**

**Both discordant cells are live, and an earlier version of this section assumed one was
empty.** It reasoned that a file-level miss implies a function-level miss — if the defect's file
is outside the top three files, its function is outside the top three functions. **That is
false, and this document measures why.**

A file's touch count is roughly a *sum* over its functions; a function's is its own. A file of
eight functions at five touches each scores 40; a file holding one function at 34 and two at 1
scores 36. File ranking puts the first above the second, function ranking puts that 34-touch
function above all eight of the first file's. **Defect in the hot function of the lower-ranked
file: file misses, function hits.** That is the supposedly empty cell, and it is not an edge case
— it is the measured reason ranking is global rather than file-then-function.

**So the discordant count is (file hit & function miss) + (file miss & function hit), both
populated**, which means power is probably *better* than the earlier estimate rather than worse.
That estimate erred in our own favour, which is the direction nothing catches.

**Across the 8 complete clones: 2,630 events, 54 file-level misses, 2.05%, Wilson 95% interval
1.6%–2.7%.** Discordance is bounded below by the difference between the two miss counts and above
by their sum, and with both cells live the tens rather than single digits remain the expectation.

**The sign is not predictable either.** Function-level wins where a hot function sits in a cold
file and loses where a cold function sits in a hot file, and which dominates is the whole reason
to run the test. **Pre-specify both cells as live**; a criterion written expecting one to be
empty pre-registers the wrong test.

If it does come back with single-digit discordance, the honest output is **"sign unresolved"**,
not a magnitude — and the document still improves, because *"floor of 1.77%, function-level gap
measured but not resolved on 8 repositories"* is truer than what it says today.

The sentence a powered run produces is the one the master document needs: *function-level top-3 misses N
points more than file-level, measured on 8 repositories; the pooled file figure of 1.77% is
therefore a floor and the function-level rate is approximately X%.* **A floor plus a measured gap
beats a wide absolute estimate.**

**Do not unfilter 27 repositories wholesale.** Blobs are needed for the commits in the event set
— base and head pairs, and the fix commits — not for all history. Fetching those objects
specifically is a much smaller job than removing the filter. Whether git scopes that cleanly on
a promisor clone is worth an hour of investigation before committing to a large download.

**And assert twice, because this is the exact operation that failed before.** `git log -p` exits
non-zero on a blob-filtered clone and emits a partial patch stream: identical invocations
returned 710 and 918 commits against 3,313. So assert the exit code, **and assert the unit count
changed** — if symbol extraction returns the same event count as `--name-only` did, the parser
did not run.

### Gate 3c — RUN, and re-run after the extraction defect it exposed

**Result, 8 full-object clones, 1,969 paired events.**

| arm | top-3 miss | 95% CI |
|---|---|---|
| file-level | 24/1,969 = **1.22%** | 0.82–1.81% |
| function-level | 174/1,969 = **8.84%** | 7.66–10.17% |
| **gap** | **+7.62 points** | |

**McNemar exact two-sided p < 0.0001.** Both discordant cells populated as pre-specified:
b = 157 (file hit, function miss), **c = 7 (file miss, function hit)** — the cell an earlier
version of this section assumed empty. **The sign is settled: function-level allocation loses
substantially more.**

### Pre-specified before running: the matched-coverage test

**Top-3 files and top-3 functions are not the same net.** With m/k = 1.64, three functions is
about 1.8 files' worth of units — **the function arm runs at roughly half the coverage of the
file arm.** A smaller net catching less is not a ranking-quality finding.

And it sits against a measurement pointing the other way: global function ranking scores **75.0%
top-1 against 58.9%** for any-function-in-the-top-file. Function *ordering* is better. This run
says function *allocation* is worse. Both can hold, and the reconciliation is budget — better
ordering, smaller net, net wins.

**The rule, fixed before the run:** function budget = `round(3 × m/k)` on the measured ratio.
With m/k = 1.64 that is **round(4.92) = 5**. So **top-3 files against top-5 functions**, which is
5/1.64 ≈ 3.05 file-equivalents.

**What each outcome means, also fixed now:**

| Outcome at matched coverage | Reading |
|---|---|
| functions still lose | **granularity is genuinely worse** — a real finding about the unit |
| functions win or draw | **the ranking is better and the BUDGET is what costs us** — a different problem with a different fix |

### The budget is re-decided against these numbers: it stays at three, and the cold list is why

The plan fixed ranks 1–3 before any of this was measured. It should not be inherited, so here is
the decision made against the data.

| budget | miss | changes/month at 200 PRs | cost/PR | cost/repo/month |
|---|---|---|---|---|
| **top-3** | 8.84% | ~18 | $0.140 | **$28** |
| top-5 | 3.50% | ~7 | $0.205 | **$41** |

Halving the miss costs about **+$13 per repository per month**, and at 20 developers across 4
repositories that moves gross margin from roughly 70% to 57% on a $19 seat. Defensible on its
own terms.

**It stays at three, because the cold list is the cheaper fix for the same problem.**

The cost of a cold miss is not the miss. It is that **nobody knew** — the defect sat in a unit
no one was told went unread. **Naming the eight skipped functions costs nothing and removes
exactly that**, where reading two more of them costs 50% more inference and still leaves six
unnamed.

So: **top-3, with every cold unit named in the coverage line.** Revisit only if the field shows
a named cold list is insufficient — which is a question about whether reviewers act on it, and
therefore folds into the shadow-mode month rather than needing its own experiment.

**And this is why every changed unit gets a `ranked_unit` row, cold ones included.** The schema
allows `allocation = cold`; it must be *required* rather than permitted. Dropping cold units at
allocation time would take the coverage line's content away, and it would also blind shadow
evaluation — a candidate ranker that would have chosen a cold unit needs that unit to exist in
the record to be credited for it.

### Pre-specified before running: the hybrid, and what it is not

**The buried result in the matched-coverage run is that FILES WON.** Top-3 files reads about 4.9
function-equivalents and misses 1.22%; top-5 functions reads 5 and misses 3.50%. **Read the same
amount of code either way and file-level allocation misses less than half as often.**

That sits against `QUANTAMIND.md` "The ranking itself", where global function ranking scores 75.0% top-1 against 58.9% for
any-function-in-the-top-file. **Functions order better. Files cover better.**

**The likely mechanism is locality, and it is already measured** in `QUANTAMIND.md` "Signals tested and rejected": 5 of 11 SELF, 6 of 11 MIXED,
**0 of 11 COMPANION** — every breakage required re-editing a file the change had already touched.
Defects cluster inside files. A file is a bundle, so reading one captures the target *and its
neighbours*; reading a function captures the target only, and pointing one function off yields
nothing.

**So the hybrid worth testing is not a union.** A union of top-3 files and top-3 functions would
miss only d = 17 events = 0.86% — but that is ~8 function-equivalents of budget against 5, which
is the same confound the matched-coverage run just removed. **The union's real ceiling is the c
cell: 7 events, 0.36 points.**

**The hybrid is: rank by function, allocate by file.** Use the global function ranking to choose
the target — the part functions are better at — then read the *enclosing file* rather than the
function alone — the part files are better at.

**This is not the nested strategy that scored 54.2%.** That ranked the top file *first* and then
picked a function inside it, discarding better candidates elsewhere in the diff. **This is the
inverse: rank globally across all functions, then expand.** Nothing measured argues against it.

**The expansion rule, fixed now:**

| | Rule |
|---|---|
| **Expansion** | the enclosing file of each of the top-N ranked functions, deduplicated |
| **Hit** | the expanded file set intersects the file-level target set |
| **Budgets reported** | N = 1, 2, 3, so the cost is visible rather than hidden |
| **The comparison that decides it** | **N = 3 expanded against top-3 files** — same file count, same rough token cost. Does function ordering pick better files than file ranking does? |

**And a cheaper variant in the same run:** expand to the *changed hunks* in that file rather than
the whole file, which captures most of the locality at a fraction of the input tokens.

**On cost, the objection is weaker than it looks.** In the illustrative table, output including
thinking is $0.050 of $0.075 and input on the ranked unit is $0.015. Tripling the input is
$0.030, not a doubling of the bill.

### Pre-specified: the changed-hunks variant uses a different target, and that is the trap

**Reading the changed hunks of a file is not reading the file.** So the hit criterion changes
with it, and getting this wrong would make the variant look better than it is by comparing it
against an easier target.

| variant | what is read | correct target |
|---|---|---|
| top-N functions | N symbols | **symbol** target — did the fix return to one of them |
| top-N → changed hunks in their files | every changed symbol in those files | **symbol** target |
| top-N → whole files | the files entire | **file** target |

**So the hunks variant is compared against the FUNCTION arms, not against the whole-file arm.**
The whole-file number (2.03%) was measured against the file target and **is not comparable** to
what follows.

**And mean units read is reported alongside**, because the confound this whole section exists to
remove is comparing policies at unequal budgets.

### The signature of a tuned-on-noise result, now seen twice

**V2 and V6 produced the same shape**, and having two instances makes it nameable:

| | train | holdout | paired |
|---|---|---|---|
| V2 | better than V0 (1.01% vs 1.44%) | **worse** (1.56% vs 0.69%) | b=4, **c=10**, p=0.18 |
| V6 | better than V0 (1.15% vs 1.44%) | **identical** (0.69%) | b=2, **c=6**, p=0.29 |

**Both times: a train-set advantage the paired test could not see, with the discordant cells
favouring the incumbent.** `c > b` means the challenger *lost* more of the events where the two
disagreed — so whatever produced the train advantage was not the head-to-head comparison.

**That is what a tuned-on-noise result looks like from the inside**, and it is visible without a
holdout. **When the aggregate favours a challenger and the discordant cells favour the incumbent,
believe the cells.**

### Pre-specified: recency weighting, the last cheap test

**Orthogonal to everything else** — it changes the score, not the unit or the budget. If it works
it *improves* V0 rather than competing with it, which is why it is worth one more draw on the
holdout.

| | Rule, fixed now |
|---|---|
| Score | exponential decay: each prior touch contributes `0.5 ** (age_days / HALF_LIFE)` |
| **Half-life** | **90 days**, one parameter, chosen before seeing any result |
| Unit | files, so it competes against V0 directly |
| Budget | top-3, matched to V0 |
| Control | alphabetical, same units, same k |
| Holdout | the same two clones, unchanged |

**And this is the last variant run against these 8.** Six have now been tested against a
two-clone, 578-event holdout. It can catch a reversal and cannot certify a winner, and further
variants draw down a resource that is nearly spent. **After this, the random-5 draw is the
binding constraint on every number in the table.**

### Five pre-specified variants — RUN, with controls and a holdout. None beats file top-3.

**Not a sweep.** 1,969 paired events on 8 repositories carries about five comparisons before
multiplicity eats the result, and this project has already recorded ten metadata signals where
nothing survived Bonferroni. Five variants, each with its non-informative control, Bonferroni α = 0.01.

**Holdout fixed before anything ran:** clones sorted by name, indices 2 and 5 — `OpenPipe_ART`
and `browser-use_browser-use`. Everything fitted on the other six, winner checked once on those.

| arm | train miss | control | hold miss | control | units |
|---|---|---|---|---|---|
| **V0 file top-3** | **1.44%** | 3.31% | **0.69%** | 4.15% | **3.00** |
| V6 recency-weighted files, 90-day half-life | 1.15% | 3.31% | **0.69%** | 4.15% | 3.00 |
| V5 union of file-3 and function-1 | 1.22% | 3.09% | 0.69% | 4.15% | 4.00 |
| V2 file ranked by summed touched-function history | 1.01% | 3.31% | 1.56% | 4.15% | 3.00 |
| V1 function top-3 | 9.20% | 16.61% | 7.96% | 14.01% | 3.00 |
| V3 score-gap stopping | 17.76% | 32.06% | 16.26% | 28.55% | ~2.0 |

**V6, recency weighting, is a clean null — and its holdout paired test is the most decisive
number here: b=0, c=0.** Not "no significant difference": **zero events where flat counting and
90-day exponential decay disagreed on the outcome at all.** On train it is nominally better,
1.15% against 1.44%, at b=2, c=6, p=0.29 — the same shape as V2, an advantage the paired test
cannot see.

**But "same outcome" is not "same decision", and checking the difference changed the
explanation.** The natural reading of b=0, c=0 is that the top three are so far ahead that
reweighting cannot reorder them. **That is false.** Comparing the chosen sets directly:

| | same top-3 set | same order | different outcome |
|---|---|---|---|
| train | 90.5% | 76.1% | 6 of 1,391 |
| **holdout** | **94.5%** | **82.5%** | **0 of 578** |

**Recency changed the chosen set on 32 holdout events and the order on 101 — and not one of them
changed whether the defect was covered.** The ranking is not unshakeable; it is reordered on
about one event in six, and the reordering is irrelevant.

**So the finding is narrower and more useful than "reweighting is inert".** The signal is
concentrated in the top one or two units, and **the third slot is close to outcome-irrelevant at
the margin** — the file swapped in and the file swapped out are almost always both non-targets.

**That also bounds what it implies about other reweightings.** It does *not* say every monotone
transform of the same counts will be inert; it says transforms that only move the margin will
be. A reweighting that changed *rank 1* would still matter, and this result says nothing about
one that did.

**The score axis is closed for recency**, and that was the last cheap test available.

**V2 is not supported, and the paired test says so before the holdout does.** It follows
directly from the hybrid post-mortem — keep the aggregation, drop history for functions the
change never touched.

**Lead with the paired result: b=4, c=10, McNemar p=0.18 against a 0.0125 threshold. Fourteen
discordant events in total. Whatever V2 did, this corpus cannot see it.** And the direction is
the tell — **c > b means V2 LOST more discordant events than it won on the pooled data**, so its
train-set advantage came from somewhere other than the paired comparison, most likely a handful
of events where both arms were close.

The holdout reversal — train 1.01% against V0's 1.44%, holdout 1.56% against 0.69%, **both arms
moving in opposite directions** — is corroborating evidence for a conclusion the paired test had
already reached on its own.

**V3 is decisively rejected.** Score-gap stopping reads about two units and misses 16–18%. It
beats its control by the widest margin of any arm, +14 points — **which is the clearest
demonstration in this corpus that beating the control is necessary and not sufficient.** A
policy can be far better than alphabetical and still be a bad policy.

**V5 buys nothing.** The union ties V0 on holdout at 0.69% and costs a fourth unit.

**V0 survives everything**, at the lowest budget, on both halves.

**Two checks passed.** Every arm beats its alphabetical control, on both halves. And V1 across
the split is 128 + 46 = **174/1,969 = 8.84%**, reproducing the pooled figure from the earlier run
exactly — an independent confirmation the split did not disturb the population.

### The hybrid — RUN, and it does not work

**Rank by function, expand to the enclosing file.** Same paired events, n=1,969.

| policy | files read | miss | 95% CI |
|---|---|---|---|
| **top-3 files** | 3 | **1.22%** | 0.82–1.81% |
| top-3 functions → their files | ≤3 | **2.03%** | 1.50–2.75% |
| top-5 functions | — | 3.50% | 2.78–4.41% |
| top-2 functions → their files | ≤2 | 4.37% | |
| top-1 function → its file | 1 | 12.09% | |

**At the same file count, function ordering picks WORSE files than file ranking does** — 2.03%
against 1.22%, intervals barely touching. The hybrid is rejected.

**It does beat pure function allocation** (2.03% against 3.50%), so expanding to the enclosing
file recovers most of what the function unit gives up. **It just never catches plain file
ranking.**

**The likely reason, and it inverts the intuition that motivated the test.** A file's touch count
is roughly a *sum* over its functions, so file ranking **aggregates** signal across the whole
file. Taking the top function and expanding **discards** the rest of that file's history and then
reads the file anyway. Summing beats taking the maximum — which is the same arithmetic that made
the reverse discordant cell exist in the first place, pointing the other way this time.

**So the ordering result and the allocation result are about different questions and both hold.**
Global function ranking is better at *naming the unit a fix returns to* (75.0% vs 58.9% top-1).
File ranking is better at *choosing what to read*. Nothing reconciles those into a hybrid that
wins; they are answers to two questions and the allocator only asks the second.

**This is no longer a live question. It is a finding the plan has not absorbed.** Six independent
variants, each against its control, on both halves of a pre-declared split, all point one way:
**allocate at file level.** The plan specifies ranking *and reading* functions, and the reading
half is wrong on every measurement taken.

**What survives of the function unit is routing** — naming which unit a fix returns to, where
global function ranking scores 75.0% top-1 against 58.9%. That is a different question from what
to read, and the allocator only asks the second.

**The honest remaining uncertainty is not which is better on this corpus.** It is whether this
corpus generalises — the random-5 draw, and nothing else.

### The first run was wrong, and the diagnostic is why we know

The first attempt reported +7.41 points on a **broken symbol index**, and the ratio m/k = 1.17
was the tell — barely one function per changed file, where a real change edits more.

**Classifying all 250,735 hunk headers found the cause.** Only 35.6% carried a `def`; **38.3%
carried a `class`.** Git's *default* funcname heuristic takes the nearest preceding line starting
in column 0 — which in Python is the `class` line, never the indented method. **Every method
inside a class was attributed to its class and no symbol recorded.**

Enabling git's python diff driver, measured on browser-use:

| | `def` | `class` |
|---|---|---|
| default heuristic | 57.8% | 30.6% |
| **python diff driver** | **85.4%** | **5.3%** |

### Matched coverage — RUN. Seventy per cent of the gap was budget, not granularity

**Top-3 files against top-5 functions, the pre-specified rule.**

| | miss | 95% CI | gap vs file top-3 |
|---|---|---|---|
| file, top-3 | 24/1,969 = 1.22% | 0.82–1.81% | — |
| function, top-3 | 174/1,969 = 8.84% | 7.66–10.17% | **+7.62 pts** |
| **function, top-5 (matched)** | **69/1,969 = 3.50%** | **2.78–4.41%** | **+2.29 pts** |

**Seventy per cent of the apparent gap was the smaller net.** McNemar at matched coverage still
gives p < 0.0001, and the reverse cell grows as predicted (c = 7 → 15) when the function net
widens.

**Read against the rule fixed before the run: functions still lose, so granularity is genuinely
worse** — but by 2.29 points, not 7.62. **Both prior measurements survive together.** Function
*ordering* is better (75.0% vs 58.9% top-1). Function *allocation* at equal budget is slightly
worse. The headline gap was mostly the third thing: three functions is not three files.

**So the earlier framing overstated by roughly 3×**, and the honest sentence is: at a fixed
number of units the function unit costs about two points of recall; at a fixed *count of three*
it costs seven and a half, because three functions covers less of a change than three files.

### What the re-run changed, and what it did not

| | broken extraction | corrected |
|---|---|---|
| symbol slots | 7,846 | **14,059** (+79%) |
| m/k | 1.17 | **1.64** |
| **gap** | +7.41 | **+7.62 points** |
| c′ / c | 5.7× | **2.4×** |

**The extraction nearly doubled and the gap moved 0.21 points** — but **this is not a
before/after on the same events, and must not be read as a stability result.** Better extraction
qualified more events, so n went 1,377 → 1,969, a 43% increase. Two measurements on overlapping
but different populations. The claim that survives is *the gap is present in both*, not *the gap
is stable*; establishing the latter needs the corrected run restricted to the original events.

**And something did move a great deal: c′/c fell from 5.7× to 2.4×, a 58% change**, while the
headline barely shifted. **That argues the decomposition is poorly constrained rather than
confirmed**, and against leaning on c and c′ for the transfer question.

**The decomposition still does not fully collapse.** c = 0.90 points per uncovered file against
c′ = 2.13 per uncovered symbol, with m/k = 1.64. So the function arm remains worse *per unit*,
not merely burdened with more units — closer than the broken run implied, and not the `c′ ≈ c`
that would have narrowed transfer to "is functions-per-file stable".

**Populations differ from the corpus-wide run**, which requires no symbols: this file arm is
1.22% against 4.6% there. **Do not compare those two figures.**

**Say "at most", not "is".** Three separate biases push the same way — the function arm's miss
rate is inflated by each, and nothing corrects any of them:

1. **8 convenience-sampled clones** carrying larger changes than the other 17.
2. **Residual misattribution.** Git reports the *nearest preceding* match, so a hunk between two
   functions is credited to the earlier one — a symbol in the index that is not the one changed.
3. **14.6% of hunks still yield no `def`** even with the driver.

Each puts a defect's true function outside the index or outside the target set, which inflates
the function arm and nothing else. **So it is at most +2.29 at matched coverage, and at most
+7.62 at equal count.** The random-5 draw remains the planned second step.

**Cheap partial check, since m/k is the tell:** with correct extraction, how does m/k
*distribute*? A substantial share of changes still yielding exactly 1.0 functions per file are
candidates for residual misattribution and can be eyeballed.
