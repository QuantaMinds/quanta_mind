# Phase 0 Runbook — Executable Protocol

> Companion to `PHASE0_PREREGISTRATION.md`. That file fixes **what** we measure and the
> thresholds. This file is **how**, day by day, with the expected output at every step and
> what to do when a step produces something unexpected.
>
> **Scope: Python and TypeScript/JavaScript only.** No other language until both arms
> report. See §8.
>
> **The single rule that makes this study worth running:** you must prove the instrument
> can detect a positive *before* you are allowed to believe a null. §2 is not optional.

---

## 0. Prerequisites

```bash
mkdir -p phase0 && cd phase0
uv init && uv add pandas scipy statsmodels tree-sitter tree-sitter-python \
                  tree-sitter-typescript gitpython pyyaml
uv add --dev pytest pytest-timeout hypothesis
pip install pycg --break-system-packages      # archived, pinned, MIT
```

Pin everything. Record versions in `phase0/ENVIRONMENT.lock`. A study you cannot re-run is
a study you cannot defend.

**Harness layout** — each module ≤200 lines, each with its own test file:

```
scripts/phase0/
  extract_prs.py       AIDev  → PRRecord[]
  census.py            source → CallSite[]        (tree-sitter, the denominator)
  run_graph.py         repo   → Edge[]            (PyCG / Jelly, scoped)
  classify_exposure.py PR     → EXPOSED | UNEXPOSED | UNANALYZED
  scan_outcome.py      PR     → BROKE | CLEAN     (7-day revert/fix scan)
  controls.py          positive + negative controls  ← §2
  build_table.py       → 2×2, RR, CI, strata
tests/phase0/          one test file per module above
```

---

## 1. Day 1 — Build the harness, test the harness

**Nothing is run against real data until every test below passes.** A measurement
instrument you have not tested produces numbers you cannot interpret.

### 1.1 Census tests (`tests/phase0/test_census.py`)

The denominator is the number everything else divides by. Get it wrong and every result is
wrong by a constant nobody can see.

| Test | Input | Expected | Why |
|---|---|---|---|
| `test_counts_direct_calls` | `foo(); bar()` | 2 | baseline |
| `test_counts_method_calls` | `obj.method()` | 1 | attribute calls count |
| `test_counts_chained` | `a().b().c()` | 3 | each link is a site |
| `test_counts_in_comprehension` | `[f(x) for x in y]` | 1 | easy to miss |
| `test_counts_decorators` | `@dec\ndef f(): ...` | 1 | decorator application is a call |
| `test_excludes_builtins` | `"a".strip(); len(x)` | 0 | **DyPyBench: ~59% of the apparent gap** |
| `test_counts_super` | `super().validate(r)` | 1 | PyCG misses these; we must still count them |
| `test_hand_count_200_line_fixture` | real file | exact match | the gate |

**Gate:** hand-count a real 200-line file. Automated count must match **exactly**. Not
approximately. If it does not, find out why before proceeding — an off-by-N in the
denominator is invisible in every downstream number.

### 1.2 Exposure classifier tests (`tests/phase0/test_classify_exposure.py`)

| Test | Setup | Expected |
|---|---|---|
| `test_all_resolved_is_unexposed` | symbol with 3 sites, PyCG resolves 3 | `UNEXPOSED` |
| `test_one_unresolved_is_exposed` | 3 sites, PyCG resolves 2 | `EXPOSED` |
| `test_timeout_is_unanalyzed` | PyCG times out on the file | `UNANALYZED` (**third arm, never merged into EXPOSED**) |
| `test_oom_is_unanalyzed` | PyCG OOMs | `UNANALYZED` |
| `test_uses_parent_commit_only` | merged state resolves, parent does not | `EXPOSED` |

That last one is the leakage test. **Classifying against the merged state leaks the
outcome into the exposure** and produces a spurious correlation. It is the single most
likely way to fake a positive result by accident.

### 1.3 Outcome classifier tests (`tests/phase0/test_scan_outcome.py`)

| Test | Setup | Expected |
|---|---|---|
| `test_revert_commit_detected` | `git revert` of the PR within 7d | `BROKE` |
| `test_fix_commit_same_file` | commit +2d, same file, msg "fix crash" | `BROKE` |
| `test_unrelated_fix_different_file` | commit +2d, "fix", other file | `CLEAN` |
| `test_fix_outside_window` | commit +9d | `CLEAN` |
| `test_refactor_is_not_a_fix` | commit +1d, msg "refactor" | `CLEAN` |
| `test_case_insensitive` | msg "FIX: broken" | `BROKE` |

