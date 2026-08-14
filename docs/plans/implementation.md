# Implementation plan

> **Derived document.** Measurements here are copied from `QUANTAMIND.md`, which is canonical.
> Reconciled against it on 2026-08-14. If the two disagree, that one wins and this is the
> bug.

**Written 2026-08-13.** Filename deliberately does not start with `session-`, because the
session-end hook writes to that pattern and would overwrite this.

This is the plan for building the product, instrumenting it so we can tell whether it works,
and turning it into revenue. It assumes `docs/plans/product-skeleton.md` for structure and
`docs/QUANTAMIND.md` for evidence, and repeats neither.

**Stages are named, never numbered in cross-references.** Inserting a stage between two numbers
is how a build order silently stops matching the document describing it.

---

## What is already true

| | |
|---|---|
| `AGENTS.md` | rewritten for this product, committed |
| `LAYER_ORDER` | `types → store → ingest → parse → rank → allocate → infer → verify → render → serve`, enforced |
| Package | `src/quantamind/`, renamed by `git mv`, guards updated |
| Pass count | **one** at rank 1, three-request ceiling, specified in the build plan |
| Ranking evidence | top-1 **86.2%**, top-3 **95.4%** vs an 89.4% null on ≥4-file changes, cold-miss **4.6%**, 7,493 events, 25 repositories |
| Cost ceiling | **$0.140** per pull request, **$28** per repository per month at 200 pull requests |

**Nothing under `src/quantamind/` exists except the package root.** Every stage below starts
from an empty layer.

---

## The rule that governs every gate here

Each stage has a gate that can **fail**. A gate that cannot fail is decoration.

So each gate below is written with its **known-answer test**: what the check outputs when the
thing it checks is broken. If that answer is "the same thing", the gate is rewritten before the
stage begins. This is `AGENTS.md` rule 14 applied in advance rather than discovered afterwards,
and this project has already lost four measurements to skipping it.

---

# Stage — The skeleton

**Goal: every layer exists, is importable, and does nothing.** No business logic.

### Steps

1. Create the ten layer directories under `src/quantamind/`, each with `__init__.py` and a
   module docstring naming what it does, why it exists, what it imports, and who consumes it.
2. Write `types/settings.py` — one frozen settings object, populated from the environment,
   validated at import. **No other module reads `os.environ`.**
3. Write the core value objects in `types/`:
   - `change.py` — `ChangedUnit`, `Diff`, `Repo`, `PullRequest`
   - `ranking.py` — `Ranking`, `RankedUnit`, `Score`
   - `finding.py` — `Finding`, `Claim`, `ClaimKind`
   - `verdict.py` — `Confidence`, `Provenance`, `Unresolved`
   - `review.py` — `Review`, `CoverageLine`, `RequestLedger`
4. Every dataclass `frozen=True, slots=True`. Every enum exhaustive, checked by mypy.
5. `serve/app.py` returns healthy. `serve/cli.py` prints its version and exits 0.

### Output

A repository where `just check` passes and `uv run quantamind --version` works.

### Tests

- **Unit:** every type constructs, every enum round-trips through the store.
- **Property:** `Unresolved` cannot be constructed without a `reason` and a `construct`.
- **Guard:** `check_conventions.py` proves no layer imports rightward.

### Gate

`just check` green, and one end-to-end test posts a fake webhook and asserts a 200.

**Known-answer test:** delete the import-direction check from `check_conventions.py` and
introduce a `verify → infer` import. The suite must go red. If it stays green, the guard is
walking a directory it thinks is excluded — which has happened here before.

### What could silently fail

The layer guard walks `src/quantamind/` by name. Rename the package without updating
`PACKAGE` in the guard and it walks nothing, reports `ok`, and enforces no layering at all.
**Mitigation:** a test asserting the guard finds a non-zero number of files.

---

# Stage — The reader

**Goal: read a repository and a pull request into typed values. No ranking, no model.**

### Steps

1. `ingest/git_history.py` — walk history once per repository. **Assert the git exit code on
   every call**; raise a typed error, never return an empty list. This is the defect that
   voided four measurements and reproduced again on `apache_airflow` while writing this plan.
2. `ingest/git_diff.py` — the diff for one pull request, as hunks with file and line ranges.
3. `ingest/github_pulls.py` — pull request metadata. Timeout 30s, declared.
4. `ingest/github_comments.py` — post one comment, idempotently, keyed on head SHA.
5. `parse/languages.py` — which languages we parse, and to what depth. **Public, and printed in
   the coverage line.**
6. `parse/units.py` — map diff hunks to the functions they touch. Two passes: git's funcname
   diff drivers as the cheap first pass, tree-sitter as the exact one.
7. `parse/signatures.py`, `parse/references.py` — signatures and call sites.
8. Everything unparseable emits `Unresolved(site, reason, construct)`. **Never nothing.**

### Output

`uv run quantamind read <repo> <pr>` prints the changed units, the signatures, and the
unresolved list, as JSON.

### Live verification

Against the pinned submodules in `tests/live/fixtures/repos/`, plus five repositories from the
research corpus, run `read` and diff against a checked-in golden file **reviewed by a human**.

### Gate

**Conservation:** for every diff, `parsed units + unresolved sites == total sites`. Nothing
vanishes.

**Known-answer test:** feed a file in a language we do not parse. It must appear in
`unresolved` with a reason, not be absent from both lists. **Sabotage the whole mechanism, not
the entry point** — disable the tree-sitter path *and* the funcname path; a previous sabotage
here disabled only the entry point and left the suite green, reading as coverage.

### What could silently fail

A blobless clone. 27 of 35 clones in the research corpus are `blob:none`, and a cold read
lazily fetches trees over the network — non-deterministic until warm, and a network failure
looks like a small repository. **Mitigation:** `ingest` records clone filter and object count
per read, and the review record carries both.

---

# Stage — The ranker

**This is the stage that decides whether the research is the product.**

