# Project Context — Research Record, Business Case, Competitive Landscape

> The complete reasoning behind this project, including the parts that were wrong.
> If you are joining the team, read this second (after `ARCHITECTURE.md`).
>
> **Every claim below is tagged with its evidential status.** Nothing here should be
> repeated to an investor or a customer without checking the tag first.
>
> | Tag | Meaning |
> |---|---|
> | ✅ **VERIFIED** | Read in the primary source, in full |
> | 🟡 **SECONDARY** | From a citing paper, vendor blog, or abstract — not the primary text |
> | 🔴 **UNVERIFIED** | Single weak source, or our own estimate. Do not cite externally. |
> | ⚠️ **CORRECTED** | We believed something else earlier. Recorded so nobody re-derives the error. |

---

## 1. The problem, in one page

Google's codebases are tractable to analyze not because Google has more data, but because
Google made dependency declaration a **build-time invariant**. ✅ *"Blaze detects whether a
target tries to reference a symbol without depending on it directly and, if so, fails with
an error... Rolling this change out across Google's entire codebase and refactoring every
one of our millions of build targets to explicitly list their dependencies was a multiyear
effort."* — *Software Engineering at Google*, ch. 18.

Everyone else must **reconstruct** the graph at read time, and reconstruction is lossy in a
way nobody measures. That gap is the product.

---

## 2. The three foundational papers

### 2.1 *In Defense of Soundiness: A Manifesto* (CACM 2015) — ✅ read in full

Ten authors from Microsoft Research, Google, Athens, Waterloo, Aarhus, IIT Bombay.

- ✅ *"we are not aware of a single realistic whole-program analysis tool... that does not
  purposely make unsound choices."*
- ✅ *"we are not aware of a single sound whole-program static analysis tool applicable to
  industrial-strength programs written in a mainstream language!"*
- ✅ **The tradeoff is causal:** *"sound modeling of all language features usually destroys
  the precision of the analysis... Imprecision, in turn, often destroys scalability
  because analysis techniques end up computing huge results."*
  → **Design consequence:** any roadmap item phrased "more complete analyzer" is a trap.
- ✅ **Soundness is not required for our client class:** *"Soundness is not even necessary
  for most modern analysis applications... Such clients include IDEs (auto-complete
  systems, code navigation), security analyses, general-purpose bug detectors."*
  → An AI coding agent is an IDE-class client. **We need calibration, not soundness.**
  This is the single most load-bearing sentence in the entire research file.
- ✅ **Their unmet ask is our product:** *"some effort should be made in experimental
  evaluations to compare results of an unsound analysis with observable dynamic behaviors
  of the program."* Published 2015. Still not productized.
- ✅ Their table of commonly-ignored features covers C/C++, Java/C#, JavaScript.
  **There is no Python row.** They also note no reliable survey of dangerous-feature usage
  exists, and suggest *"benchmarks or regression suites could be assembled to measure the
  effect of unsoundness."*

### 2.2 *DyPyBench* (FSE 2024) — ✅ read in full

50 Python projects, 681k LOC, 29,511 test cases, 82% average statement coverage.

- ✅ **PyCG produced no graph for 11 of 50 projects**: 6 exceeded a six-hour timeout,
  3 exceeded 60GB memory, 2 crashed. DynaPyt succeeded on all 50.
- ✅ Static graphs: 60,565 edges (avg 1,552/project). Dynamic: 9,575 edges (avg 191).
  **The dynamic graph is ~12% the size of the static one**, even at 82% statement coverage.
- ✅ *"only 49% of the edges present within DynaPyt's call graphs are within the set of
  edges found in PyCG's call graphs."* → 51% of runtime edges are invisible statically.
