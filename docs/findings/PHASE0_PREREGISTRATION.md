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
> Commit this file. Note the SHA. Then follow `PHASE0_RUNBOOK.md` — the executable
> protocol with harness tests, controls, expected outputs and the failure tree.
>
> **Languages in scope: Python and TypeScript/JavaScript.** The Python arm runs first;
> TS/JS repeats the identical protocol only after Python reports, so that a broken
> harness is diagnosed once rather than twice. No other language until both report.

---

## 0. Amendment log

Every change to this file after its first commit is recorded here. All amendments below
were made **before any data was touched** — the harness existed but had not been run, and
`§8 Results` was and is empty. They arise from reading the corpus schema and the source
papers, and from review of the execution plan.

**No amendment moves a decision boundary.** The RR thresholds (3.0 / 1.5), the CI rules,
the 7-day window, the `a ≥ 20` floor and the stop rule in §6 are byte-identical to the
first commit. A1–A5 are factual corrections or newly discovered prerequisites; A6–A17
change *what is measured* (A6), *how it is matched* (A9), *what is excluded* (A7), *how it
is estimated* (A8), or *what may be claimed from the result* (A10), so that all of them
match what the instrument can actually deliver.

**Every one of A6, A7, A9 and A10 was forced by a property established by running the
instrument, not by reading about it** — the set-valued edge map, the 3.10 parse ceiling,
two distinct naming defects, and a capability profile of one mechanism in four. Each is
recorded with its bias direction, and in every case the direction is toward the null. An
amendment that made a positive result *easier* would deserve far more scepticism than
these do.

**One amendment does touch the outcome definition, and it is A4.** The third of §3.2's
three BROKE criteria — the issue link — becomes conditional on API quota. The first two,
which do the overwhelming majority of the work and need no quota, are unchanged. This is
recorded here rather than filed under "factual correction" because a criterion that may or
may not execute is a real change to the outcome variable, and §3.2 now requires Results to
state whether it ran. Calling that a clarification would be exactly the kind of quiet
reclassification this log exists to prevent.

| # | § | Change | Why |
|---|---|---|---|
| **A1** | 3 | Population restated: 7,191 → 4,798 structural → ~3,300 merged. Human arm runs in the same pass. | 7,191 was the pre-filter count. The analysed population is 2.2× smaller and saying so is cheaper than discovering it at Day 6. |
| **A2** | 3.1 | Parent commit is `merge_commit_sha^1`, obtained from the GitHub API, with a diff-coverage rule for rebase merges. | AIDev carries no base, head or merge SHA. `base.sha` would be the commit the PR was *opened against*, potentially weeks stale. |
| **A3** | 3.1 | Census scope ≡ PyCG scope, as a rule with the failure mode named. | A wider census makes every out-of-scope site look unresolved and inflates exposure toward 100%. |
| **A4** | 3.2 | Issue-link outcome criterion marked optional and API-dependent; whether it ran is stated in Results. | It needs quota the other two criteria do not. Silent non-execution would give two runs different outcome variables under one name. |
| **A5** | 7 | Pilot added as Day 2.5, with its gate table. | The Day 1–2 gates test the harness against fixtures, never against the corpus. |
| **A6** | 3.1 | Primary analysis restricted to single-site (caller, callee) pairs; multi-site pairs to a bounded sensitivity analysis; fallback pre-specified. | PyCG resolves at pair granularity, so call-site granularity is not measurable. Bias ran toward the null — toward the stop rule. |
| **A7** | 3.1 | `EXCLUDED_SYNTAX` split out of `UNANALYZED` and excluded from the study. | PyCG parses on CPython 3.10; 3.11+ syntax fails because our toolchain is behind, not because the code is dynamic. §4.4 reads that arm to decide what company this is. |
| **A8** | 3.4, 4 | Primary inference is cluster-robust at repository level; naive Katz CI reported alongside; power restated in clustered terms. | Symbols cluster in PRs, PRs cluster in repos. Katz assumes independence and understates variance at exactly the boundary §4 turns on. |
| **A9** | 3.1 | Edge matching normalises PyCG's path separators and is lenient about the package prefix, requiring a dot boundary. | PyCG names the same function two ways and leaks path separators into module names. Strict equality would mark nested-package callers unresolved wholesale. |
| **A10** | 3.1, 6 | The exposure variable's **capability profile** is recorded, and the scope of a null is narrowed to match it. | Measured: the variable detects 1 of 4 unresolvable-caller mechanisms. Value-dispatched calls carry no callee name, so they produce no pair and read UNEXPOSED. A null therefore cannot be reported as a null about unresolvability in general. |
| **A11** | 4.1 | Control corpus is synthetic repositories plus one real repository, not a Django fixture; per-mechanism detection reported against a fixed reading table; gate unchanged at pooled RR ≥ 5. | A control that times out measures our timeout, not our instrument. Synthetic repos guarantee `graph_status == OK`, so a non-detection is unambiguously a detection failure. |
| **A12** | 4.2 | Control corpus: **if an exposed unit is excluded, its matched control twin is excluded with it.** Unseeable mechanisms go to the capability table only; the firing mechanism scales to 40/40. Gate unchanged. | The first run computed RR = 8.0 from 50 of 80 units, with all 30 exclusions in the exposed arm and none in the control arm. Coding them the other way gives 2.0 — a 4× swing from asymmetric absence alone. |
| **A13** | 4.3 | **Differential exclusion by arm**, for the main study: exclusions reported by arm and reason; pooled RR demoted if the exposed-arm rate exceeds the control arm's by >10pp or the bounds diverge; every exclusion category bounded both ways, or declared unbounded. | Every exclusion category plausibly removes exposed units faster than unexposed ones. The control measured the magnitude at 4×; on the real corpus nobody plants it deliberately. |
| **A14** | 4.4 | RR reported **by agent**; §6 scopes the finding; non-identical arm time windows recorded. | Computed: Codex is 64.9% of the corpus and Claude Code 1.4% (459 PRs). A general-sounding claim would rest on one agent — and the product targets the agent with 1.4% of the evidence. |
| **A15** | 4.5 | Human-arm star-band mismatch confirmed by **joining `human_pull_request` to `repository`**, not by a superset statistic; handled by stratifying on star band. | The human arm's true floor is 503 stars with 0% below 500; the agent arm has 47.3% below 500 and a median of 564 against the human Python slice's 14,933. A 26× popularity gap. |
| **A16** | 4.6 | **Supersedes A13's mechanism.** Distinguishes the control's *restricted estimand* (no measurement to be missing) from the study's genuine, likely **MNAR** loss to follow-up. Primary labelled complete-case; worst-case bounds; **tipping-point multiplier** run only if the primary is positive; IPCW as supporting. | The §3.3 2×2 is a complete-case analysis, unbiased only under MCAR. The bias is not identifiable, so the question is how much of it the conclusion survives — which is a number, not a caveat. |
| **A17** | 4.7, 6 | Agent-stratified RR **reportable for Codex only**; Claude Code descriptive at best; corpus composition recorded in §6 as *conservative*; retrieval-strategy moderation **pre-registered as a prediction**. | Codex is 64.9% of the corpus and has the lowest breaking rate (2.62%) of the five, so a positive appears under unfavourable conditions. Claude Code is 459 PRs — below the power floor before the filters. A moderation found post-hoc is a story; predicted, it is mechanism evidence. |

