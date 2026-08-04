# Phase 0 Pre-Registration — Does Unresolved Predict Breakage?

> **Status: PRE-REGISTERED. Not yet run.**
>
> This file is committed **before** any data is touched. Its purpose is to remove our own
> discretion from the result. Everything below — the outcome variable, the exposure
> variable, the threshold, and the stop rule — is fixed at commit time.
>
> **Amending this file after data collection begins requires a PR that states what was
> changed, why, and who approved it.** An unamended, unexplained change to the threshold
> is research misconduct on ourselves.
>
> Commit this file. Note the SHA. Then start.

---

## 1. The question

Does the label `unresolved` carry predictive information about whether an AI-authored code
change breaks something?

If yes, the product exists. If no, the labels are decorative and QuantaMind Context should
not be built. There is no third outcome, and no amount of engineering elsewhere rescues a
null result.

## 2. Why this must run first

Everything in `ARCHITECTURE.md` and `docs/BUILD_PLAN.md` Phases 1+ assumes this
correlation. Building any of it before measuring is the failure mode we have already paid
for once: a real problem, a plausible mechanism, and no evidence anyone bleeds from it.

**No product code is written until this file has a Results section.**

---

## 3. Design

Retrospective cohort study over AI-authored pull requests.

- **Unit of analysis:** one changed public symbol within one agent-authored PR.
  Not one PR — a PR may change ten symbols with different exposure.
- **Population:** agent-authored PRs in Python repositories from the AIDev dataset
  (~7,191 agent PRs). Human PRs (~1,402) are the comparison arm in the secondary analysis.
- **Design:** 2×2 contingency table, relative risk with a 95% confidence interval.

### 3.1 Exposure variable — fixed

At the **parent commit** of the PR (never the merged state — that leaks the outcome):

Run **vanilla PyCG, entry-point scoped, no custom resolvers.**

For each changed symbol `S`, enumerate every call site referring to `S` and classify:

- **EXPOSED** — one or more call sites referring to `S` exist that PyCG did not resolve,
  or `S` sits in a file PyCG timed out / OOM'd on.
- **UNEXPOSED** — every call site referring to `S` was resolved by PyCG.

**Why vanilla PyCG and not our labeler:** this is the *crudest* instrument available, and
crudeness is the conservative choice. Adding resolvers can only move sites from exposed to
unexposed, shrinking the exposed group. **If the crude instrument shows no lift, a better
instrument cannot manufacture one.** This also dissolves the chicken-and-egg — the test
does not depend on any code we have not written.

Builtin call sites are excluded from both arms. Per DyPyBench they are ~59% of the apparent
static/dynamic gap and are irrelevant to a developer.

### 3.2 Outcome variable — fixed, and deliberately NOT AST-based

**Primary outcome: a revert or fix commit touching the changed file within 7 days of merge.**

Operationalised as any commit in the 7 days following merge that:
- reverts the PR's commit (git revert, or a commit message matching `revert`), **or**
- modifies a file the PR modified **and** whose message matches
  `fix|bug|broke|regress|hotfix|revert` (case-insensitive), **or**
- is linked to an issue opened within 7 days that references the PR

**Why not the AIDev breaking-change labels.** The published study
<cite index="358-1">"leverages an abstract syntax tree (AST) based analysis to detect potential breaking
changes."</cite> AST-based detection can only observe breakage at statically resolvable
sites. Using it as ground truth would make the outcome variable **structurally blind to
exactly the breakage this thesis is about**, producing a false null. The ruler cannot
measure the thing.

Revert-and-fix signals are noisier and are produced by humans reacting to real failures,
independent of any static analysis. Noisy and independent beats clean and contaminated.

**Secondary outcome (recorded, not decisive):** CI status flip — green at merge, red on the
next run of the same workflow.

**Tertiary (recorded for comparison only):** the AIDev AST-based label. If our primary and
this one disagree, that disagreement is itself a publishable finding about how breakage in
AI-authored code is under-measured.

### 3.3 The table

|  | broke (revert/fix ≤7d) | did not break |
|---|---|---|
| **EXPOSED** (≥1 unresolved call site) | a | b |
| **UNEXPOSED** (all call sites resolved) | c | d |

**Relative risk** = `[a / (a + b)] / [c / (c + d)]`, reported with a 95% CI.

A raw count of "how many breakages were at unresolved sites" is **explicitly rejected as
an analysis.** With ~15% of call sites unresolved, 15% of breakages at unresolved sites is
zero signal that looks like confirmation. Only the ratio carries information.

---

## 4. Decision thresholds — fixed before data

| Result | Verdict | Action |
|---|---|---|
| **RR ≥ 3.0**, CI lower bound > 1.5 | Strong | Proceed to Phase 1. The label predicts breakage. |
| **RR 1.5 – 3.0**, CI excludes 1 | Weak but real | Proceed, **but the pitch changes** from "we prevent breakage" to "we prioritise review attention." Re-do the business case in `PROJECT_CONTEXT.md §5` before building. |
| **RR < 1.5** or **CI includes 1.0** | Null / underpowered | **Stop.** See §6. |