- ✅ ⚠️ **CORRECTED — the 51% is mostly not useful signal.** *"a call `"abc".strip()` is
  adequately detected by DynaPyt... but PyCG fails to capture the call... this particular
  phenomenon accounts for 59% of all callees missing in the static call graph"* and
  *"Differences in function name resolution account for roughly 12% of the observed
  mismatches."*
  🔴 Our arithmetic: real actionable signal ≈ 15%, not 51%. **Combines a missing-*edges*
  denominator with a missing-*callees* denominator — verify against Figure 5 before citing.**
- ✅ ⚠️ **CORRECTED — runtime tracing is not cheap.** *"executing DyPyBench while computing
  the call graph takes 215 minutes per project"* vs *"average time required to execute a
  complete test suite is 71 seconds"* → ~180× overhead.
- ✅ Callers resolve well (95% of dynamic callers appear in PyCG); **callees do not**
  (48.5%). "Who calls this?" is answerable statically. "What does this reach?" is not.
- ✅ `super().method()` calls are absent from PyCG's graph entirely.

### 2.3 *Judge* (ISSTA 2019) — 🟡 abstract, slides, README; **full text unread**

- 🟡 ⚠️ **CORRECTED — architecture.** We assumed "fork the analyzer, instrument its
  bail-outs." Judge instead uses **annotated fixtures + capability profiles**, which is
  analyzer-agnostic and better. Pipeline: compile annotated test cases → compute CG per
  framework → compare against *expected* targets → capability profile. Separately, Hermes
  scans real projects for feature prevalence. **Unsoundness map = profile × prevalence.**
  → Neither half requires ground truth on customer code. This is our coverage score,
  correctly factored.
- 🟡 *"soundness-relevant features/APIs are frequently used and support for them differs
  vastly, up to the point where comparing call graphs computed by the same base algorithms
  but different frameworks is bogus."*
- ✅ ⚠️ **CORRECTED — JCG already covers Python.** The repo README states it is *"a
  collection of annotated test cases that are relevant for call-graph construction in
  Java, JavaScript, and Python"* and ships `jcg_pycg_testadapter`,
  `jcg_jarvis_testadapter`, `jcg_pyan_testadapter`, `jcg_code2flow_py_testadapter`.
  **We do not build this. We use it.**
- ✅ But: 10 stars, 10 forks, no releases, 63% Scala / 35% Java, JVM binary notation in
  annotations, *"each test case must be a full runnable Java program."* It measures
  **analyzers**, not **repositories**, and has no runtime service or agent integration.

### 2.4 *PyCG* (ICSE 2021) — 🟡 **Section III-C still unread after four attempts**

arXiv serves the abstract; ACM is paywalled; ResearchGate rate-limits.
**Get the TeX source at `arxiv.org/src/2103.00587`, or email Vitalis Salis.**

- 🟡 Precision ~99.2%, recall ~69.9% — but ground truth was *"manually generated"* call
  graphs of a handful of packages. Not measured at scale.
- ✅ *"PyCG is archived. Due to limited availability, no further development improvements
  are planned. Happy to help anyone that wants to create a fork... implemented in Python3
  and requires Python version 3.4 or higher. It also has no dependencies."*
- 🟡 Jarvis's independent diagnosis: *"PYCG adopts the worklist algorithm where iterations
  are unfixed until the global assignment graph remains unchanged"* and *"treats the entire
  program equally without considering its hierarchy within the application and external
  dependencies"* → the cause of the OOMs. Plus flow-insensitivity conflating points-to sets.

---

## 3. Market evidence

### The downstream pain is measured