**A8 is the one that most needed to be pre-registered.** Switching to cluster-robust
inference after seeing a confidence interval would be indistinguishable from moving the
goalposts, whatever the motivation.

Amended by: Claude Opus 5, 2026-08-04. Reviewed by: *(sign before running Stage A)*.

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
  (HuggingFace `hao-li/AIDev`, Zenodo `10.5281/zenodo.16899501`), AIDev-pop subset —
  530 Python projects with ≥100 stars. Human PRs are the comparison arm and run in the
  **same pass**, not a later one. **[A1]**
- **Design:** 2×2 contingency table, relative risk with a 95% confidence interval.

**Corpus arithmetic — fixed before the run** (see amendment **[A1]**):

| Stage | Agent | Human |
|---|---|---|
| Python repos, AIDev-pop | 7,191 | 1,402 |
| Filtered to structural task types (`feat`/`fix`/`perf`/`refactor`/`chore`) | **4,798** | **1,026** |
| Merged only — required, the outcome is a 7-day post-merge scan (69.3% acceptance) | **~3,300** | ~700 |
| PyCG succeeds (~78%; the rest is the UNANALYZED arm, not discarded) | ~2,570 | ~550 |

`docs/findings/PHASE0_RUNBOOK.md` §3 carries the per-stage expected shape and the stop
conditions if any of these come out far off.

### 3.1 Exposure variable — fixed

At the **parent commit** of the PR (never the merged state — that leaks the outcome):

**Obtaining the parent commit. [A2]** The AIDev dataset does not carry it. The
`pull_request` table has `id, number, title, body, agent, user_id, user, state,
created_at, closed_at, merged_at, repo_id, repo_url, html_url` and no base, head or merge
SHA; `pr_commits` has `sha, pr_id, author, committer, message` with no parent field and no
ordering field, so the PR's first commit cannot be identified from it either. Merge
metadata is therefore fetched once per PR from
`GET /repos/{owner}/{repo}/pulls/{number}` and cached. **A GitHub token is a prerequisite
of this study**, not an implementation detail. Responses are cached to disk so a re-run
consumes no quota — §5 of the runbook requires the whole thing be reproducible from raw
data.

