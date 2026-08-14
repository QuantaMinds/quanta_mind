# Market position — August 2026

**Retrieved 2026-08-12.** Every claim below carries a source and a verification status.
Nothing here is asserted from memory. Where a claim could not be verified it is marked
**UNVERIFIED** and left in rather than deleted, because a reader needs to know which parts
of the argument are load-bearing and which are not.

Companion to the published page at
`claude.ai/code/artifact/39809a92-7eba-4674-b7d4-bd264822c199`. This file is the evidence;
that page is the argument.

---

## The position in three sentences

Every code map in this market is built by **matching names**, not resolving types, and none
of the vendors documents that limit. The map itself is taken — CodeGraph reached 66k stars
in seven months with the framework resolvers we were about to build already shipped. What
remains unowned is **confidence on the edges**, which is verified as a real defect by one
user against ground truth and wanted, so far, by that one user.

---

## Verification standard used

| Status | Means |
|---|---|
| **VERIFIED** | Read from the vendor's own documentation, the GitHub API, or executed locally |
| **QUOTED** | Verbatim from a primary source, quote checked against the source text |
| **MEASURED** | Produced by running code during this session, with the command recorded |
| **UNVERIFIED** | Could not be confirmed; stated as unconfirmed wherever it appears |
| **REJECTED** | Was believed, then checked, then found false — listed in “Claims that did not survive” |

---

## 1. No shipping reviewer can say “I could not analyse this”

| Tool | What it emits | Analytical “could not analyse”? | Status |
|---|---|---|---|
| Cursor Bugbot | `success`, `neutral`, `failure` | **No** | VERIFIED — `cursor.com/docs/bugbot` |
| Qodo | severity-ranked findings | **No** | VERIFIED — `docs.qodo.ai/code-review` |
| Greptile | confidence 0–5, P0/P1/P2 | **No** — `Failed` means the run broke | VERIFIED — `greptile.com/docs/code-review/first-pr-review` |
| CodeRabbit | 5 severities, 6 categories | **Administrative only** — draft, paused, ignored title | VERIFIED — `docs.coderabbit.ai/pr-reviews/walkthroughs` |
| GitHub Copilot | always a “Comment” review | **No** | VERIFIED — GitHub Docs, Copilot code review |
| Graphite | “less than 5% negative comment rate” | **No** — no blind spots or thresholds documented | VERIFIED — `graphite.com/features/ai-reviews` |
| BreakBot | Success / Neutral / **Skipped** | **Yes** | VERIFIED — `github.com/break-bot/breakbot` |

**The defect in one line.** QUOTED, Cursor's own documentation:

> `neutral`: “Bugbot found issues, the run was cancelled by a newer commit, **or Bugbot hit
> an internal error**.”

Three different situations, one signal. Cursor also states outright: *“Bugbot does not emit
a `skipped` conclusion.”*

**Qodo deletes uncertainty rather than reporting it.** QUOTED: a judge agent filters
*“anything low-confidence before it reaches the pull request.”*

**The one tool that typed absence is dead.** BreakBot: ISC licence, **8 stars**, last code
push **2023-12-16**, clients supplied by hand rather than derived — *“supplied manually as a
list of GitHub repositories”*, with auto-discovery listed as future work. VERIFIED via
GitHub API. Its “3 of 30 clients” denominator is therefore **configured, not computed**.

---

## 2. Copilot already ships the coverage line, with a false reason

Source: GitHub community discussion **#152385**, opened 2025-02-25 by `tallior`, **12
comments**, last activity **2026-02-16**, no GitHub staff response. Retrieved via GitHub
GraphQL API, not a summary. All QUOTED:

- `tallior`: *“Copilot reviewed 5 out of 15 changed files in this pull request and generated
  no comments.”* Skipped files were `.cs`. *“The reason provided is Evaluated as low risk”*
- `guzelgun`: *“Copilot reviewed 120 out of 120 changed files… and generated 1 comment.”*
- `armsnyder`: a large Go file was not reviewed though the count claimed otherwise — *“I
  wonder if Copilot is not opening the diff if it is too large?”* — **458 LOC**, and Copilot
  chat could not see the file either