### Steps

1. `rank/touch_index.py` — the index built from history. Bounded strictly by the parent commit;
   **no data from after the change may enter the ranking of that change.**
2. `rank/percentile.py` — the percentile threshold. Absolute thresholds fired at 11% on one
   repository and 53% on another; percentiles self-calibrate to 10–12% across an 80× velocity
   range.
3. `rank/ranker.py` — the ranking itself, global across the diff, never file-then-function.
4. A `NullRanker` shipped **in the test tree, not in `src/`** — alphabetical, non-informative,
   run on every gate.

### Output

`uv run quantamind rank <repo> <pr>` prints the ranked units with scores and the fire decision.

### Three gates, not one — they fail for different reasons and share no evidence

A single stage that can fail three ways gives one bit of information when it fails. Ranker
reproduction is a correctness check against research already collected. Allocation loss needs
labelled outcomes. Cost needs live `usage` figures on real diffs. **They are separated so a
failure names itself.**

| | Gate | Needs |
|---|---|---|
| **3a** | the productionised ranker reproduces the research ranker on the collected corpus | nothing new — run it today |
| **3b** | measured per-pull-request cost across **all** calls, with `cache_read_input_tokens` non-zero | live traffic |
| **3b′** | **the shipping policy's miss rate stated on the record, at whatever budget ships** — 8.84% at three units, 3.50% at five — **and the coverage line naming what it did not read** | measured; the coverage line is a build item |
| **3c** | allocation loss at **function** level, stated with an interval | live traffic, shares 3b's run |

**3a does not wait on the other two**, and it is the one that can end the project. 3b and 3c
share a single instrumented run.

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

### Gate 3a — the hard one

**The productionised ranker reproduces the research figures on the corpus already collected:**

| Metric | Research value | Tolerance |
|---|---|---|
| Top-1, pooled | 86.2% | ±2 points |
| Top-3, changes touching ≥4 files | 95.4% | ±2 points |
| Cold miss, ≥4 files | 4.6% | must not exceed 7% |
| Fire rate | 10–12% | must not exceed 15% |
| Alphabetical null, top-1 | 72.0% | ranker must beat it by ≥8 points |

**If it does not reproduce, stop.** The research measured something the product cannot, and
that must be understood before anything is built on top of it.

**3b's known-answer test** is that the cost figure counts every request, not the deep read
alone. A per-pull-request cost that matches the single-call arithmetic is evidence the
instrumentation is counting one call, not that allocation got cheaper.

**3c's known-answer test** is stated in the master document: the function-level miss rate should
come in **above** the file-level 1.77%, because functions are a finer partition. A result that
matches the file-level number is a signal the extraction did not change units.

**Known-answer test for 3a, and it is the important one here.** A ranker returning a constant scores
above 70% on top-1 because the null is 72%. So the gate is not "the number is high" — it is
**"the number is high AND the null ranker, run through the identical harness, is not."** Three
sabotages, all required to go red:

1. Replace the score with a constant → top-1 must fall to the null.
2. Reverse the ranking → top-1 must fall below the null.
3. Let post-change history into the index → top-1 must rise implausibly. **A rise is a failure
   here**, and the only sabotage in this plan whose failure signal is an improvement.

### Live verification

Re-run against all 25 repositories with the skip ledger printed. **Any failed read refuses to
report.** Compare per-repository against `research/phase0/results/top3_recall.json`.

### What could silently fail

The research harness ranks **files**; the product ranks **functions**. These are different
units and the file-level number may not transfer. **This is the single largest technical risk
in the plan.** Mitigation: the gate runs at both granularities and reports both; a function-level
number materially below the file-level one is a finding, not a rounding error.

---

# Stage — The free tier

**Goal: something shippable that runs no model at all.** First public release.

### Steps

1. `render/coverage_line.py` — what we checked, what we did not, and why.
2. `render/comment.py` — the comment body. Coverage first, findings second.
3. `serve/cli.py` — `quantamind review <pr> --no-post` runs the whole path locally.
4. `render/digest.py` — the weekly Slack message.

### Output

A real comment on a real pull request, containing a ranking and a coverage line and **no model
output**.

### Gate

Install on our own repository. **For ten consecutive pull requests, the coverage line must be
accurate when checked by hand.** Not "plausible" — checked, unit by unit, by a person.

**Known-answer test:** a coverage line that always prints 100% looks identical to a correct one
on a well-parsed repository. So the gate includes a repository with a deliberately unparseable
file, where the correct answer is **not** 100%.

### Why ship this first

It is the tier a sceptic runs before granting repository access, it is what the retrospective
prints, and it costs us compute rather than inference. It is also the only part of the product
we can give away without giving away margin.

---

# Stage — The retrospective

**Goal: the sales motion.** Replays history and shows where we would have pointed.

### Steps

1. `serve/cli.py` gains `quantamind retrospective <repo> --since 180d`.
2. For each merged pull request in the window, in ancestral order: rank it using only history
   before it, record the top-ranked unit, then look forward for a later fix touching it.
3. `render/report.py` — the customer-facing document.

### Output

An HTML and Markdown report: every merged pull request, what we would have pointed at, whether
a later fix went there, and what we could not read.

### Gate

Runs end to end on three repositories of different sizes, and **the numbers it prints match a
hand audit of twenty randomly selected pull requests.**

**Known-answer test:** the lookahead must be bounded by `git merge-base --is-ancestor`. Remove
the bound and the report's hit rate must rise — an unbounded lookahead scores better and is
wrong. **A report that improves when the bound is removed is the failure signal.**

### What could silently fail

Time-travel. A ranking that sees any commit after the change is not a prediction, it is a
lookup. **Mitigation:** the ranker takes an explicit `as_of` commit and the store refuses reads
beyond it. Not a convention — a refusal.

---

# Stage — Allocate, infer, verify

**`verify` ships in the same change as `infer`, never after it.** A reviewer publishing
unchecked model claims for even one release is the failure this product exists to prevent.