**The parent is `merge_commit_sha^1`, not `base.sha`.** `base.sha` is the commit the PR was
*opened against*; for a long-lived PR that can be weeks stale, and exposure would be
classified against a repository state that never immediately preceded the change. What this
study needs is the trunk state the change **landed on**, because that is the code that then
broke.

That is well defined for merge commits and squash merges. It is **not** well defined for
rebase merges: GitHub replays each commit onto the base individually, with new SHAs and no
merge commit, so for a PR of N > 1 commits `merge_commit_sha^1` is the PR's own
second-to-last commit rather than trunk.

Detection is by **diff coverage**, not by commit message. A squash commit's message is the
PR title and body, which matches no individual `pr_commits.message`, so a message-matching
rule would silently reject every squashed multi-commit PR — the most common case on GitHub.

| Case | Detection | Parent |
|---|---|---|
| Merge commit | `merge_commit_sha` has ≥ 2 parents | `merge_commit_sha^1` |
| Squash | 1 parent, and the commit's diff covers the PR's **entire** changed-file set | `merge_commit_sha^1` |
| Rebase, N > 1 | 1 parent, and the diff covers only a **proper subset** of that set | walk back along first-parent while each commit's changed files ⊆ the PR's file set and its author matches a `pr_commits.author`, at most `count(pr_commits)` steps; parent is the first parent of the earliest such commit |
| Ambiguous | the walk exceeds `count(pr_commits)` steps, or stops on step 1 with a partial diff | **exclude, and count as corpus attrition** |

The changed-file set comes from `pr_commit_details`. The ambiguous bucket is reported in
Results alongside clone failures rather than quietly dropped, and the rule is validated
against a fixture repository merged three ways — once per strategy.

Run **vanilla PyCG, entry-point scoped, no custom resolvers.**

**Scope rule — the census and the graph must see the same files. [A3]** PyCG reports
`{caller_fqn: [callee_fqn, …]}` with no line numbers and no record of sites it failed on,
so "a call site PyCG did not resolve" is not something PyCG reports — it is computed by
joining our tree-sitter census against PyCG's edge set. If the census walks a wider file
set than PyCG was given, every call site outside PyCG's scope has no possible edge and
exposure inflates toward 100%. One function computes the file set and both stages consume
it. `PHASE0_RUNBOOK.md` §6 Q4 lists "exposure ≈ 100% → classifier degenerate" as a stop
condition; this is the mechanism that would cause it.

For each changed symbol `S`, enumerate every call site referring to `S` and classify:

- **EXPOSED** — one or more call sites referring to `S` exist that PyCG did not resolve,
  or `S` sits in a file PyCG timed out / OOM'd on.
- **UNEXPOSED** — every call site referring to `S` was resolved by PyCG.

**Granularity: the primary analysis is restricted to single-site pairs. [A6]** The
definition above is stated at *call-site* granularity. PyCG resolves at
**(caller, callee) pair** granularity — it emits a set of callees per caller, so a function
`F` calling `S` both directly and through `getattr` produces one edge `F → S`, and asking
whether that edge exists marks **both** sites resolved. The unresolved one is invisible,
and the bias runs toward UNEXPOSED, toward RR ≈ 1, and therefore toward the stop rule in
§4. It is the most expensive direction for an artefact to point.

The property is not measurable at pair granularity. It is measurable *exactly* on a subset:

| Sites in `F` matching `S` | Measurable? |
|---|---|
| Exactly one | **Yes** — `S ∈ edges[F]` ⟺ that site resolved |
| Two or more | No — pair granularity collapses them |

The census already counts sites per pair, so the split costs nothing.

1. **Primary analysis: single-site pairs only.** On this subset the instrument does exactly
   what this section says it does, and the headline number needs no caveat.
2. **Sensitivity analysis: multi-site pairs, coded both ways** — all EXPOSED for an upper
   bound, all UNEXPOSED for a lower bound. If the verdict is identical at both bounds, the
   collapse provably does not affect the conclusion, and that is a number rather than a
   disclosure.
3. **Fallback, fixed now so it is not a rescue later:** if the pilot projects `a < 20` in
   the single-site exposed arm, the primary analysis reverts to the full sample with the
   bias documented. The switch and the projection that triggered it are recorded in the
   amendment log **before** the full run. **That projection is read against the
   cluster-adjusted effective sample size of §3.4, not the raw event count** — the
   restriction and the clustering both shrink effective N, and evaluating either alone
   would trip the fallback at the wrong threshold.

The **opposite** bias is also measured rather than disclosed: matching call sites by short
name over-matches, since `validate` also catches `other.validate` and
`UnrelatedClass.validate`. Fifty matched sites from the pilot are hand-checked and the
false-match rate reported.

**Matching an edge to a symbol. [A9]** Two defects in PyCG's naming were found by
running it, not by reading about it. Both are silent: a name mismatch does not error, it
returns no edge, and the site reads as unresolved.