### Power

Target ≥ 200 EXPOSED symbols with an observed breakage rate ≥ 5%. If `a < 20`, the
confidence interval will span 1.0 regardless of the point estimate. **That is not a
negative result — it is no result**, and reporting it as a negative would be as dishonest
as reporting it as a positive. Widen the corpus (more repos, longer window) before
concluding anything.

Record the achieved `a` in the Results section whatever happens.

---

## 5. Pre-specified confounders

Recorded now so that adjusting for them later is not a post-hoc rescue attempt.

| Confounder | Why it threatens the result | Handling |
|---|---|---|
| **Complexity** — dynamic code is harder code, and harder code breaks more regardless | Would inflate RR through a path that has nothing to do with our labels | Stratify by changed-lines quartile. Report RR per stratum. |
| **Framework density** — Django/Celery repos have both more unresolved sites and more coupling | Same inflation | Stratify by framework presence. |
| **Repo activity** — busy repos produce more fix commits by base rate | Inflates the outcome in both arms unevenly | Normalise by the repo's 30-day fix-commit rate. |
| **Test coverage** — well-tested repos catch breakage before merge | Suppresses the outcome | Record coverage where available; report as a stratum. |
| **PyCG failure ≠ dynamism** — a timeout is a tooling limit, not a property of the code | Conflates two different exposures | Report `UNANALYZED` (timeout/OOM) as a **separate third arm**, not merged into EXPOSED. |

The third row of that last one matters: if the entire effect comes from `UNANALYZED`, the
product is a scalability product, not an unsoundness product. That is a different company.

---

## 6. If the result is null

**We stop, and we publish.**

A rigorous null — *"static-analysis resolvability does not predict breakage in AI-authored
Python changes, RR = 1.1 [0.8–1.5], n = 7,191 PRs"* — is a genuine contribution. The
soundiness literature has asked since 2015 for empirical work on whether unsoundness
matters in practice, and explicitly noted that no reliable survey exists. Answering "less
than we assumed" is publishable, is an original contribution for the O-1A file, and closes
the question honestly rather than leaving it to be rediscovered in six weeks of building.

**What we do not do on a null:** add resolvers and re-run hoping for a better number,
switch to the AST-based outcome because it gives a nicer answer, or narrow the corpus to
the repos where it worked. If any of those becomes tempting, re-read this paragraph.

---

## 7. Timeline

| Day | Work |
|---|---|
| 1–2 | Commit this file. Build the extraction harness. Dry-run on 20 PRs by hand to validate the outcome classifier against human judgement. |
| 3–5 | Full run: checkout parent commits, scoped PyCG, call-site enumeration, 7-day history scan. |
| 6 | Fill the 2×2. Compute RR + CI. Stratify by the five confounders. |
| 7 | Write the Results section below. Convene the go/no-go. |

**Day 2 gate:** the outcome classifier must agree with hand-labelling on ≥16 of 20 PRs.
If it does not, the outcome variable is unreliable and the whole study is unreliable — fix
the classifier before proceeding, and record how many iterations that took.

---

## 8. Results

> **Empty. Do not fill until the run is complete. Do not start Phase 1 until this is filled.**

```
Run date:
Corpus:                     PRs,        repos,        changed symbols
Exposed (n):
Unexposed (n):
Unanalyzed (n, third arm):

                broke     did not break
EXPOSED           a=          b=
UNEXPOSED         c=          d=
UNANALYZED        e=          f=

Relative risk (exposed vs unexposed):        [95% CI:      ,      ]
Relative risk (unanalyzed vs unexposed):     [95% CI:      ,      ]

Stratified RR — changed-lines quartile:
Stratified RR — framework present / absent:
Normalised by repo fix-rate:

Primary vs tertiary outcome agreement:       %

Achieved a:                (power target was ≥20)

VERDICT:   [ ] Strong — proceed    [ ] Weak — re-pitch first    [ ] Null — stop
Signed off by:
Date:
```

---

## 9. Related open thread — close immediately after

`docs/PROJECT_CONTEXT.md` open thread **#7**: we found blogs and vendor content, not raw
practitioner complaints.

**Protocol, one week, run only after §8 is filled and non-null:**

Collect **50 verbatim complaints** from r/ExperiencedDevs, r/programming, Hacker News and
the Cursor forum. Code each one for the vocabulary the developer used:

| Code | Example phrasing |
|---|---|
| `context-window` | "it ran out of context" |
| `hallucination` | "it made up a function" |
| `missing-caller` | "it didn't know X also called this" ← **the mechanism** |
| `index-stale` | "it used the old version of the file" |
| `cost` | "it burned my whole budget" |
| `works-local-breaks-prod` | — |

**Decision rule:** if fewer than 5 of 50 use `missing-caller` language, the sales motion
begins with education. That is not fatal, but it must be priced and planned for — and it
must appear in the go-to-market section of `PROJECT_CONTEXT.md` before a single sales
conversation.

Skipping this step is what cost six weeks last time. It is one week now.