### Steps

1. `allocate/budget.py` — emits a `Budget` carrying a **maximum request count**. Exceeding it
   raises; it never silently degrades.
2. `allocate/tiers.py` — deep for rank 1 at one pass, shallow for ranks 2–3, nothing for cold.
3. `infer/client.py` — `claude-opus-5`. Check `stop_reason` before `content[0]`; a refusal is
   an HTTP 200. Stream anything above roughly 16K.
4. `infer/prompts.py`, `infer/schemas.py` — structured output only. **The verifier can only
   check a claim it can parse**, so free-text review output would make verification impossible.
5. `infer/caching.py` — repository prefix cached; **no clock, no request id, nothing volatile in
   the prefix.** A clock there makes every request a cache miss with no error.
6. `verify/claims.py` — extract the structural claims from a finding.
7. `verify/adjudicate.py` — check each against the parse. Confirmed publishes; contradicted
   drops; **undecidable is labelled, not silently published.**

### Output

A review with findings, each carrying a verdict and a provenance.

### Gates

| Gate | Passes when |
|---|---|
| **Request ceiling** | observed request count ≤ 3 on 100 consecutive reviews, read from the ledger, not from the config |
| **Cost** | observed cost per pull request within 20% of $0.140 |
| **Cache** | `usage.cache_read_input_tokens` non-zero on the second request of every review |
| **Sabotage** | an injected false structural claim is dropped |
| **Drop rate** | the live counter reports a non-zero, non-100% drop rate by claim class |

**Known-answer test on the ceiling:** a ceiling never hit and a ceiling never wired up print
the same thing. So the test sets the ceiling to 1 and asserts the run **raises**. If it does
not, the ceiling is decoration.

**Known-answer test on the verifier:** the sabotage gate proves it can reject **once, on the
planted case**. It cannot distinguish "rejecting correctly" from "rejected that one and nothing
since". The drop-rate counter is what proves it still works — and a drop rate that falls to zero
and stays there is either a flawless model or a dead verifier. **Those must not look the same on
the wire**, so zero for seven consecutive days raises an alert.

### What could silently fail

**The verifier is a parser, so it cannot adjudicate semantic claims** — and semantic defects are
the reason a model runs at all. A wrong semantic finding publishes. This is not fixable within
this stage; it is bounded by labelling every published finding with whether it was verified or
merely suggested, and never claiming more.

---

# Stage — Serve

### Steps

1. `serve/webhook_github.py` — signature verification, then enqueue. **Verify before parse.**
2. Idempotency keyed on `(repo, pr, head_sha)`. A redelivered webhook must not double-post.
3. `serve/review_status.py`, `serve/health.py`, `serve/admin_policy.py`.
4. `serve/contracts/` — Pydantic models at the edge, mapped explicitly to `types/`.
5. GitHub App: read on code, write on pull request comments. **Nothing else requested.**

### Gate

Replay 100 real webhook deliveries including duplicates and out-of-order arrivals. **Exactly one
comment per head SHA.**

**Known-answer test:** send the same delivery twice. Two comments is a fail. Then send with a
bad signature — a 401 and no queue entry. A handler that parses before verifying accepts
attacker-controlled JSON, and its happy path looks identical.

---

# Memory: what we store, and why it is not a graph

The question this section answers: **when the product is wrong, how do we find out, and how do
we improve it?**

### The shape of the problem

The label arrives late. We rank a change today; whether the fix returns to that unit is knowable
in two to eight weeks. **So the store must be append-only with late-arriving outcomes**, and
nothing may be overwritten when the truth turns up.

### Why not a graph database

There is a graph in this product — changes, follow-up fixes, and the edges between them. But the
queries are relational: *count reviews where the ranked unit matched a later fix, grouped by
repository and month.* A graph store buys traversal we do not need and costs an operational
dependency. **SQLite per install, Postgres for cloud. The graph is a table of edges.**

We reconsider only if a query needs traversal deeper than two hops, which none currently does.

### The tables

```
repo            id, host, name, clone_filter, first_seen, languages_parsed
review          id, repo_id, pr_number, head_sha, created_at,
                fire_decision, coverage_pct, request_count, tokens_in,
                tokens_out, cost_cents, latency_ms, tier
ranked_unit     review_id, unit_path, unit_name, rank, score,
                percentile, allocation          -- deep | shallow | cold
                -- EVERY changed unit, including cold ones. Not the funded subset.
                -- Cold rows are the coverage line's content and shadow evaluation's
                -- denominator; dropping them silently removes both.
finding         id, review_id, unit_path, kind, body, published,
                confidence, provenance
claim           id, finding_id, claim_kind, verdict, reason
                                                -- confirmed | contradicted | undecidable
unresolved      review_id, site, reason, construct
outcome         review_id, unit_path, fix_sha, fix_at, source, matched_rank
                                                -- git | datadog | manual
reaction        review_id, finding_id, kind, actor_hash, at
                                                -- resolved | dismissed | replied | emoji
shadow_pick     review_id, ranker_name, unit_path, rank, score, percentile
                -- ranks 1..k for k >= 3, NOT the top pick only
request         id, review_id, ordinal, model, model_version, effort,
                tokens_in, tokens_out, cache_read_tokens, cache_creation_tokens,
                latency_ms, stop_reason
```

### Three things the schema must record from the first row, because append-only cannot backfill

**`shadow_pick` stores a ranked LIST, not a top pick.** The allocator funds ranks 1–3 and
top-3 recall is the metric that decides whether allocation loses defects — and **top-3 for a
candidate ranker cannot be computed from a top-1 record.** Scores and percentiles go in too, or
the firing threshold cannot be re-derived either. This is the most consequential line in the
design: shadow evaluation on free-tier traffic is the strongest asset here, and a top-1 schema
silently halves it.