1. **Path separators leak into module names.** `acme/sub/deep.py` is named `sub\deep` on
   Windows and `sub/deep` elsewhere — a path separator where a dot belongs. Normalised to
   dots at the point PyCG's output is parsed.
2. **The same function has two names.** At its definition site it is `sub.deep.helper_fn`;
   where an import resolved it, `acme.sub.deep.helper_fn`. This is the name-resolution
   mismatch DyPyBench measured at roughly 12% of observed differences, and it lands on the
   join directly.

An edge target therefore matches a symbol when the two are equal, **or when either is a
dot-boundary suffix of the other**. The dot boundary is required so `revalidate` never
matches `validate`.

**Bias direction, stated before the run: leniency errs toward UNEXPOSED**, because it finds
edges a strict comparison would miss. That is toward the null and toward the stop rule —
the same conservative direction as A6, and the reverse of a rescue. Strict equality was
rejected precisely because its bias runs the other way: it would inflate the exposed arm
for every layered repository in the corpus, which is the direction that manufactures a
positive.

**Diagnostic:** the pilot reports how many matches were exact and how many required
prefix tolerance. If tolerance is doing most of the work, the join is resting on a
heuristic rather than on agreement, and that must be visible before the full run.

**Capability profile of the exposure variable — measured, not assumed. [A10]**

Exposure is operationalised by matching a call site's **callee name** to the changed
symbol. That has a consequence which was measured before the run, by probing four
unresolvable-caller mechanisms with an empty edge set, so that a miss is structural rather
than something PyCG happened to resolve:

| Mechanism | Detected | Why |
|---|---|---|
| `super()` chain | **yes** | the site names `validate`; the edge is simply absent |
| computed `getattr(m, cfg[k])()` | no | no call site carries the symbol's name |
| string-keyed registry `REGISTRY[k]()` | no | same |
| registering decorator, `HOOKS[0]()` | no | same |

**One of four.** A call dispatched through a *value* carries no name, so nothing can be
attributed to the symbol, the symbol produces no pair at all, and it reads **UNEXPOSED
while having a hidden caller.**

**What this variable actually measures** is therefore *"named call sites whose edge PyCG
did not emit"* — in practice, largely `super()` chains — and **not** *"call sites we cannot
resolve"*. That is narrower than the prose above, and narrower than the worked example in
`README.md`, which is a computed `getattr`.

**Bias direction: false negative, toward the null.** Consistent with A6, A7 and A9, and for
the same reason: an instrument that under-detects and still shows lift is stronger
evidence, not weaker.

**Diagnostic:** the pilot reports the share of non-builtin call sites carrying **no static
callee name**. That is the prevalence half of the Judge decomposition, and it bounds how
much of the problem this variable is structurally blind to. If it is large, the gap between
what we measure and what the product claims is large too, and that belongs in
`PROJECT_CONTEXT.md` before any sales conversation.

**Parse failures are attrition, not an arm. [A7]** PyCG parses with its host interpreter's
`ast`, pinned at CPython 3.10 (`research/phase0/ENVIRONMENT.lock`). A repository using
`except*` (3.11) or `type X = …` (3.12) therefore fails to parse **because our toolchain is
behind, not because the code is dynamic.**

- **`UNANALYZED_RESOURCE`** — timeout or OOM. This is the third arm, and the only thing
  `PHASE0_RUNBOOK.md §4.4` reads when deciding whether this is a scalability product rather
  than an unsoundness product.
- **`EXCLUDED_SYNTAX`** — parse failure attributable to interpreter version. **Excluded
  from the study**, reported as corpus attrition exactly like a repository that will not
  clone.

Merging the two would let a fact about our toolchain decide what company this is. The
pilot reports the `EXCLUDED_SYNTAX` share for its own sake: if it is large on a 2026
corpus, vanilla PyCG on 3.10 may not be a viable instrument at all, and that is far
cheaper to learn on 200 PRs than on 3,300.

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
- is linked to an issue opened within 7 days that references the PR **[A4 — optional]**

**[A4]** The first two criteria run from the local clone and need no API quota. The third
requires the GitHub issues API and is therefore an **optional enrichment**: it is run if
quota allows and skipped otherwise. Whether it ran is stated in Results. A criterion that
silently did not execute would make two runs of this protocol produce different outcome
variables under the same name, which is the ambiguity this document exists to remove.

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

### 3.4 Observations are clustered, and the CI must say so [A8]

The unit of analysis is a changed symbol, but symbols are **not independent observations**:

- Many symbols share one PR, and the outcome is measured per file — a single revert
  commit assigns the same outcome to every symbol the PR touched in that file.
- Many PRs share one repository, and repositories differ systematically in fix-commit
  rate, review culture, test coverage and framework density. Three of those are already
  named as confounders in §5.