### 1.4 The 20-PR hand-labelling gate

Sample 20 merged agent PRs at random. **Read them yourself.** Decide BROKE or CLEAN as a
human. Then run the classifier.

**Gate: ≥16 of 20 agreement (80%).**

If below 16, the outcome variable is unreliable and so is the whole study. Iterate on the
classifier, and **record how many iterations it took in the results.** Three iterations is
tuning; ten is fitting the classifier to your hopes.

> Do the hand-labelling **before** you look at any classifier output. Once you have seen
> the machine's answer you cannot un-see it, and your "independent" labels are anchored.

---

## 2. Day 2 — Controls. The step everyone skips.

You cannot interpret a null result from an instrument you have not shown can produce a
positive. This day exists to earn the right to believe your own answer.

### 2.1 Positive control — plant breakage, prove we detect it

Construct 30 synthetic PRs on a real repository (Django fixture) where breakage **is**
caused by an unresolvable edge:

1. Add a subclass calling `super().method()` — PyCG misses it entirely (DyPyBench §4.1.2)
2. Change the base method's signature
3. Commit; the subclass now breaks
4. Commit a fix 2 days later

Interleave 30 controls where the changed symbol has only directly-resolvable callers and
the change is benign.

**Expected: RR ≥ 5 on the synthetic set.**

| Outcome | Meaning |
|---|---|
| RR ≥ 5 | Instrument works. A null on real data means something. |
| RR ≈ 1 | **The instrument is broken.** Stop. Do not run on real data — a null would be uninterpretable and you would probably believe it. |

**This is the most important gate in the entire study.**

### 2.2 Negative control — prove we do not manufacture signal

Re-run the whole pipeline with exposure replaced by a variable that cannot possibly matter:

- filename starts with a letter in a–m
- changed-file line count is even
- PR number is odd

**Expected: RR ≈ 1.0, CI comfortably spanning 1.**

If any nonsense variable shows RR > 1.5, your pipeline has a bug — most likely the outcome
scan is contaminated by something correlated with repository identity rather than with the
PR. Find it before proceeding.

### 2.3 Base-rate sanity check

The published breaking-change rates for agent PRs on Python repos are **3.45% for code
generation, 6.72% refactoring, 9.35% chore** (AIDev, AST-based detection).

Our outcome is behavioural (revert/fix ≤7d), which should catch **more** than AST detection
— it sees runtime and semantic breakage the AST method cannot.

| Observed overall breakage rate | Verdict |
|---|---|
| 5–20% | Plausible. Proceed. |
| <2% | Classifier is too strict. It is missing real breakage. Loosen and re-validate against the 20 hand-labels. |
| >40% | Classifier is too loose. It is counting ordinary follow-up commits as fixes. Tighten. |

Record the observed rate whatever it is. A rate outside 5–20% that you cannot explain is a
reason to pause, not a reason to proceed carefully.

---

## 3. Days 3–5 — The run (Python arm)

```bash
uv run python scripts/phase0/extract_prs.py \
    --dataset aidev --lang python --out data/prs.jsonl

uv run python scripts/phase0/run_pipeline.py \
    --prs data/prs.jsonl \
    --graph pycg --scoped --timeout 600 --mem-limit 16G \
    --out data/exposure.jsonl

uv run python scripts/phase0/scan_outcome.py \
    --prs data/prs.jsonl --window-days 7 \
    --out data/outcome.jsonl
```

### Expected shape and what deviation means

| Metric | Expected | If far outside |
|---|---|---|
| PRs extracted | ~7,191 total; some non-Python, some unclonable | <3,000 → extraction is dropping records silently |
| Repos successfully cloned | 80–95% | <70% → check rate limits and deleted repos |
| PyCG success rate | **~78%** — DyPyBench: 39/50 projects | Much higher → scoping is skipping code. Much lower → resource limits too tight. |
| PyCG timeout/OOM | ~22%, into `UNANALYZED` | 0% → the third arm is empty and something is wrong |
| Changed symbols per PR | 1–5 median | >20 → you are counting private helpers; restrict to public symbols |
| Exposure rate (EXPOSED share) | 10–30% | ~0% or ~100% → classifier is degenerate, stop |
| Overall breakage rate | 5–20% (§2.3) | see §2.3 |

**Log everything per PR.** `pr_id, repo, parent_sha, symbols[], call_sites, resolved,
unresolved, pycg_status, pycg_duration_ms, outcome, outcome_evidence`. The
`outcome_evidence` field — the actual commit SHA and message that triggered BROKE — is what
makes the result auditable by someone who does not trust you.