**Token counts per request, and cost derived from them — never a stored `cost_cents`.** Prices
change and token counts do not. Cents cannot separate a cache read from fresh input, and they
round away shallow calls that cost fractions of a cent. **Gate 3b is measured against uniform
review, and a cents column cannot produce that measurement.** `requests=3` on the review row is
a summary; the `request` table is the data.

**`outcome` carries a `rule_version` and the inputs to re-derive it.** The attribution rule has
already been corrected once — file overlap to symbol overlap, which changed 67.9% of verdicts.
Correct it again and every stored outcome needs re-deriving, and without a version stamp nobody
can tell which rule labelled which row. The rule also assumes English fix-keywords in commit
subjects, so the subject is stored rather than just the verdict.

**`outcome` is the table the product is built to fill.** Everything else describes what we did;
this one says whether it was right.

### The cache monitor lives in the data, not in a test

The build plan verifies `cache_read_tokens` in tests, where a persistent zero means an
invalidator is in the cached prefix. **On Cloud Run that becomes a production concern**: many
short-lived instances, and any per-instance value that reaches the prefix — an instance id, a
boot timestamp, a request id threaded through the system prompt — is a **total cache miss with
no error and no failing test.**

Because `request` stores cache-read tokens per call, a persistent zero is visible as data.
**Alert on it.** A test that passed once cannot see a regression that arrives with a deploy.

### The two rules on this store

**Append-only, and no destructive migration.** The schema is versioned; changing
`store/schema.py` requires a migration and a `SCHEMA_VERSION` bump. There is no
delete-and-reindex path in production, because the outcome history *is* the asset.

**Never store source code.** `finding.body` quotes at most a few lines. `unit_path` and
`unit_name` are identifiers. A telemetry table that accumulates customer source is a breach
waiting for a date.

### How outcomes get filled

| Source | Mechanism | Latency |
|---|---|---|
| **git** | a later commit whose subject looks like a fix touches a ranked unit | days to weeks |
| **Datadog** | Error Tracking suspect commits, consumed as configuration | hours |
| **manual** | a reviewer marks a finding as real | immediate, rare |

The git path is the one we control and the one the research validated. **Datadog is the faster
signal and we consume rather than rebuild it** — see the integrations section.

## Before routing inference through Vertex, three things to confirm

Claude runs on Vertex AI, so model spend could land on a GCP bill and against GCP credits.
**Three checks before any plan depends on that**, and none is a formality:

1. **Do the credits apply to partner models?** Some GCP credit programmes exclude marketplace
   and partner models. Ask the account representative about Claude on Vertex specifically.
2. **Does prompt caching behave identically?** Same cache-read multiplier, same five-minute and
   one-hour window economics. **The entire cost architecture rests on this**, and a difference is
   not a rounding error.
3. **Is structured output the same?** The verification pillar requires findings to arrive as
   parseable structure. Free-text output makes adjudication impossible, so a gap here is not a
   degradation — it removes a layer.

**And keep the label attached to any figure derived from it.** $0.140 per pull request is
derived from a specification, and its shallow-call token sizes are assumed rather than observed.
Any headline built on it — "$16,000 of credits is roughly 114,000 reviews" — inherits that, and
should carry it.

## Which database runs, and when

**The split is not free versus paid. It is local versus hosted.** Both engines run the same
schema and the same migrations, and the store layer is written to SQL both accept.

| Where the product runs | Engine | Whose machine |
|---|---|---|
| `quantamind review` / `retrospective` on a laptop | **SQLite**, one file | theirs |
| The GitHub App, **any tier including free** | **Postgres**, one shared database | ours |
| Enterprise self-host | **Postgres** in their VPC | theirs |

### Walking one customer through it

**They run the retrospective first.** `uv run quantamind retrospective` against a clone. That
writes `quantamind.db`, a SQLite file in their working directory. **No account, no upload, and
we never see it.** This is the whole point of the CLI existing: a sceptic can check the claim
before granting anything.

**They install the App on the free tier.** Now reviews run on our infrastructure, so rows land
in our Postgres — one row in `repo`, then a `review` row per pull request with its
`ranked_unit` and `unresolved` children. **`finding` and `claim` stay empty**, because the free
tier runs no model. Their SQLite file stays on their laptop; nothing is imported, because a
retrospective is a report rather than state worth migrating.

**They upgrade to Team.** *No data moves and no database changes.* It is a plan column on their
organisation row. From the next pull request, `allocate` permits inference, so `finding` and
`claim` rows start appearing beside the ones already there. **The upgrade is visible in the
data as the moment those tables start filling** — which is exactly how it should read, because
that is what they started paying for.

**They upgrade to Business.** Again no migration. The `org` row gains their second and third
repositories, and the cross-repository report becomes a query over rows that were already being
written. **Everything the org view needs has been collected since the free tier**, which is why
the schema change for `org` lands before the first Business customer rather than after.

**They go Enterprise and self-host.** A container plus a Postgres they operate. Same schema,
same migrations, run by command. **We hold nothing.** Telemetry from that install is opt-in and
sends counts only.

### Why one shared Postgres rather than a database per customer

A database per customer means a migration is a fleet operation and a schema bug is discovered
customer by customer. One database with rows keyed by organisation means one migration, run
once, verified once. **The cost is that isolation is now a query predicate rather than a
boundary**, so every read is scoped by organisation at the repository layer and that scoping is
what the tests target — a missing `WHERE org_id` is the failure mode this trade buys, and it
must be tested for directly rather than assumed.

### The constraint that keeps both engines possible

**No engine-specific features in `store/`.** No Postgres arrays or `JSONB`-only queries, no
SQLite pragmas doing anything but performance. The moment one appears, self-hosting on SQLite
stops working and the CLI stops being able to run the same code as the App — and the CLI's
whole value is that it runs *the same pipeline*.

**Gate, and it is a CI job rather than a note.** `.github/workflows/ci.yml` gains a `store`
job that runs the `store/` suite twice — once against SQLite, once against a Postgres service
container — and asserts identical results. A written rule that nothing can fail is a wish; this
is the same argument the sabotage test rests on, applied to a rule this plan had left as prose.