The Katz log method assumes independent Bernoulli trials. Under clustering it **understates
variance**, so the confidence interval comes out too narrow — and it comes out too narrow at
precisely the boundary that decides the project, since §4 turns on whether the CI lower
bound clears 1.5 and whether it includes 1.0. A naive CI could clear a threshold that a
correct one would not.

**Fixed before data:**

1. **Primary inference is cluster-robust, clustered at the repository level** — the
   outermost cluster, which absorbs the PR level beneath it. Estimated as a modified
   Poisson regression (log link, binary outcome) with a robust sandwich variance, which
   yields a relative risk directly. `statsmodels` GEE with a Poisson family and `repo_id` as
   the group provides this; it is not hand-rolled.
2. **The naive Katz CI is reported alongside, explicitly labelled as such.** The gap between
   the two is the design effect, and it is a number the reader is entitled to see.
3. **The reported design effect** (ratio of cluster-robust to naive variance) goes in
   Results whatever it is.

**Power is restated in clustered terms.** `a ≥ 20` counts events, and 20 breakages drawn
from two repositories are not 20 independent observations. Results must therefore also
record **the number of distinct repositories contributing at least one exposed-arm
breakage**, and the floor is read against the effective sample size, not the raw count.

This is recorded now because switching to cluster-robust inference *after* seeing a
confidence interval would be indistinguishable from moving the goalposts, whatever the
motivation.

---

## 4. Decision thresholds — fixed before data

Every CI below is the **cluster-robust** one from §3.4. The naive Katz interval never
decides anything; it is reported for comparison only.

| Result | Verdict | Action |
|---|---|---|
| **RR ≥ 3.0**, CI lower bound > 1.5 | Strong | Proceed to Phase 1. The label predicts breakage. |
| **RR 1.5 – 3.0**, CI excludes 1 | Weak but real | Proceed, **but the pitch changes** from "we prevent breakage" to "we prioritise review attention." Re-do the business case in `PROJECT_CONTEXT.md §5` before building. |
| **RR < 1.5** or **CI includes 1.0** | Null / underpowered | **Stop.** See §6. |

### 4.1 Control design [A11]

`PHASE0_RUNBOOK.md §2.1` names a Django fixture. This amends that, and it lands before the
control runs.

**Why not Django.** A control that times out returns `UNANALYZED_RESOURCE`. The gate would
then be measuring our timeout rather than our instrument, which tests nothing about
detection. RUNBOOK itself expects ~22% of real repositories to time out.

**Two halves, each establishing something the other cannot:**

| Half | What it establishes |
|---|---|
| **Synthetic repositories** — small, purpose-built, one mechanism each | `graph_status == OK` is guaranteed, so a failure to detect is **unambiguously a detection failure**. This is the only place RR ≥ 5 carries meaning. |
| **One real repository** (5–20k LOC, genuine package structure) | The pipeline survives nested packages, `__init__.py` re-exports, relative and conditional imports, C extensions — all things synthetic repos are clean of by construction. |

The real repository is chosen to run **comfortably inside 600 s, not to stress it**. Scale
is what the pilot measures, on real corpus repositories, where a timeout is a legitimate
recorded outcome rather than a broken control.

**Its `graph_status` and duration are reported.** If the real control repository times out,
that is a finding about instrument viability and it surfaces — never grounds for quietly
substituting a smaller repository until one passes.

**The control corpus is not representative of the study corpus.** It isolates detection and
under-represents scale by construction. Stated here so no reader mistakes it for a sample.

**Gate unchanged: pooled RR ≥ 5.** Requiring all four mechanisms to fire was rejected —
that converts the control into a *capability requirement*, forcing resolvers to be built
before the thesis may be tested, which inverts the point of Phase 0. The control
characterises the instrument; it does not certify it.

**Per-mechanism detection is reported alongside, and the reading is fixed now:**

| Pattern | Meaning | Consequence |
|---|---|---|
| 4/4 fire | broad | Null scope: unresolvability generally |
| 2–3 fire | partial | Null scoped to the detected mechanisms, **named individually** in §6 |
| **1/4 — only `super()`** | narrow | Null scoped to statically-named unresolved sites, per A10. **Explicitly not a claim about dynamic dispatch.** |
| 0/4 | broken | **Stop.** Not a null — fix the instrument. |

The third row is the likely one given A10, and the point of fixing the reading now is that
the headline sentence gets written before anyone is motivated to write it generously.

**Into `PHASE0_RUNBOOK.md §5`'s authenticity checklist:** if only `super()` fires, record
that `super()` is PyCG's single best-documented blind spot — the easiest possible positive,
and therefore weak evidence of general detection capability. Better said by us than worked
out by a reader.

### 4.2 Control corpus construction [A12]

Written after the first control run, **before** the corrected one, because the first run
exposed a construction defect rather than a result.