- `divinity76`: Copilot reported 1 of 2 files while the review text proved it read both —
  *“seems like it's just a bug in the counter?”*
- `douglasg14b`: *“it says it reviewed essentially all the files. But only shows a summary
  for like 2/100.”*
- `nnellanspdl` cites GitHub's own **Limited scope** page: *“only designed to identify a
  limited, fixed set of code quality issues.”*

**Three distinct failures wear one label**: genuine skips, size-driven skips, and a count
that is wrong in both directions.

**GitHub documents the exclusion list but no size limit.** VERIFIED: 40+ named files plus
patterns `**/*.svg`, `**/*.lock`, `**/node_modules/**`, `**/vendor/**`, `**/generated/**`,
`**/*.min.js`, `**/*.d.ts`. Nothing documents whether the user is told a file was skipped.

**Demand signal in that thread points the other way.** Nobody asks for reasons. `Frank-Buss`
asks *“Would it be possible to pay more for a full review?”* Every expressed want is **more
review**, not better reporting of absence.

---

## 3. The map is taken

`github.com/colbymchenry/codegraph`, VERIFIED via GitHub API 2026-08-12:

| Metric | Value |
|---|---|
| Stars | **66,097** |
| Forks | 4,164 |
| Created | 2026-01-18 |
| Last push | 2026-08-08 |
| Open issues | 411 |
| Licence | MIT |

QUOTED description:

> “Pre-indexed code knowledge graph, auto syncs on code changes, for Claude Code, Codex,
> Gemini, Cursor, OpenCode, AntiGravity, Kiro, and Hermes Agent — fewer tokens, fewer tool
> calls, 100% local”

**The Flask resolver is already shipped there.** VERIFIED by reading
`src/resolution/frameworks/python.ts` from the repository:

- line 4: *“Handles Django, Flask, and FastAPI patterns.”*
- line 11 `djangoResolver`, line 179 `flaskResolver`, line 232 `fastapiResolver`
- Flask decorator match: `/@(\w+)\.route\s*\(\s*['"]([^'"]*)['"](?:\s*,\s*methods…)?\)/g`
- comment: *“the handler is the next `def`, allowing intervening decorators
  (`@login_required`) and stacked `@x.route()` lines”*
- plus `extractFlaskRestful` for Flask-RESTful, and Django `path`/`re_path`/`url` plus DRF
  `router.register`

Sibling resolvers in the same directory: `express.ts`, `laravel.ts`, `java.ts`, `nestjs.ts`,
`go.ts`, `goframe.ts`, `csharp.ts`, `react.ts`, `react-native.ts`, `astro.ts`, `play.ts`,
`drupal.ts`, `cics.ts`, `fabric.ts`, `expo-modules.ts`, `cargo-workspace.ts`.

**Coverage is their stated thesis, not a side effect.** The source is a file in **their**
repository, not ours — which is why the citation guard is suppressed on the path line below
rather than the path being softened into something unfindable:

`colbymchenry/codegraph` → `docs/design/dynamic-dispatch-coverage-playbook.md` <!-- citation:allow external repo -->

> “systematically close static-extraction coverage holes for **dynamic dispatch** across
> **every language and framework** codegraph supports”

> “the lever for sufficiency is **coverage**, not prompting/hooks/new-tools: when a flow is
> missing from the graph, the agent reads the files to reconstruct it; when the flow is in
> the graph, the agent can answer completely without reading.”

Their backlog is organised *by indirection shape, not language×framework* — Redux, RTK
Query, NgRx, MediatR, **registries**. The last is the `REGISTRY[k]` mechanism recorded in
`PHASE0_PREREGISTRATION.md` amendment A50.

**The academic path is equally crowded.** VERIFIED via publisher pages: PyCG is archived;
JARVIS reports *“at least 67% faster in time, 84% higher in precision, and at least 20%
higher in recall”* over PyCG; InferCG (TOSEM, 2026) reports **+13.9% average recall** and
**+5.0% F1** over PyCG using LLM filtering of a high-recall candidate set.