**Row-level security is worth an hour before the first Business customer.** Postgres RLS turns
the `org_id` predicate back into a boundary without giving up the single-migration benefit, and
it is far harder to retrofit once queries exist that assume it is absent.

### Retention

**Retention is set on the measurement, not on the table**, and the earlier version of this
policy got it wrong in a way that would have destroyed the asset it meant to protect.

An `outcome` row on its own is unusable. `review=8801, unit=process_refund, fix_sha=b71e` says a
fix happened — it does not say what rank we gave that unit, or what any candidate ranker would
have picked. **The `ranked_unit` and `shadow_pick` rows are what turn an outcome into a
measurement.** Expiring those at 90 days while keeping outcomes forever would retain the truth
and delete the belief it exists to adjudicate.

| What | Kept |
|---|---|
| An `outcome`, **and the `ranked_unit` and `shadow_pick` rows it adjudicates** | **indefinitely, together, at every tier** |
| Reviews with no outcome, findings, claims, comment bodies | 90 days free · 2 years paid |
| Enterprise | their policy, and they hold it |

**This matters most on the free tier**, which is where shadow data accumulates at zero inference
cost — the counterfactual evaluation a model-per-diff competitor cannot replicate at any tier.

### Enforced by the database, not by the deletion job

A retention job written against table names deletes exactly the rows this policy exists to keep,
**and produces no error**: the tables still exist, queries still return, and the loss surfaces
months later when someone asks a question the deleted rows would have answered. That is the
signature of every instrumentation failure this project has recorded — plausible output, nothing
detectable from the output alone.

**So it is a constraint, not a comment.** `outcome` holds foreign keys to the `ranked_unit` and
`shadow_pick` rows it adjudicates, `ON DELETE RESTRICT`. The wrong deletion aborts. A job that
has to be written around a constraint is one somebody thinks about; a job that silently satisfies
a policy paragraph is not.

**The application role has no DELETE on `ranked_unit` or `shadow_pick`.** The constraint above
cannot express "keep this until we know whether it matters", because that is a fact about the
future and there is no row to point at yet. So it is expressed as an **absence of capability**
rather than a rule: a retention job that tries to delete these fails loudly at runtime, and
nobody has to remember the policy. Pruning later goes through a separate migration role with a
deliberate grant — a decision somebody makes, not a job that runs.

**`ranked_unit` is not deleted at all.** Adjudication arrives two to eight weeks late and
retention runs on a schedule, so a row at day 89 with no outcome yet is indistinguishable from
one that will never get an outcome. The rows are small and they are the belief half of the only
comparison this product sells. Keeping them is cheaper than being wrong about which ones matter.

**And the job reports both numbers**: rows deleted, and rows retained *because* they adjudicate
an outcome. A retention job that never retains anything is not retaining.

### The house rule these three share

Three mechanisms in this plan exist because a check that cannot report having fired is
indistinguishable from one that was never connected:

| Mechanism | What its silence would otherwise mean |
|---|---|
| The verifier's **drop-rate counter** | a flawless model, or a dead verifier |
| The **alphabetical ranker running in shadow forever** | a working ranker, or one measuring nothing |
| The **retention counter** | nothing needed keeping, or the constraint is not wired |

A fourth is already in the research: a dead hotspot check reported zero at every threshold until
a sanity counter reported in-window commits found — **0 before the fix, 1,298 after.**

**Rule: every check reports what it did, not only what it found.** Ask what a mechanism outputs
when the thing it protects is broken; if the answer is "the same thing", it is not a mechanism.

---

### Shadow ranking: how the product improves without shipping regressions

Every review runs the live ranker **and** every candidate ranker, recording all picks in
`shadow_pick`. Only the live ranker's output is published.

Weeks later, when `outcome` fills, we can ask: *which ranker would have been right?* — on real
customer traffic, with no experiment, no traffic split, and no risk.

**A candidate is promoted only when it beats the live ranker on outcomes across at least three
repositories and does not lose on any.** The alphabetical null runs in shadow permanently: if it
ever draws level with the live ranker, something has broken upstream and the whole ranking is
measuring nothing. **That is the single most valuable row in this table** — it is the check that
tells a working ranker from a dead one, and without it both print a plausible number.

### The analysis queries we commit to running monthly

1. Top-1 and top-3 against outcomes, per repository, per month. Trend, not a point.
2. Cold-miss rate — outcomes landing on a unit we gave no model call.
3. Drop rate by claim kind. Zero for a week is an alarm, not a success.
4. Fire rate per repository. Drift away from 10–12% means the percentile is mis-calibrated.
5. Coverage percentage distribution. A rise without a parser change means we stopped noticing
   what we cannot read.
6. Reaction rate on published findings. The only direct human signal we get.
7. Live ranker versus every shadow ranker, including the null.

**Each has a number that means "broken" as well as one that means "good".** A query with only
the second is not a check.

---

# Tracking: what we count and what we refuse to

### The one number

**Weekly active repositories with at least one acted-on finding.**

Not installs, not reviews posted, not comments. A repository where reviews go out and nobody
ever reacts is churn that has not happened yet, and counting it as usage hides that.

### The counters

| Group | Metric |
|---|---|
| **Adoption** | installs, active repositories, active developers (opened a PR this period), reviews posted |
| **Frequency** | daily and weekly active repositories, daily and weekly active developers, reviews per repository per week |
| **Volume seen** | commits observed, pull requests observed, pull requests reviewed, pull requests skipped **and why** |
| **Behaviour** | fire rate, coverage percentage distribution, unresolved sites per review, languages encountered vs parsed |
| **Quality** | drop rate by claim kind, findings published per review, reaction rate, dismissal rate |
| **Cost** | requests per review, tokens in and out, cost per review, cost per repository per month |
| **Service** | time to first comment, webhook-to-comment latency, error rate, queue depth |
| **Money** | free-to-paid conversion, seats billed, expansion, day-30/60/90 retention |