---

## 4. Day 6 — Analysis

```bash
uv run python scripts/phase0/build_table.py \
    --exposure data/exposure.jsonl \
    --outcome  data/outcome.jsonl \
    --strata changed_lines_quartile,framework_present,repo_fix_rate,test_coverage \
    --out results/phase0.json
```

### 4.1 The primary table

|  | BROKE | CLEAN |
|---|---|---|
| EXPOSED | a | b |
| UNEXPOSED | c | d |
| UNANALYZED | e | f |

`RR = [a/(a+b)] / [c/(c+d)]`, 95% CI via Katz log method.

### 4.2 Read the power first, the point estimate second

**If `a < 20`, stop reading. You have no result.** Widen the corpus and re-run. An
underpowered null reported as a negative is the most expensive mistake available here,
because it kills a live thesis on noise.

### 4.3 Verdict

| RR | CI lower | Verdict | Action |
|---|---|---|---|
| ≥ 3.0 | > 1.5 | **Strong** | Proceed to Phase 1 |
| 1.5–3.0 | > 1.0 | **Weak but real** | Proceed — but rewrite `PROJECT_CONTEXT.md §5` first. Pitch becomes "prioritise review," not "prevent breakage." |
| < 1.5 | any | **Null** | §6 |
| any | ≤ 1.0 | **No result** | §6 |

### 4.4 The `UNANALYZED` arm decides what company this is

Compute `RR_unanalyzed` separately.

| Pattern | Meaning |
|---|---|
| `RR_exposed` high, `RR_unanalyzed` ≈ 1 | **Unsoundness product.** As designed. |
| Both high | Both matter. Report both; coverage must distinguish them. |
| `RR_exposed` ≈ 1, `RR_unanalyzed` high | **You are a scalability product, not an unsoundness product.** The signal is "our tools cannot process this code," not "this code is dynamic. " Different company, different pitch. Rewrite the thesis before writing code. |

---

## 5. Authenticity checklist

Before any number leaves this document, all eight must be true.

- [ ] **Pre-registration SHA recorded** and predates the first data commit — `git log` proves it
- [ ] **Positive control passed** (§2.1, RR ≥ 5 on synthetic)
- [ ] **Negative controls passed** (§2.2, RR ≈ 1 on nonsense variables)
- [ ] **Base rate within 5–20%** or the deviation explained in writing (§2.3)
- [ ] **Exposure computed at parent commit only** — leakage test in the harness suite is green
- [ ] **Hand-label agreement ≥16/20**, with the iteration count recorded
- [ ] **`a ≥ 20`** — the study is powered
- [ ] **Full re-run from raw data reproduces the table**, on a different machine, from `ENVIRONMENT.lock`

Then publish the raw `exposure.jsonl` and `outcome.jsonl` alongside the result. If you are
not willing to publish the inputs, you do not believe the output.

---

## 6. Failure deep-dive — is this a real null or a broken study?

Work top to bottom. **Do not skip to "the thesis is wrong" — that is the last node, not the
first.** Every branch above it is a bug in us, not a fact about the world.

```
Null or no result
│
├─ Q1. Did the positive control pass? (§2.1)
│   └─ NO → INSTRUMENT BROKEN. The null means nothing. Fix and re-run.
│           Usual causes: exposure computed post-merge; symbol identity
│           mismatch between census and graph; outcome scan on the wrong branch.
│
├─ Q2. Is a ≥ 20?
│   └─ NO → UNDERPOWERED. Not a null. Widen: more repos, 14-day window,
│           include human PRs as an additional arm. Re-run.
│
├─ Q3. Is the breakage base rate 5–20%?
│   └─ NO → OUTCOME CLASSIFIER WRONG.
│           <2%: only catching literal `git revert`. Add fix-commit heuristics,
│                issue links, CI status flips.
│           >40%: counting routine follow-ups. Require file overlap AND
│                message match AND no intervening feature commit.
│           Re-validate against the 20 hand-labels, then re-run.
│
├─ Q4. Is the exposure rate 10–30%?
│   └─ NO → EXPOSURE CLASSIFIER DEGENERATE.
│           ~0%: PyCG is being credited with resolutions it did not make —
│                check that unresolved sites are counted, not silently dropped.
│           ~100%: the census is finding sites PyCG never sees (builtins?
│                  test files? vendored code?). Check exclusions.
│
├─ Q5. Does any stratum show RR ≥ 3 while the pooled RR is ~1?
│   └─ YES → SIMPSON'S PARADOX / NARROWER MARKET.
│           The effect is real but conditional. Most likely stratum:
│           framework-heavy repos. That is not a null — it is a smaller,
│           sharper market. Re-scope the product to that stratum and say so
│           explicitly in PROJECT_CONTEXT.md. Do not report it as a general result.
│
├─ Q6. Do primary (behavioural) and tertiary (AST) outcomes disagree sharply?
│   └─ YES → PUBLISHABLE FINDING regardless of the commercial answer.
│           It means AI-authored breakage is systematically under-measured by
│           AST-based methods. Write it up. It is an original contribution and
│           it is true whether or not we build anything.
│
├─ Q7. Is the effect concentrated entirely in UNANALYZED? (§4.4)
│   └─ YES → WRONG PRODUCT, NOT WRONG THESIS. Scalability, not unsoundness.
│           Rewrite the thesis before writing code.
│
└─ Q8. All the above clean, RR still ≈ 1?
    └─ TRUE NULL. The label does not predict breakage.
        STOP. Publish. Do not add resolvers and re-run hoping for a better
        number — adding resolvers shrinks the exposed group and can only move
        RR toward 1, never away from it. There is no rescue path from here
        and looking for one is how six weeks get spent.
```