- ✅ **Agents break maintenance work more than humans do.** *Safer Builders, Risky
  Maintainers* (arXiv 2603.27524, MSR 2026), 7,191 agent vs 1,402 human PRs from **530**
  Python repositories in AIDev, filtered to five structural task types → 4,798 agent /
  1,026 human PRs and 60,324 file-level patches. Breaking changes detected by their own
  AST tool applying 17 patterns from Du et al.; validated at 95.7% / 93.6% against two
  independent reviewers, Cohen's κ = 0.79.

  | Task type | Agent | Human |
  |---|---|---|
  | feat | 2.89% | 7.74% |
  | fix | 2.69% | 5.32% |
  | perf | 4.12% | — |
  | refactor | **6.72%** | 4.36% |
  | chore | **9.35%** | 4.95% |

  **The trends invert** — that is the paper's title. Agents are safer building and riskier
  maintaining. The authors name a *"Confidence Trap"*: highly confident agentic PRs still
  break things.
  → **This is the single best framing for the product.** Greenfield has no hidden callers;
  refactoring does.
  ⚠️ **These are the PR-level population, not ours.** Phase 0 requires *merged* PRs (the
  outcome is a 7-day post-merge scan), which at a 69.3% acceptance rate leaves ~3,300.
  See `docs/findings/PHASE0_PREREGISTRATION.md` amendment **A1**.
- 🟡 **The safety net is a coin flip.** Martian Code Review Bench, an independent
  open-source benchmark tracking real developer behaviour across ~200k–300k PRs: the #1
  tool scores **49.2% precision** — roughly one in two comments leads to a code change.
  Best F1 across all tools is 50–60%. 🔴 *Sources disagree on launch date (Feb vs Mar 2026)
  and PR count. **We have not read the leaderboard directly.***
- 🟡 **Noise is the documented killer.** *"false positives are still the #1 complaint across
  every tool"*; *"the 'cry wolf' effect... is the most common reason teams abandon these
  tools entirely."*
- 🟡 **Revealed willingness to pay.** *"one enterprise customer deployed LSP org-wide before
  broad rollout of Claude Code specifically for C and C++ navigation reliability. Their
  codebase was too large for grep to remain useful... LSP was the unlock."*
  → An enterprise built a worse version of our layer 2 at their own cost, with no vendor.

### Vendors admitting the gap in their own docs

- ✅ Anthropic: *"as the codebase grows, the defaults tuned for smaller projects can fill
  the context window with instructions and file reads unrelated to the task, costing
  tokens and degrading Claude's performance."*
- ✅ Cursor: *"On large monorepos, indexing... may not include all files if the index size
  limit is exceeded... If critical files are consistently missing from context, add them
  explicitly with @-mentions."* → The remedy is the human noticing.

### What nobody is saying