**Consequence.** `AGENTS.md` states: *“We do not build a graph. Upstream MIT projects ship
daily and we cannot outrun them.”* That principle now has a name, a number and a date.

---

## 4. Our own Flask measurement — what it proves and what it does not

MEASURED 2026-08-12. Probe at `scratchpad/flask_probe.py`, run against
`DogukanUrker/FlaskBlog` at four corpus parent commits via
`phase0.pipeline.worktree.cloned`, scope from `phase0.scope.resolve`, sites from
`phase0.census.count_call_sites`, symbol match via `phase0.classify_exposure._matches`.

```
changed symbols measured        : 12
Tier 0 BEFORE (no static caller): 11
Tier 0 AFTER  (flask resolver)  :  1
converted by @route             : 10   (91% of Tier 0)
```

Every conversion is a real Blueprint route named in source — `@indexBlueprint.route('/')`,
`@editPostBlueprint.route('/editpost/<urlID>')`, `@adminPanelUsersBlueprint.route(…)`.

**What it proves:** the mechanism converts, deterministically, with no model in the loop.

**What it does not prove:** anything about a rate. **n = 1 repository**, 4 PRs, 12 symbols,
and FlaskBlog is close to a best case — a small Flask blog where nearly every PR edits a
route handler. **91% must not be quoted as a corpus rate.**

**And it buys no differentiation**, because the capability ships in CodeGraph — see
“The map is taken” above.

**Recorded because it nearly shipped as a null.** The probe's first run reported **0%
converted**. `scope.module_of` is relative to `package_root` and drops the package name, so
a handler resolved to `index.index` against a corpus symbol of `app.routes.index.index`. An
exact comparison matched nothing and read exactly like a clean negative. What caught it was
the asymmetry — **31 route decorators found, 0 matched**. The fix uses A9's dot-bounded
matcher rather than a rule invented for the probe.

**The one non-conversion is a Flask hook, and was not chased.** `app.app.afterRequest` is
`@app.after_request`; the same file holds three `@app.errorhandler(...)` functions. The
decorator set was fixed before the run. Extending it after seeing the result would be tuning
a constant to improve a number, so it stays a separate untested extension with a stated
prediction of 11 of 11.

---

## 5. The wedge: confidence on edges

Every graph in this market matches **names**, not types. In a dynamic language a name is
sometimes all the information that exists, so this is not a removable bug. The defect is
what the tool *says* about it.

Source: CodeGraph issue **#765**, opened **2026-06-09**, VERIFIED still **open** with **1
reaction** and **1 comment** as of 2026-08-12. The author ran head-to-head comparisons
against **ground truth** on ~1,100 Swift files plus TypeScript/React and Python, ~17k nodes.

All QUOTED:

> “Cross-file edges conflate same-named symbols. Examples we hit: a Swift method named
> `matches` reported as called from an unrelated package's phonemizer code (different
> `matches`); React `render`/`Layout` edges surfacing in the relationships section of a
> Swift-only query.”

> “…the instructions actively tell agents the opposite: **“Trust codegraph's results — don't
> re-verify them with grep… They come from a full AST parse”**, **“PRIMARY — call FIRST… most
> often the ONLY call you need”**. An agent following that takes name-collision edges at face
> value and builds conclusions on them.”

> “the ‘no covering tests found’ annotation produced **false negatives** for symbols that do
> have covering tests.”

Their own correction: *“it's tree-sitter name-matching across files, not type-resolved.”*
Their workaround: patching `dist/mcp/server-instructions.js` in the installed package, which
*“silently reverts on every update.”*

**Read against ourselves.** `classify_exposure._matches` performs dot-bounded name matching
too. Our edges are not more accurate. The difference is that ours are required to carry a
label — `AGENTS.md` non-negotiable, *“Never emit an unlabeled edge”*, with
`Confidence.RESOLVED` requiring two independent resolvers agreeing — while theirs carry an
instruction to trust them.