**"Pull requests skipped and why" is not a vanity metric.** If we silently skip 40% of traffic,
every other number is computed on a population nobody chose.

### How it is collected

- Every review writes one row. **Telemetry is a query over the store, not a parallel pipeline**
  — a second pipeline drifts from the first and then both are wrong.
- Cloud aggregates by repository, hashed. **We never see repository names for customers who
  have not asked us to.**
- Self-hosted telemetry is **opt-in**, documented on the security page, and refuses to send
  anything but counts.
- A weekly digest email to us. **No dashboard**, for the same reason the product has none.

### What we refuse to collect

Source code. File contents. Commit messages beyond a fix/not-fix classification. Individual
developer identity — `actor_hash` is salted per install and cannot be reversed to a person.

**A tool that measures where code needs rework must never become a tool that measures which
developer causes it.** That is the fastest way to be uninstalled, and it deserves to be.

---

# Free tier to revenue

### The path

```
free report          →  free tier        →  Team           →  Business        →  Enterprise
retrospective,          ranking and         findings on       org-wide report,   own model,
no install              coverage line,      pull requests,    SSO, own key       self-host
                        no model            unlimited
```

### Where the wall sits

**The free tier runs no model.** That is not a limit we invented to force upgrades — it is what
makes the free tier free. Ranking and the coverage line cost compute. Findings cost inference.
The wall sits exactly where our cost begins, and saying so is more persuasive than a feature
grid.

### The conversion event

Not a trial expiry. **The retrospective report.** A team that has seen where we would have
pointed across their own six months has already tested the claim. The upgrade question is then
"do you want it on the next one" rather than "do you believe us".

### Triggers to watch

| Trigger | Move |
|---|---|
| Free tier active 14 days, coverage line read | offer the retrospective |
| Retrospective delivered | offer Team, two-week trial with findings on |
| Third repository connected | offer Business — the org-wide view is the reason |
| Someone asks about SSO | Business |
| A security questionnaire arrives | Enterprise, and start the process immediately |
| PR volume above the fair-use ceiling | Enterprise with their own key. **Not a cap — an upgrade** |

### Billing

**Seats = developers who opened a pull request in the period.** Reviewers and managers are free.
This matches how CodeRabbit bills, so the comparison is honest, and it removes the
"but we only have four people who actually push" objection before it is made.

Stripe. Monthly and annual. **Usage is metered in the store from day one even while every plan
is unlimited**, because we cannot price what we never measured — and the $28 per repository
figure is a ceiling derived from a specification, not from traffic.

### The separate line

**The quarterly coverage audit, $8,000–15,000 per engagement.** Different buyer, different
budget, no seat maths. Plausibly the larger business, and the reason `render/report.py` is built
during the retrospective stage rather than later.

---

# Integrations

### Slack — one message a week

`render/digest.py` posts a weekly summary: where rework concentrated, coverage trend, what we
could not read.

**Not an alert stream.** An alert per finding trains people to mute the channel, and a muted
channel is worse than no channel because it looks like a working integration.

### Jira — read, never write

**We read the linked issue to give the model intent.** A change whose ticket says *"customers
are being double-charged on partial refunds"* is a different review from the same diff with no
context.

**We do not create tickets, and we do not assign blame.** Datadog already creates tickets from
issue panels; duplicating it puts us in an occupied position with a worse product, and a tool
that files tickets naming people gets switched off within a quarter.

Scope: OAuth, read the issue linked in the branch name or PR title, pass summary and description
into the prompt prefix. **Feature-flagged per repository, off by default**, because sending
ticket text to a model is a decision a customer must make deliberately.

### Datadog — consumed as an instrument

This is the integration that closes the loop in the memory section.

Datadog Error Tracking already ships **suspect commits**, on four stated criteria: the commit
modifies a line in the stack trace, was authored before the first error occurrence, no more than
90 days before, and is the most recent commit meeting those criteria.

**So the incident-to-commit link is a configuration, not a build.** We consume it to fill
`outcome` faster than git history can — hours instead of weeks.

Two things their documentation does **not** claim, and we must not either: automatic
pull-request linking and auto-assignment. Commit-to-pull-request is a GitHub API lookup — a thin
gap, not a moat.

**What we add is the denominator.** The standard file-overlap attribution rule is wrong on 67.9%
of its verdicts. Their webhook plus our corrected rule is the measurement, and that is the whole
of our contribution here.

**Out of scope, deliberately:** reimplementing their attribution, and emitting per-incident blame
tickets.

---

# The commercial surface, which the pricing table sells and this plan did not build

**Audited against the four-tier table. Every row below was being sold with no stage, no gate and
no test.** Listing them as monetisation prose was not the same as planning them, and the gap was
only visible by reading the price list next to the build order.

| Sold on | Row | Was it planned? |
|---|---|---|
| Business | cross-repository aggregation | **No** |
| Business | quarterly coverage audit | named once, never built |
| Business | SSO / SAML / SCIM | SSO named, SAML and SCIM absent |
| Business | verifier drop-rate telemetry | covered by the telemetry section |
| Business | bring your own key, allowlisted model | mentioned, no mechanism |
| Enterprise | bring your own **model**, uncertified | **No**, and it implies a recurring process |
| Enterprise | self-host, audit logs, residency, SLA | self-host named; audit logs and residency absent |
| Team+ | token budget, fair use per repository | **No** — and it is load-bearing for margin |

Four stages follow. **None may start before the ranker gate**, because all of them are worthless
if the ranking does not reproduce.

---

## Stage — The budget ceiling

**First of the four, because it is not a feature. It is what keeps the price honest.**

At twenty developers and 400 pull requests a month, inference runs about $56 against $380 of
revenue — 85% margin. At 2,000 pull requests it is $280 against $380, or **26%**. "Unlimited
reviews" is a promise the `allocate` layer has to keep.

