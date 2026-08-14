# Signal search log — every candidate tried, 2026-08-12

**Purpose: so nobody runs these again.** Thirteen candidate pre-merge signals were tested
against breakage in the agent corpus in one session. This file records all of them, including
the ones that failed and the two occasions the harness itself was wrong. Detailed analysis of
the co-change result is in `HISTORY_SIGNAL_BACKTEST_2026-08.md`.

Nothing here is a product recommendation. It is the evidence a plan should be written from.

---

## Populations and labels

| Set | n | Provenance |
|---|---|---|
| Analysable pull requests | **215** | `graph_status == "ok"` with a symbol list, across `results/exposure_*.jsonl`, deduplicated by `pr_id` |
| BROKE — file rule | **49** | `a54_confound.json`, the standard file-overlap attribution |
| BROKE — symbol rule (corrected) | **16** | subset of the above with non-zero symbol overlap |
| Repositories, analysable set | **97** | — |
| Repositories containing a symbol-rule breakage | **10** | the within-repo backtest population |
| Within-repo backtest set | **41** | 16 broke, 25 clean, in those 10 repositories |
| Pull requests with GitHub metadata | **215 of 215** | `data/gh_cache/pr-*.json` |

The file rule is wrong on 67.9% of its verdicts (36 of 53 share no symbol with the pull
request), so it is used **only as a larger, noisier discovery set**, with the 16 corrected
labels held back for validation.

---

## The thirteen signals

### Structural and historical

| # | Signal | Result | Verdict |
|---|---|---|---|
| 1 | **Call-site coverage** — any call site with no static callee name | RR **0.916**, CI [0.557, 1.505], fires on 45.0% | **Null** (prior work, `COVERAGE_GATE_NULL_2026-08.md`) |
| 2 | **Co-change companion missing** — a changed file's historical partner absent from the diff | fires **8/16** broke vs **2/25** clean, Fisher **p = 0.0066** | **Discriminates — but localises 0 of 8** |
| 3 | **Fix-history hotspot** — a changed file has ≥2 fix-labelled commits in the prior 180 days | catch 9/16 = 56.2%, fires on 9/25 = 36.0% clean, RR **1.56**, p = 0.334 | **Null, and far too noisy** |

Signal 2 at other thresholds, for completeness: loose (support ≥2, confidence ≥0.5) gives
8/16 against 10/25 — RR 1.25, useless. Tight (≥5, ≥0.75) gives 2/16 against 0/25 — fires too
rarely to evaluate.

### Pull-request metadata — all ten, both label sets

Median split on each feature. **Bonferroni factor 10.**

**Discovery, file-rule labels (49 events of 215):**

| Signal | High half | Low half | RR | p | p×10 |
|---|---|---|---|---|---|
| additions per commit | 33/107 = 30.8% | 16/108 = 14.8% | **2.08** | 0.0058 | 0.058 |
| additions | 33/107 = 30.8% | 16/108 = 14.8% | **2.08** | 0.0058 | 0.058 |
| changed files | 32/106 = 30.2% | 17/109 = 15.6% | 1.94 | 0.0144 | 0.144 |
| deletions | 32/106 = 30.2% | 17/109 = 15.6% | 1.94 | 0.0144 | 0.144 |
| churn | 32/107 = 29.9% | 17/108 = 15.7% | 1.90 | 0.0150 | 0.150 |
| commits | 22/83 = 26.5% | 27/132 = 20.5% | 1.30 | 0.320 | 1.000 |
| comments | 20/81 = 24.7% | 29/134 = 21.6% | 1.14 | 0.618 | 1.000 |
| time to merge | 26/107 = 24.3% | 23/108 = 21.3% | 1.14 | 0.629 | 1.000 |
| deletion ratio | 23/107 = 21.5% | 26/108 = 24.1% | 0.89 | 0.746 | 1.000 |
| review comments | 9/43 = 20.9% | 40/172 = 23.3% | 0.90 | 0.841 | 1.000 |

**Validation, symbol-rule labels (16 events of 215):**

| Signal | High half | Low half | RR | p | p×10 |
|---|---|---|---|---|---|
| comments | 2/81 = 2.5% | 14/134 = 10.4% | **0.24** | 0.033 | 0.331 |
| deletions | 11/106 = 10.4% | 5/109 = 4.6% | 2.26 | 0.124 | 1.000 |
| additions per commit | 11/107 = 10.3% | 5/108 = 4.6% | 2.22 | 0.128 | 1.000 |
| changed files | 10/106 = 9.4% | 6/109 = 5.5% | 1.71 | 0.308 | 1.000 |
| additions | 10/107 = 9.3% | 6/108 = 5.6% | 1.68 | 0.312 | 1.000 |
| time to merge | 6/107 = 5.6% | 10/108 = 9.3% | 0.61 | 0.437 | 1.000 |
| review comments | 4/43 = 9.3% | 12/172 = 7.0% | 1.33 | 0.533 | 1.000 |
| churn | 9/107 = 8.4% | 7/108 = 6.5% | 1.30 | 0.615 | 1.000 |
| commits | 6/83 = 7.2% | 10/132 = 7.6% | 0.95 | 1.000 | 1.000 |
| deletion ratio | 8/107 = 7.5% | 8/108 = 7.4% | 1.01 | 1.000 | 1.000 |