### Why the incumbents will not fix it

Not an oversight; an economic decision. Each competes on a number that admitting uncertainty
damages. Graphite markets a *“less than 5% negative comment rate”*. CodeGraph markets
*“fewer tokens, fewer tool calls”*. An “I am not sure” output is a comment nobody acts on and
a tool call nobody wanted.

**This is a barrier to entry, not a moat.** A barrier is only worth something once there is
a market behind it, and “The demand counterweight — the strongest evidence against
everything above” says there may not be. The earlier draft of the published page used the
word *moat*; that was an overstatement and is corrected here.

### Where the damage actually bites

In a **reviewer**, a wrong edge becomes a wrong comment — visible, dismissable, and it counts
against the precision the vendor advertises. A bad edge punishes them.

In an **agent-facing graph**, a wrong edge becomes a confident wrong answer. No human sees
the edge, only the conclusion built on it. That is why #765 is in CodeGraph's tracker and not
in CodeRabbit's, and it is the reason the wedge is agent-facing rather than PR-facing.

---

## 6. The demand counterweight — the strongest evidence against everything above

**In CodeGraph's own tracker**, VERIFIED 2026-08-12:

| Issue | Reactions |
|---|---|
| #649 Tracking: agent / IDE install-target requests | **44** |
| #648 Tracking: language support requests | **32** |
| #689 Homebrew tap support | 13 |
| #499 Extra search/indexing paths | 12 |
| #781 NixOS packaging | 7 |
| **#765 edge reliability overstated** | **1** |

Demand is for **breadth and packaging**. The calibration issue is last.

**In the literature**, QUOTED from a review of six static-analysis usability surveys — the
largest sending to 2,000 developers for 375 responses:

> “To build trust in their analyzers, tool designers should keep in mind that developers care
> much **more about too many false positives than too many false negatives**.”

Among **15 ranked pain points, “misses too many issues” placed 14th**, ahead only of “not
cross platform”. Johnson et al. (ICSE 2013) interviewed 20 developers; **14 of 20** named
*warning presentation* as the barrier, not detection rate.

A declared blind spot is a declared false negative — the category developers rank second to
last.

**Countervailing context**, VERIFIED — Sonar State of Code, 8 January 2026, 1,100+
developers: **96%** do not fully trust AI-generated code, **48%** always verify before
committing, **38%** say reviewing AI code takes *more* effort than human code. The
verification burden is real. Appetite for more warnings is not established.

---

## 7. Adopt / refuse

### Adopt

| Source | What | Why |
|---|---|---|
| Codecov | Sectioned PR comment, **non-blocking** | A decade of developers tolerating a coverage number in a PR. Docs show no merge-blocking behaviour |
| Greptile, CodeRabbit | **One number at the top** | 0–5 and effort 1–5; independently converged, for a two-second triage decision |
| CodeRabbit | **Grouped rows** | *“one source file and 27 localization files produces two rows”* |
| CodeRabbit | **Action without context switch** | *“no copy-paste, no switching contexts”* |
| CodeRabbit | **Sections as independent flags** | Ten toggles → a team mutes one section, not the tool |
| BreakBot | **Typed run states** | Success / Neutral / **Skipped** — the only prior art |
| MCP | The channel | Supported by Claude Code, Cursor, Copilot, Codex, Windsurf, Zed, Continue, Cline, Goose |
| CodeRabbit | **The poem** | Zero utility, most-discussed feature they ship. Delight is uncontested |

### Refuse

| Source | What | Why |
|---|---|---|
| Bugbot | `neutral` conflating found-issues with internal-error | Copying it refutes the product |
| Qodo | Judge agent deleting low-confidence findings | The inverse of the thesis |
| Copilot | “Evaluated as low risk” for unopenable files | A capacity failure wearing a judgement label |
| CodeGraph | *“don't re-verify them with grep”* | Never remove the user's last check |
| Codecov | `require_changes: false` — always post | Posting when nothing changed is how you get collapsed. Stay silent at full coverage |
| Greptile, CodeRabbit | Always-on diagrams and sections | Generate nothing that was not earned |
| All | A marketed precision number | Four vendors each claim #1 on the same benchmark; Graphite's “negative comment rate” is its own coinage |