### Steps

1. `store/quota.py` — spend per repository per billing period, written by the same review record
   that already carries request count and token spend. **A query over the existing store, never
   a second counter.**
2. `allocate/ceiling.py` — a per-repository budget read at allocation time. Above it, the review
   still runs and still posts the coverage line; **only inference is withheld, and the comment
   says so.**
3. Threshold configurable per plan, defaulting to the fair-use figure on the price list.

### Gate

Drive a repository past its ceiling on real traffic. **Reviews keep arriving, coverage lines keep
appearing, inference stops, and the comment states that it stopped.**

**Known-answer test:** set the ceiling to zero. Every review must degrade to coverage-only and
none may fail. A ceiling that errors instead of degrading turns a billing limit into an outage.

### What could silently fail

A ceiling never reached and a ceiling never wired up look identical. The monthly analysis already
required for cost includes **spend against ceiling per repository**; a column of zeroes across
every repository means the ceiling is not connected, not that nobody is heavy.

---

## Stage — Identity and the organisation view

**What actually separates Team from Business.** Not a bigger quota — a different buyer, who has
more than one repository and someone above them asking about all of them.

### Steps

1. `serve/auth_sso.py` — SAML and OIDC. **SCIM last**, and only when a customer asks: it is user
   provisioning, it is where identity integrations rot, and nobody has ever bought because of it.
2. `types/org.py`, `store/org.py` — an organisation owning repositories. **This is a schema
   change and needs a migration**, which is why it lands before any Business customer, not after.
3. `render/org_report.py` — rework concentration across repositories, quarter over quarter.
4. `serve/admin_org.py` — role-based access. Three roles, not nine.

### Gate

Two repositories, one organisation, one report whose numbers **equal the sum of the per-repository
records** when checked by hand.

**Known-answer test:** put a repository in the organisation with no reviews. It must appear with
zeroes rather than be omitted — a silently dropped repository is how an org-wide report becomes
quietly wrong, and it looks like a clean report.

---

## Stage — Bring your own key, and the certification that follows

**Two features, deliberately split, and the split is the pricing line.** Business gets a key for
a model we have already evaluated. Enterprise gets a model we have not.

### Steps

1. `infer/providers/` — one module per provider: direct, Bedrock, Vertex, Azure. **They differ on
   cache semantics, structured-output shape and refusal handling**, and each is a maintained
   integration rather than a configuration flag.
2. `store/credentials.py` — customer keys encrypted at rest, never logged, never in a review
   record. **A key in a log is a breach with a date on it.**
3. `infer/allowlist.py` — the models certified for Business. Anything outside it is Enterprise.
4. **`scripts/certify_model.py` — the recurring process this plan had no place for.** For a model
   we have not evaluated: run the verifier against it on the corpus and record the drop rate by
   claim class. **We publish a coverage number under our name; publishing one for a model we
   never measured is the failure this product exists to prevent.**

### Gate

The same pull request reviewed through two providers produces **the same structural claims**.
Where it does not, the difference is recorded in the certification, not averaged away.

**Known-answer test:** a deliberately weak model must produce a **higher** drop rate, and
certification must refuse to pass it. If every model certifies, the certification measures
nothing — and this is the one gate whose failure is silent, because a bad certification still
prints a number.

### What could silently fail

Certification is **not one-off**. A provider updating a model silently invalidates it. Record the
model version in every review, and treat an unrecognised version as uncertified rather than
assuming continuity.

---

## Stage — What procurement requires

**Bought by security review, not by engineers.** None of it improves the product and all of it is
mandatory above a company size.

**Checked against what the competition already holds, because this is the one area where being
behind loses a deal before anyone sees the product.** Greptile lists SOC 2 Type II, self-hosted
deployment, SSO/SAML, GitHub Enterprise compatibility and a custom DPA. CodeRabbit lists SOC 2
Type II, GDPR, SSO, audit logs, zero-retention options and self-hosting. **Both hold SOC 2
Type II today.**

### The item that cannot be triggered on demand

**SOC 2 Type II is the gate, and it has a lead time that breaks the trigger below if ignored.**

A Type II report needs an *observation window* — typically three to six months for a first
audit — on top of readiness work and fieldwork. **Roughly six to nine months from kickoff to a
report**, and the auditor cannot compress the window, because the window is the evidence. Budget
in the region of $20,000–$60,000 all in for a company this size. *(Figures from published
guidance; confirm with an auditor before planning against them.)*

**So it cannot start when the first questionnaire arrives.** Starting then means losing that deal
and the two behind it. **It starts when enterprise becomes a target, not when it becomes
urgent** — and a Type I report is what covers the gap, since it needs no observation window and
demonstrates the controls exist.

### Steps

1. **Begin SOC 2 readiness on the decision to sell to enterprise.** Everything else here is
   evidence that feeds it.
2. `serve/audit_log.py` — append-only: who changed configuration, when, from where. **Separate
   from application logs**, because the first question in an audit is whether the log could have
   been edited.
3. Data residency — region-pinned storage, chosen at install and not migratable afterwards.
4. **Zero-retention mode** — asked for by name by regulated buyers, and a competitor already
   offers it. Nothing but the review record persists; no diff content at rest.
5. Self-hosted deployment: container, migrations run by command, an offline licence check that
   **fails open**. A licence check that fails closed takes a customer's reviews down over our
   billing problem.
6. **GitHub Enterprise Server**, which is not github.com — a different API surface, self-hosted by
   the customer, and a real engineering item rather than a configuration flag. A competitor lists
   it; assume it will be asked for.
7. Retention controls, and contractual no-training in writing. **A custom DPA has legal lead
   time** and is not an engineering task.
8. SLA measurement before an SLA is offered. **We do not have latency numbers**, and the rule
   against performance claims without measurement applies hardest in a contract.

### Gate

A full security questionnaire answered **from the running system**, not from a document. Every
answer demonstrable.