🔴 **Almost nobody publicly frames this as a dependency-graph completeness problem.**
Developers report symptoms ("context window too small", "it hallucinated", "works locally,
breaks in prod"). Nobody has the cause.

Cuts both ways: the diagnosis is unclaimed (strong entry), but we are selling a solution to
a problem with no name in the buyer's head (slow sales). **Mitigation: lead with the
symptom, prove with the cause, sell the fix.**

---

## 4. Competitive landscape

| Player | What it does | Funding / scale | Why it does not close the gap |
|---|---|---|---|
| **CodeGraph** | tree-sitter → SQLite graph → MCP, local-first | MIT, 🔴 32k–47k stars (sources conflict) | Static only. Reports nothing about what it missed. Free. |
| **GitNexus** | LadybugDB graph, 16 MCP tools, deep Claude Code integration | 🟡 ~42k stars, noncommercial licence | Same blind spots, plus a licence that blocks commercial use |
| **Graphify** | Largest by stars | 🟡 ~75k, MIT, YC S26 | Same category, same silence |
| **Cursor** | AST-aware chunking + embeddings + vector DB, incremental | ~$10B class | Index silently incomplete; the documented fix is manual `@`-mentions |
| **Claude Code** | grep/glob/read in a loop, no index | Anthropic | Deliberate: index staleness, embedding leakage, extra failure surface. Fails "I don't know the name" queries. |
| **Augment Code** | Context Engine, 400k files, live dependency graph, commit-history lineage | $252M raised; MongoDB, Spotify, Webflow | **Closest competitor.** Static + embeddings, no runtime oracle, no coverage number, code goes to their servers. |
| **Tabnine** | "Enterprise Context Engine", context-as-control-plane | — | Governance framing, same underlying blind spots |
| **Sourcegraph / Amp** | Code graph + SCIP, agentic layer | — | Strong on our layer 2. 🟡 24–48h initial index on large repos. Nothing on layers 3–6. |
| **Potpie** | Neo4j graph of every file/class/function, agents on top | 🟡 $2.2M pre-seed after 2 years | Static graph + LLM. FDE-heavy enterprise motion — the funding reflects it. |
| **Greptile / CodeRabbit / Qodo / cubic** | PR review over an indexed repo | Various | Review layer, no abstention. All optimise F1; none report coverage. |
| **Unblocked / Packmind / BuildBetter** | Non-code context, context governance, cross-agent memory | — | Complementary, not competing. Integration targets. |
| **JCG / Judge** | Annotated fixtures + capability profiles, incl. Python adapters | Research, 10 stars | Measures **analyzers**, not repos. JVM-shaped. No service, no agent integration. **We build on it.** |

### The one-sentence differentiator

> Every one of them tells the agent what it **found**. None tells it what it **missed**.

### Honest competitive risks

1. 🔴 **THE THESIS IS UNMEASURED.** Nobody — including us — has shown that unresolved call
   sites correlate with agent-caused breakage. Signal size is ~15% at best. **This is not
   a risk to manage, it is a precondition to test.** Pre-registered protocol:
   `docs/findings/PHASE0_PREREGISTRATION.md`. **No product code until it reports.**
   Recorded failure mode: this is exactly where the previous project stalled — a real
   problem, a plausible mechanism, no evidence anyone bleeds from it and no evidence they
   would pay.
2. **Free tools may be good enough.** 🟡 CodeGraph reports 60% lower cost / 69% fewer tokens
   with a plain tree-sitter graph and zero unsoundness reporting.
3. **Anthropic ships it.** Mitigated only by multi-provider MCP from day one.
4. **The scalability wall is inherited.** PyCG dies well before our target scale — which
   is one reason we consume an upstream graph rather than maintaining one.
5. **Category velocity.** CodeGraph went 0 → 47k stars in five months; Graphify ships
   daily. We cannot win a feature race and must not enter one. **Consequence, taken:** we
   consume their graph as a dependency and own only `probe/` + `label/` — the number none
   of them computes. See `ARCHITECTURE.md §0.1`.
6. **Runtime economics do not close.** ~180× overhead for a graph 12% the size, of which
   ~59% is builtins. **Consequence, taken:** the runtime oracle is deleted from v1, not
   deferred. See `ARCHITECTURE.md §0.2`.

---

## 5. Business case

**Buyer:** platform engineering. **Sign-off:** security (nothing leaves the VPC).
**Justification:** incident cost from agent-authored change. **Not** the individual developer.

**Pitch:**
> You are running coding agents against a codebase where refactors break things ~6.7% of
> the time and the agent is confident every time. We tell it — and you — exactly which
> parts of a change it could verify and which it could not. Per PR. With a receipt.

**Pricing:** per PR that receives a labeled blast radius — not per seat. We bill when we
produce a verdict. Competitors bill per seat whether or not their comments were noise.
That is a sales line they structurally cannot copy without gutting revenue.

**Free forever** for public repositories and solo developers: that is how our comments
appear in other people's PRs, which is the distribution loop.

**Adjacent budget already exists:** 🟡 *"88% of agent pilots never reach production. The
blocker is rarely the agent itself. It is the deployment infrastructure: isolation,
governance, compliance controls."* (Vendor blog — self-interested framing, directionally
consistent with other 2026 data.)

**Honest positioning shift, recorded:** ⚠️ this is a **productization play, not a research
play.** The method was proven in 2015, built in 2019, and extended to Python. Nobody turned
it into a running service. Our moat is execution — the Python prevalence scanner, the
framework resolvers, incremental update, the MCP surface, developer experience — not
novelty. Pitch it that way. Investors who read these papers will check.

---

## 6. Open threads