---

## 8. Claims that did NOT survive verification

Recorded because the reasoning around each was sound and the figure underneath was never
sourced. Same defect class as `CORRECTIONS.md`.

| Claim | Reality | How caught |
|---|---|---|
| “Four named false-positive mechanisms” in our corpus | **REJECTED.** No such taxonomy exists. A10 records a *capability profile of the exposure classifier* — four ways a caller can be unresolvable — not a taxonomy of wrong review comments | Read `PHASE0_PREREGISTRATION.md` A10 |
| “`enclosing == None` on 76% of call sites” | **REJECTED.** `census.py` types it `str`; `_qualify` returns `module or enclosing`, never `None`. Measured **0.00% empty** across 1,680 sites with a module supplied, which `pipeline/measure.py` always supplies. Worst case with the test-only default is 5.12% | Ran the census locally |
| “Corpus files sit outside their package root” | **REJECTED.** Zero, structurally: `resolve()` sets `root` then takes `iter_python_files(root)`, so `relative_to` cannot raise. The `return ""` branch is unreachable for scope files | Read `scope.py`, measured 296 files |
| BreakBot “appears actively maintained” | **REJECTED.** Last push 2023-12-16; only metadata updated since | GitHub API `pushed_at` |
| BreakBot clients from “declared Maven dependencies” | **REJECTED.** *“supplied manually as a list of GitHub repositories”*; auto-discovery is future work | Read the README |
| Greptile “generates diagrams for every PR” complaint | **UNVERIFIED.** No such evaluation found. Greptile's docs say *“For minimal or trivial changes, no diagram is generated”* | Searched; source never located |
| Greptile “comments only appeared in this summary” complaint | **UNVERIFIED.** Source never located | Searched |
| “Copilot reviewed 115 out of 191 files” | **REJECTED.** Appears nowhere in discussion #152385. Introduced by a page summariser | Pulled the thread via GraphQL |
| “38% of Tier 0 is framework-registered, n=8” | **UNVERIFIED.** Hand-classified, no artefact in the repository | Searched the repo |
| Gemini critique: GPU-agnostic inference system, aerospace-thermodynamics co-founder search | **UNVERIFIED.** No mention in this repository, `AGENTS.md`, or the two planning documents then present and since deleted as dead-product records. The “vision disconnect” argument rests entirely on it | Searched the repository |

---

## 9. What the evidence says to do

1. **Do not build framework resolvers as differentiation.** Shipped in CodeGraph — see
   “The map is taken” — confirmed by reading their source.
2. **Do not compete on finding more bugs.** Field precision runs roughly 50–76%; our own
   correlation is null — RR 1.040, cluster-robust CI [0.598, 1.890]
   (`PHASE0_PREREGISTRATION.md`, Results, Python arm).
3. **Every claim is a coverage claim, never a risk claim.** *“We did not check these six
   places”* is defensible. *“These six places are dangerous”* is falsified by our own null.
4. **Invert the validation target.** Do not test demand by contacting the author of #765 —
   they wrote it, so they will agree, and that is confirmation rather than evidence. Contact
   people who upvoted **#649** and **#648** and ask what they do when the graph gives them a
   wrong caller. Indifference is the finding being looked for.
5. **Consuming CodeGraph does not require their plugin API.** It is MIT and its index is a
   local SQLite graph, so the dependency is weaker than a platform bet — though the risk that
   they implement edge labelling themselves is real and unmitigated.

---

## 10. What remains unanswered

**Whether anyone will pay for typed uncertainty.** No corpus work can answer it. The
strongest evidence for it is one issue with one reaction; the strongest evidence against it
is 44 reactions on a packaging request and a literature finding placing this category 14th
of 15.

That is the whole of what remains to decide.