**What happened.** The pooled RR of 8.0 was computed from 50 of 80 units. All 30 exclusions
fell in the **exposed** arm and none in the control arm: symbols reached only by
value-dispatch have zero matching call sites, so A6 excludes them, while their matched
control twins have a resolvable direct call and remain. Coding the excluded units the other
way gives RR = 2.0. **A 4× swing produced by asymmetric absence alone.**

**Invariant, and it is general rather than a patch:**

> **If an exposed unit is excluded, its matched control twin is excluded with it.**

Pairwise, automatic, and it holds for mechanisms not yet built. A corpus that drops 75% of
one arm and 0% of the other is broken *whichever way it pushes the ratio* — the test being:
would this change be made if the result had been RR = 2.0 and failed? Yes. That is what
separates a fixture correction from motivated reasoning.

**Two consequences:**

1. Mechanisms the instrument cannot see belong to the **capability table only** and never
   to the pooled RR. A11 already said this in principle; the corpus did not reflect it.
2. With one mechanism firing, 10-vs-10 is too thin. The firing mechanism scales to
   **40/40**, so the control has power rather than a wide interval around a fragile point.

**The gate is not changed.** Adding a `bounds_agree` condition after seeing a disliked
result would be a threshold change, and tightening is as much a degree of freedom as
loosening. The bounds diverged because the corpus was asymmetric, not because the world is
uncertain — so the cause is fixed and the unchanged gate is re-run.

### 4.3 Differential exclusion by arm [A13]

**This is a threat to the main study, not only to the control**, and nothing in this
document previously checked for it.

Every exclusion category plausibly removes exposed units faster than unexposed ones:

| Exclusion | Correlated with exposure? |
|---|---|
| `UNANALYZED_RESOURCE` (timeout / OOM) | **Yes** — dynamic code is harder to analyse |
| `EXCLUDED_SYNTAX` (A7) | plausibly |
| Multi-site collapse (A6) | **Yes** — more call sites, more chance of collapse |
| No static callee (A10) | **Yes, by definition** — that is the dynamic-dispatch category |
| Ambiguous parent (A2) | possibly |

The control measured what this mechanism can do: **RR 2.0 → 8.0**. On the real corpus
nobody plants it deliberately, which makes it harder to notice, not weaker.

**Fixed before the run:**

1. Exclusion counts are reported **by arm and by reason** — never a single attrition total.
2. **Differential-exclusion check.** If the exposed-arm exclusion rate exceeds the
   control-arm rate by more than **10 percentage points**, or if the bounds below diverge on
   the §4 verdict, the pooled RR is **not** the headline result; the bounded reading leads.
3. **Bound every exclusion**, as A6 bounds multi-site: code all excluded units UNEXPOSED
   (lower) and EXPOSED (upper), report both. **Divergent bounds mean no general claim.**
4. **The pilot reports exclusion rate by arm**, so this is known before the full run rather
   than at analysis.

**And the defect A6 was found to have generalises.** A zero-site symbol returned `None` for
`primary` *and* for both sensitivity bounds, so the largest exclusion category was invisible
to the very mechanism built to make exclusions visible.

> **Every bound must be computable for every exclusion category — or the category is
> unbounded and must say so.**

That is the typed-absence principle turned on our own sensitivity analysis.

### 4.4 Agent composition — the result is mostly about Codex [A14]

Computed from the live `pull_request` table, 33,596 rows:

| Agent | PRs | Share |
|---|---|---|
| **OpenAI Codex** | 21,799 | **64.9%** |
| GitHub Copilot | 4,970 | 14.8% |
| Devin | 4,827 | 14.4% |
| Cursor | 1,541 | 4.6% |
| **Claude Code** | **459** | **1.4%** |

**Two consequences, fixed before the run:**

1. **RR is reported by agent**, and §6 scopes the finding accordingly. "Unresolved sites
   predict breakage in agent PRs" reads as a general claim while resting on one agent.
2. **The product targets Claude Code users, and the evidence will contain 459 of their
   PRs.** That belongs in `BRIEFING.md` beside the market argument, not only here.

Recorded with it: the arms cover overlapping but non-identical windows — agent PRs
2024-12→2025-07, human PRs 2025-01→2025-06. A limitation, not an assumption of
comparability.

### 4.5 The human arm is not a matched control [A15]

**Settled by joining the two tables, not by computing a related quantity.** An earlier
version of this amendment cited `min(stars) = 101` over all 2,807 repositories. That
measures the **agent** arm's floor; the dataset card's claim is about the **human** subset.
Correct measurement, wrong quantity — the same error shape as the confidence column.

The join that answers it: `human_pull_request ⋈ repository`, 6,569 of 6,618 PRs matched.

| | min stars | median | max | repos below 500 |
|---|---|---|---|---|
| **Human arm** (810 repos) | **503** | 4,194 | 203,424 | **0.0%** |
| **Agent arm** (2,807 repos) | 101 | 564 | 203,424 | **47.3%** |