---

## What survives thirteen attempts

**Nothing survives Bonferroni correction on either label set.**

**Size replicates in direction and magnitude across both**, which no other candidate does:
RR ≈ 2.1 on the discovery set and RR ≈ 1.7–2.3 on the validation set, same sign, for
additions, deletions, changed files and churn.

That is the oldest result in defect prediction, and **it is already a shipping feature in
every competitor** — the then-current product plan listed `max_changed_lines` and `max_files`
among the conditions Mergify's `auto_merge_conditions` has expressed since 2026-05-06. It is
a true signal and not a differentiator.

**One inversion worth naming rather than burying.** On the corrected labels, pull requests
with **any** discussion comment broke at 2.5% against 10.4% for silent ones — RR 0.24,
p = 0.033 uncorrected, which does not survive Bonferroni and runs opposite to the discovery
set. Treat as noise unless it replicates; it is recorded because a later run finding the same
thing should know it appeared here first.

---

## Why the search failed, measured rather than assumed

For each genuine breakage, the fix commit's files split into those the pull request had
already changed and those it had not:

| Class | Count |
|---|---|
| **SELF** — the fix only re-touched files the pull request changed | **5 of 11** |
| **MIXED** — re-touched changed files **and** added new ones | **6 of 11** |
| **COMPANION** — only touched files the pull request did not | **0 of 11** |

**Every breakage required re-editing a file the pull request had already changed.** The
defects are wrong logic, not missing structure — which is why no signal about *which files
are involved* can localise them. Published work agrees: semantic errors account for over 60%
of faults in model-generated code, and AI-assisted generation produces roughly 1.7× more
logic and correctness bugs.

**The ceiling for any companion-change product on this corpus is 6 of 11**, and even those
six also required editing a file already in the diff.

---

## Harness verification, and the two times it was wrong

A green number is not a verified number. What was checked, and what broke:

1. **No-lookahead, asserted.** `git merge-base --is-ancestor merged_sha parent_sha` on all 41
   pull requests. **Zero leaks.**
2. **Sabotage.** History rebuilt from `merged_sha` moved the catch rate 50.0% → 37.5%, so the
   ancestry bound is load-bearing. **This is a weak sabotage** — it does not prove the harness
   would catch a signal built from the fix commits themselves. Still owed.
3. **Known-answer test.** The same signal, same code path, on **ordinary** commits: predicted
   a held-out file **22 of 52 times it fired — 42.3%**, against **0 of 8** on defect fixes,
   Fisher **p = 0.0218**. The instrument works; the zero is a real negative.
4. **A run was discarded.** The first bounded run analysed 34 pull requests against the
   sabotage run's 39 — three repositories finished cloning between them. Both re-run on an
   identical 41. **The discarded numbers were not used.**
5. **A truncation was caught.** The first localisation check compared only the top 3
   predictions per pull request. Re-run against all predictions: still 0 of 8.
6. **A dead check was caught.** The hotspot signal first returned zero at every threshold —
   identical output whether or not the signal existed. Cause: a 180-day window expressed
   relative to today while the history walked was ancestral to a 2025 commit, so no commit
   could satisfy both. A sanity counter now prints in-window commits found: **0 before the
   fix, 1,298 after.**

---

## The fourteenth and fifteenth signals — one of them works

The diagnostic said the fix lands **inside the files the pull request already changed**. That
makes the answerable question not *"which file is missing"* but ***"which of the files you
just changed will the fix come back to."*** That target had not been tested.

### Signal 14 — test-coverage gap. Null.

Pull request changes source and no test file:

| Labels | Broke | Clean | RR | p |
|---|---|---|---|---|
| symbol-rule | 10/16 = 62.5% | 55/80 = 68.8% | 0.91 | 0.770 |
| file-rule | 28/48 = 58.3% | 37/48 = 77.1% | 0.76 | 0.080 |

Null, and the direction is **backwards** — pull requests that changed no test broke slightly
*less*. Dead.

### Signal 15 — rank the pull request's own changed files. **This one replicates.**

Rank the changed files by how many commits touched them in the year before the pull request,
and ask whether the **top-ranked file** is one the fix commit re-touches.

| Ranker | Corrected labels | Discovery labels |
|---|---|---|
| **prior commits (1 year)** | **9 of 9 — 100%** | **17 of 30 — 56.7%** |
| prior fix-labelled commits | 8 of 9 — 88.9% | 16 of 30 — 53.3% |
| lines changed in this pull request | 3 of 9 — 33.3% | 7 of 30 — 23.3% |
| alphabetical (null ranker) | 4 of 9 — 44.4% | 11 of 30 — 36.7% |
| **random baseline** | **46.5%** | **35.2%** |