**Known-answer test:** attempt to modify an audit-log entry through any application path. It must
be impossible, and the attempt must itself be logged.

---

## Where these sit in the order

**All four are gated behind the ranker**, and three of the four should wait for a customer who is
actually blocked on them:

| Stage | Trigger | Why not sooner |
|---|---|---|
| **Budget ceiling** | **before the first paid seat** | It is not a feature, it is what makes the price true |
| Identity and org view | first Business prospect with two repositories | The schema change wants doing before there is data to migrate |
| BYO key and certification | first prospect blocked on compliance | Each provider is a maintained integration; build them one customer at a time |
| Procurement surface | **SOC 2 readiness on the decision to target enterprise; the rest on the first questionnaire** | The report needs a three-to-six-month observation window, so triggering on the questionnaire loses that deal |

**Only the budget ceiling is unconditional.** The rest are sold on the price list and built when
someone tries to buy them — which is the honest way to run a four-tier table with no customers
yet, provided the table does not promise a delivery date.

---

# Order, and what would make us stop

| Stage | Ships | Stop condition |
|---|---|---|
| Skeleton | week 1 | — |
| Reader | weeks 2–3 | conservation invariant cannot be made to hold |
| **Ranker (3a)** | weeks 4–5 | **does not reproduce within tolerance — stop and re-examine the research** |
| Allocation instrumented (3b, 3c) | with first live traffic | cost counts one call not three; or function-level miss rate is unstated |
| Free tier | week 6 | coverage line cannot be made accurate by hand audit |
| Retrospective | weeks 7–8 | report contradicts the hand audit |
| Allocate/infer/verify | weeks 9–11 | cost exceeds uniform review, or drop rate is 0% or 100% |
| Serve | week 12 | duplicate comments cannot be eliminated |
| Telemetry | with each stage | — |
| **Budget ceiling** | **before the first paid seat** | **degrades to an outage instead of coverage-only** |
| Billing and integrations | after ten paying repositories | — |
| Identity and org view | first two-repository prospect | org report disagrees with the per-repository sum |
| BYO key and certification | first compliance-blocked prospect | every model certifies, so certification measures nothing |
| Procurement surface | SOC 2 on targeting enterprise; rest on first questionnaire | audit log is modifiable through any application path |

**The ranker gate is the one that can end the project**, and it is deliberately placed before
any hosting, any billing, and any model spend. If the productionised ranker does not reproduce,
everything after it is built on a number that did not survive contact with the product.

---

# What this plan does not resolve

**Whether anyone will pay.** Unchanged by any amount of building, and still the largest risk.

**Whether the tool survives thirty days on a team with no stake in it** — and this is the
necessary condition, which the plan had wrong for most of its life.

It specified: does a reviewer shown the routing line catch anything they otherwise would miss.
That is the right *upside* question and the wrong *necessary* one. **If the reviewer is the
distribution mechanism for the measurement layer, what has to be true of it is that it gets
installed and left on.** A reviewer firing on 10–12% and largely ignored still writes
`ranked_unit`, `shadow_pick` and `outcome` rows on every pull request, and those rows are the
asset. **Being ignored does not destroy it. Being uninstalled does.**

| | Question | Cost |
|---|---|---|
| **Necessary** | does it survive 30 days on an uninvested team? | an install date, a disable event, and the rows in between — data already collected |
| **Upside** | does a reviewer shown the routing line catch or clear anything they otherwise would not? | measure alongside; a null here is survivable |

**Both come from the same month**, which is why specifying only the second was expensive: a null
on routing efficacy would have read as a failure of the company when it is a failure of the
upside. Every number in this corpus is retrospective and no amount of history substitutes for
either measurement.

### What a null means, written down before the month starts

**Recorded in advance so the post-hoc reading is constrained.** The old framing is easy to let
back in once the month is over and somebody asks "did it work".

| Result | Reading, fixed now |
|---|---|
| Routing null, survival holds | **The upside did not land.** The asset still accrues on every pull request. Not a failure of the company |
| **Survival null** | **That is the company.** No amount of routing efficacy compensates for a tool that gets switched off |
| Both hold | Proceed, and the routing magnitude is worth publishing |

### Survival has to be defined as more than "not uninstalled"

**A team that mutes the bot, filters its comments, or stops reading them has abandoned it, and
none of that appears as a disable event.** The schema is being written now, so this is the moment
to decide what counts.

**`reaction` volume is the signal.** Reviews still posting while reactions fall to zero is
abandonment without uninstallation, and it is the failure mode a naive install-count metric would
report as success — the same shape as every other check in this plan.

**Exit criterion: survived AND still generating reaction volume at day 30.** Not survived alone.

**Zero reactions is unresolved, not failed.** A careful reader who never clicks is
indistinguishable in the data from someone who stopped looking — the metric captures
interaction, not attention. **So accept the asymmetry rather than pretending to fix it: nonzero
reactions is positive evidence of engagement, zero is no evidence either way.** A zero-reaction
team is recorded as unresolved, which shrinks the denominator honestly and still gives a decisive
answer if most teams land on the clean side.

**And ask, once, at day 30.** Three questions by email to any team showing zero reactions. Not a
survey programme — a single message resolving the one ambiguity the instrumentation cannot.
**This is the only place in the plan where self-report is the right instrument**, because the
quantity is a mental state and no row records it.

**This criterion was written in conversation, not derived from a measurement**, and it will be
tempting to soften at day 30 if the number is close. That is why the readings above are fixed in
advance — and knowing *why* they were fixed is the part that has to survive with them.

**And check again at 90 days.** Thirty days may be short for a decision in either direction — a
team that keeps it for a month and drops it in week seven has said something the experiment as
specified would not capture. Not a reason to delay the month, a reason not to close the question
when it ends.

**Whether function-level ranking transfers from the file-level research.** Named as the largest
technical risk, measured at the ranker gate, and it has no mitigation beyond measuring it early.