The dataset card is correct, and **the mismatch is far larger than a threshold difference
suggests: 47.3% of agent repositories sit entirely below the human arm's floor.** The
Python slice joins to exactly **1,402 human PRs across 162 repositories** — matching the
breaking-changes paper's figure precisely, which confirms it is this table — with a median
of **14,933 stars** against the agent arm's 564. A 26× difference in median popularity.

Comparing the arms therefore confounds *agent vs human* with *repository popularity* to a
degree that would dominate any modest effect, and §5 already names repository activity as a
confounder.

**Handling: stratify by star band (≤500, >500) and report both**, rather than restricting.
Restriction would discard 47.3% of the agent arm. Stratification keeps them, and the >500
stratum is the only band where an agent-vs-human comparison is even defined.

49 human PRs did not join to a repository row and are corpus attrition, counted.

### 4.6 Missing data — and what is *not* missing [A16]

**Supersedes A13's mechanism.** A13 correctly identified differential exclusion as a
threat and specified an ad-hoc margin. This replaces that with named methods, and it first
draws a distinction A13 merged.

#### The control's exclusion is not missing data

The units excluded from the control are not cases whose exposure status exists and went
unobserved. A symbol with **zero statically-named call sites has no measurement to be
missing** — the instrument definitionally cannot classify it. That is not loss to
follow-up; it is a **restricted estimand**.

So the control needs no imputation and no bounding. It needs an honest label:

> RR = 8.0 **among symbols with ≥1 statically-named unresolved call site.** Recall against
> planted exposure: 25%. Not an estimate for dynamically-dispatched unresolvability, which
> the instrument cannot measure.

That is what A11's reading table already said. The corpus hid it by including unseeable
mechanisms in the pooled arm; A12 removes them. The estimand was always restricted.

#### The real study does have missing data, and it is likely MNAR

`UNANALYZED_RESOURCE`, `EXCLUDED_SYNTAX`, ambiguous parents, unreadable repositories —
these are units with a **real exposure status we failed to observe**. That is loss to
follow-up, and the mechanism is plausibly *not* at random: complex dynamic code both times
out more (exposure-related) and breaks more (outcome-related). Missing-not-at-random.

**The §3.3 2×2 is a complete-case analysis**, which is unbiased only under MCAR and biased
under MAR and MNAR. The control measured what asymmetric absence alone can do to this
estimate: **RR 2.0 → 8.0**.

And the honest limit, stated up front: where missingness depends on unmeasured causes,
neither imputation nor weighting removes the bias. The bias is **not identifiable**. What
*is* available is quantifying how much of it the conclusion survives.

#### Fixed before the run

1. **Primary: complete-case RR, cluster-robust, labelled `complete-case`** in Results, with
   exclusion counts **by arm and by reason**. Never a single attrition total.
2. **Worst-case bounds** — all excluded coded UNEXPOSED (lower) and EXPOSED (upper). This is
   the outer envelope. **Divergent verdicts across the bounds mean no general claim.**
3. **Tipping-point analysis.** Report the *breakage-rate multiplier* among excluded PRs
   required to push RR below the §4 threshold of 3.0. A multiplier of 4× is implausible and
   the result is robust; 1.2× is not and it is fragile. **Run only if the primary analysis
   is positive** — stress-testing a null is a fishing exercise, and pre-specifying the
   direction prevents it.
4. **IPCW as a supporting analysis, never the headline.** Missingness here is predictable
   from measured variables — `graph_status`, multi-site count, no-static-callee share,
   patch size, files touched — so exclusion probability can be modelled and observed units
   weighted. Recorded as supporting because uptake of the method in applied epidemiology is
   limited and an unfamiliar headline estimator invites the wrong argument.
5. **The pilot reports exclusion rate by arm.** If the difference is material, §6 leads with
   the bounds and the tipping point, not the point estimate.

### 4.7 Agent stratification, and a predicted moderation [A17]

Extends A14 with what the composition means once it is crossed against the source paper's
per-agent breaking rates.

| Agent | Share of corpus | Breaking rate (arXiv 2603.27524) |
|---|---|---|
| **OpenAI Codex** | **64.9%** | **2.62% — lowest of five** |
| GitHub Copilot | 14.8% | 3.04% |
| Devin | 14.4% | 4.09% |
| Cursor | 4.6% | 4.20% |
| **Claude Code** | **1.4%** (459 PRs) | **5.10% — highest** |

**The corpus is two-thirds the safest agent, and that is conservative.** If the effect
appears anyway, it appears under unfavourable conditions. **Recorded in §6 as strengthening
a positive**, since a reader will otherwise see only "65% one agent" and read it as a
weakness.

**Agent-stratified RR is reportable for Codex only.** 459 Claude Code PRs, through the
structural filter, the merged filter and into the exposed arm, lands far below the `a ≥ 20`
floor. Stating this now stops someone computing it at analysis time and reading noise.
Claude Code is **descriptive at best**, and said as such.