### Two rescue attempts that are forbidden

1. **Switching to the AST-based outcome because it gives a nicer number.** It is
   contaminated by construction; that is why it was rejected in the pre-registration.
2. **Dropping repos where the result was unfavourable.** If you must subset, it is a
   pre-specified stratum (Q5) or it is nothing.

If either becomes tempting, that is the signal to stop, not to continue.

---

## 7. TS/JS arm — run after Python reports

Same protocol, three substitutions. Run it **only after** the Python arm has a verdict, so
that a broken harness is diagnosed once rather than twice.

| Component | Python | TS/JS |
|---|---|---|
| Graph | PyCG (archived, MIT) | **Jelly**, `js-callgraph`, or TAJS — JCG ships adapters for all three |
| Census | tree-sitter-python | tree-sitter-typescript |
| Builtin exclusion | `str.*`, `len`, `super` | `Array.prototype.*`, `Object.*`, `console.*` |

### Three TS/JS-specific hazards

**The bundler boundary.** Webpack/Vite/esbuild rewrite module resolution before execution.
An import graph read from source can be structurally wrong about what actually loads. Add a
fourth arm: `EXPOSED_BUNDLER` for symbols crossing an alias or dynamic `import()`. If this
arm dominates, TS/JS is a *different* product from Python.

**Types are not safety.** The manifesto is explicit that TypeScript's type system is
unsound but practically useful. Do not treat `.ts` files as pre-resolved.

**ES6+ coverage.** TAJS specifically was found to underperform on contemporary code despite
high precision on classic benchmarks. Check your graph tool's ES version support before
trusting its resolution rate — a tool that silently skips modern syntax will look like it
resolved everything.

### TS/JS gate

Same thresholds. **Additional check:** exposure rate should be **higher** than Python's,
because JS has a larger unsoundness surface (`eval`, prototype mutation, dynamic property
access, DOM, bundlers). If it comes out *lower*, your graph tool is over-claiming and the
whole arm is suspect.

---

## 8. Deliverables

| File | Contents |
|---|---|
| `results/phase0-python.json` | raw 2×2, RR, CI, all strata |
| `results/phase0-typescript.json` | same |
| `results/controls.json` | positive and negative control results |
| `data/exposure.jsonl`, `data/outcome.jsonl` | raw per-PR records, published |
| `ENVIRONMENT.lock` | every pinned version |
| `PHASE0_PREREGISTRATION.md §8` | filled and signed |
| `docs/findings/phase0-writeup.md` | the narrative, **including the failure path taken if any** |

The writeup is written **whatever the answer is.** A null with clean controls is a real
scientific result, an O-1A original-contribution artifact, and an honest close to a
question that would otherwise be rediscovered in six months.

---

## 9. Timeline

| Day | Work | Gate to proceed |
|---|---|---|
| 1 | Harness + tests | all harness tests green; hand-count exact |
| 2 | Controls | positive RR ≥ 5; negatives ≈ 1; base rate 5–20%; hand-labels ≥16/20 |
| 3–5 | Python run | PyCG success ~78%; exposure 10–30% |
| 6 | Analysis | `a ≥ 20` |
| 7 | Verdict + writeup | authenticity checklist 8/8 |
| 8–12 | TS/JS arm | same gates |

**Two weeks total for both languages. No product code in either week.**