```
corrected  : 9/9  observed, 4.2 expected   exact Poisson-binomial P(X>=9)  = 0.00042
discovery  : 17/30 observed, 10.6 expected  exact Poisson-binomial P(X>=17) = 0.00638
```

**Everything that could have made this an artefact was checked and did not:**

- **The null ranker sits at baseline** — alphabetical scores 44.4% and 36.7% against baselines
  of 46.5% and 35.2%. The harness is calibrated.
- **Not degenerate** — in 0 of 39 pull requests did every candidate file have identical
  history, so the ranker is always making a real choice.
- **Not one repository** — the discovery set spans **20 repositories**. Dropping the largest
  contributor leaves 14 of 27 = 51.9% against a 34.7% baseline; on the corrected set, 6 of 6.
- **Replicates across two independently derived label sets**, one of which is 68% noise.
- **It is not "the biggest edit."** Ranking by lines changed in the pull request scores
  **worse than random** — 33.3% against 46.5%. The predictive file is the historically active
  one, not the heavily edited one.

### What it is, stated precisely

It predicts **where** a fix will land, **conditional on something breaking**. It does *not*
predict whether a pull request will break — that was signal 3, the hotspot, and it was null
at RR 1.56. The two results are consistent: file activity carries no information about
whether a change is wrong, and substantial information about which file gets revisited.

**This is a review-attention router, not a defect detector.** Its honest output is *"of the
six files here, start with this one"*, and in production its precision is bounded by the base
rate of breakage — roughly a fifth to a quarter of pull requests in this corpus.

**And it is cheap to copy.** It is `git log --since=1.year -- <file>` counted per changed
file and sorted. There is no algorithmic moat. What nobody does is **put it in the pull
request**, which is a distribution claim rather than a technical one, and it should be
described that way rather than dressed up.

---

## Scaling signal 15 to big repositories

The ranker needs only a change, its files, and a later fix — not the exposure pipeline. So it
can be tested on **ordinary commit history at scale**: for every commit touching 2 to 12
Python files, look forward 90 days for a fix-labelled commit that re-touches one of them, and
ask whether the top-ranked file is one it returns to. History used for ranking is strictly
earlier than the commit being ranked.

| | |
|---|---|
| Repositories | **17** |
| Events | **4,293** |
| **prior-commits ranker** | **3,660 of 4,293 — 85.3%** |
| alphabetical null ranker | 3,093 of 4,293 — 72.0% |
| random baseline | 67.5% |
| **Repositories where the ranker beats its null** | **17 of 17** |

Sign test on repository-level direction: **p ≈ 1.5 × 10⁻⁵**. Per-repository margins over the
null run from +2.0 points to +34.0. It holds in `Z3Prover/z3`, `browser-use/browser-use`,
`cartography-cncf/cartography` and `commaai/opendbc` — production codebases, not toys.

**Caveat that matters.** This population is ordinary commits with a keyword-matched fix
heuristic, not agent-authored pull requests with corrected labels. It is a much larger and
independent test of the same mechanism, not a bigger version of the same study. The two
populations agree in direction; only the corrected-label study carries the label quality.

---

## The call-graph proxy — void, then weak

**First run was a dead check.** Reference lookup used `git grep` at a historical commit
inside a blobless clone, which fails with `fatal: You are attempting to fetch...`; the error
was swallowed and returned an empty reference set. It reported 0 of 6 while measuring
nothing. Four of six repositories showed zero references across the whole tree, including one
with 2,841 Python files — the tell.

**Rerun** with each parent commit materialised in a worktree so blobs exist:

| | |
|---|---|
| MIXED breakages evaluated | 5 (airbyte excluded for clone size) |
| Located a new fix file | **1** |
| Cost | the reference set averages **19% of the repository's Python files** |

Weak. Flagging a fifth of a codebase to find one file in five is not a finding a developer
can act on. It is a **textual reference proxy, not the real call graph**, so a PyCG-based
version remains formally untested — but it would have to be dramatically better than this to
matter, and the self-fix ceiling caps it at 6 of 11 regardless.

One case is genuine rather than instrumental: Gemini-FastAPI shows zero references across 17
files **with blobs present**. In a small service the changed symbols really are referenced
nowhere else.

---

## What has not been tested

- **Symbol-level structural localisation.** Callers and dependents of the changed function
  from the call graph, rather than statistical co-change. The Skyvern breakage was fixed in
  three files that plausibly call the changed one. Untested, and capped at 6 of 11 by the
  self-fix result above.
- **Test-coverage gap** — changed code with no covering test. Fix commits in this corpus did
  touch tests.
- **Anything requiring a model.** Excluded by the no-inference decision in
  the then-current product plan, and the defect class measured here is precisely the one that
  needs it.

---

## Scale reached

Live clones of **29 repositories** pulled during this session, 215 analysable pull requests,
148 additional ordinary commits used for the known-answer test. Every number above was
produced in one session; the population is small and every interval is wide.