**A moderation hypothesis, pre-registered rather than discovered.** The five agents differ
in retrieval strategy — Claude Code greps with no index, Cursor uses embeddings, Devin
maintains its own index, Codex operates in a sandboxed checkout. If unresolvability predicts
breakage **because the agent could not see the caller**, then retrieval strategy should
*moderate* the effect, and Codex-heavy pooling would wash it out.

> Predicted: RR differs by agent retrieval strategy, where power permits.

If it appears, it is mechanism evidence for the causal story. Found afterwards, it is a
story fitted to a number. This paragraph is the difference between the two, and it costs
nothing to write now.

### Power

Target ≥ 200 EXPOSED symbols with an observed breakage rate ≥ 5%. If `a < 20`, the
confidence interval will span 1.0 regardless of the point estimate. **That is not a
negative result — it is no result**, and reporting it as a negative would be as dishonest
as reporting it as a positive. Widen the corpus (more repos, longer window) before
concluding anything.

Record the achieved `a` in the Results section whatever happens, together with the number
of distinct repositories contributing to it (§3.4) — 20 events from two repositories do not
meet this floor.

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

**We stop, and we publish — but we publish the null we actually measured. [A10]**

The capability profile in §3.1 narrows what a null is entitled to claim. The variable
detects named call sites whose edge is missing; it is structurally blind to calls
dispatched through a value. So the defensible null is:

> *"Call sites that are statically **named** but unresolved do not predict breakage in
> AI-authored Python changes, RR = … [ … ], n = …. Calls dispatched through a value were
> not measurable with this instrument and are excluded; they were X% of non-builtin call
> sites in the corpus."*

Reporting instead that *"unresolvability does not predict breakage"* would overclaim the
null, because most unresolvability was never measured. That is the same error as
overclaiming a positive, and it is easier to make because a null feels modest.

**The same limit binds a positive.** The excluded sites are **non-randomly the most dynamic
in the corpus** — computed dispatch, string registries, plugin loading. The direction of
bias on the point estimate is *unknown*, because their breakage rate is unmeasured. So a
positive result on statically-named sites alone is a result about the **tamest** form of
unresolvability, and generalisation beyond it is not claimed. Neither verdict may be
stated more broadly than the instrument reached.

A rigorous null of the narrower kind is still a genuine contribution. The
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
| **2.5** | **Pilot — 30 repositories, ~200 PRs, every stage end to end. [A5]** |
| 3–5 | Full run: checkout parent commits, scoped PyCG, call-site enumeration, 7-day history scan. |
| 6 | Fill the 2×2. Compute RR + CI. Stratify by the five confounders. |
| 7 | Write the Results section below. Convene the go/no-go. |
| 8–12 | Repeat the identical protocol for the TS/JS arm (`RUNBOOK §7`). |

**Day 2 gate:** the outcome classifier must agree with hand-labelling on ≥16 of 20 PRs.
If it does not, the outcome variable is unreliable and the whole study is unreliable — fix
the classifier before proceeding, and record how many iterations that took.

### Day 2.5 — the pilot gate [A5]

The Day 1–2 gates test the harness against synthetic fixtures and planted positives. They
do not test it against the corpus. The pilot runs every stage on ~200 real PRs from 30
repositories and reports, before ~3,300 PRs of compute is committed:

| Metric | Expected | Decides |
|---|---|---|
| Clone success | 80–95% | corpus still exists |
| PyCG success | ~78% | instrument viable |
| `UNANALYZED_RESOURCE` share | ~22% | third arm is populated |
| **`EXCLUDED_SYNTAX` share** | small | **whether PyCG-on-3.10 is viable at all [A7]** |
| Changed symbols per PR | 1–5 median | scoping is sane |
| Exposure rate | 10–30% | classifier not degenerate |
| Breakage rate | 5–20% | outcome classifier calibrated |
| **Multi-site pair fraction** | — | **whether the A6 restriction costs real power** |
| **Short-name false-match rate** | — | magnitude of the opposite bias |
| **Design effect** (§3.4) | — | how much clustering widens the CI |

Any of the first seven far outside its range is a **stop and fix**, not a "proceed
carefully" — `PHASE0_RUNBOOK.md §6` carries the diagnosis tree. The last three carry no
expected range because nobody has measured them; they exist so that the A6 fallback and the
§4 power reading are made on numbers rather than on assumption.

---

## 8. Results

> **Empty. Do not fill until the run is complete. Do not start Phase 1 until this is filled.**
>
> Two blocks below: one per language arm. A strong Python result with a null TS/JS result
> is a valid and useful outcome — it means the product is Python-first, and that is a
> narrower company than the one currently described in `PROJECT_CONTEXT.md`.
>
> **Before filling either block, complete the authenticity checklist in
> `PHASE0_RUNBOOK.md §5`. All eight items. A result that fails a control is not a result.**

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