| # | Thread | Why it matters | Cost |
|---|---|---|---|
| 1 | **PyCG Section III-C** unread | Authors' own limitation list = the resolver backlog | 1 hour |
| 2 | **Judge full text** unread | Their feature taxonomy should shape ours | 2 hours |
| 3 | **Martian leaderboard** never opened directly | The GTM plan rests on it | 1 hour |
| 4 | **PyXray** — 🔴 claims dynamic analysis *without inputs*, NumPy/PyTorch in minutes | If true, Phase 9 is a different design | 2 hours |
| 5 | **Jarvis / PyPt** availability, licence, maintenance | Phase 1 decision | 1 day |
| 6 | **Does unresolved ⇒ breakage?** | **The thesis. Blocks all product code.** Pre-registered at `docs/findings/PHASE0_PREREGISTRATION.md`. Outcome must be behavioural (revert/fix ≤7d), not the AIDev AST labels — those are produced by static analysis and are structurally blind to the breakage in question. Analysis is relative risk, not a count. | 1 week — **next step** |
| 7 | **Reddit / HN primary research** — we found blogs, not raw practitioner complaints | Do developers ever name the *missing-caller* mechanism, or only symptoms? Protocol at `PHASE0_PREREGISTRATION.md §9`. Skipping this cost six weeks last time. | 1 week, immediately after #6 |

---

## 7. Corrections log

Recorded so nobody re-derives an error we already paid for.

| Believed | Corrected to | Source |
|---|---|---|
| 51% of the graph is recoverable signal | ~15%; 59% builtins, 12% naming artifacts | DyPyBench §4.1.2 |
| Runtime trace ≈ one CI run, free | ~180× overhead, 215 min/project | DyPyBench §4.1.2 |
| Fork the analyzer, instrument bail-outs | Annotated fixtures + capability profile | Judge |
| Nobody has done Judge for Python | JCG already ships Python adapters | JCG README |
| EU AI Act high-risk lands Aug 2 2026 | Deferred to Dec 2 2027 (Reg. EU 2026/1744) | Council, 29 Jun 2026 |
| Martian launched Feb 2026 | March 2026 (🟡 sources still conflict) | vendor blogs |
| Strict rules belong in CLAUDE.md | Rules belong in hooks/CI; memory file ≤200 lines | Anthropic docs + 2026 practice |
| Phase 0 = classify DyPyBench's missing edges | Phase 0 = **correlation test**: does unresolved predict breakage? Classification is interesting; correlation is load-bearing. | internal review |
| Framework resolvers are the moat | The **probe layer** is the moat. Resolvers are a feature race against projects shipping daily. | internal review |
| We build parse + static resolution | We **consume** an upstream graph. ~165k stars of MIT code, iterating faster than three people can. | internal review |
| Runtime oracle in Phase 9 | Runtime oracle **deleted from v1**. ~180× overhead, 12%-size graph, 59% builtins. | DyPyBench §4.1.2 |
| Phase 0 corpus is ~7,191 agent PRs | 7,191 is pre-filter. Structural task types → 4,798; merged-only (69.3% acceptance) → **~3,300**. The analysed population is 2.2× smaller. | AIDev + arXiv 2602.08915, via PHASE0_PREREGISTRATION.md **A1** |
| Agent breaking-change rate is "3.45% code generation vs 7.40% human" | That pairing appears nowhere in the paper. Per task type, agents: feat 2.89, fix 2.69, perf 4.12, refactor 6.72, chore 9.35. Humans invert it. | arXiv 2603.27524, full text |
| `pr_task_type.confidence` is the "Confidence Trap" variable | It is the task-type **classifier's** confidence in its own label, and it is 10 on every row sampled. Zero variance; useless as a stratum. Dropped. | AIDev live schema |
| AIDev supplies the PR's parent commit | It supplies no base, head or merge SHA. Parent = `merge_commit_sha^1` via the GitHub API. | AIDev live schema, **A2** |
