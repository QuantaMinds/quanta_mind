# Architecture

> **STATUS: PROVISIONAL.** This document describes a system whose founding assumption has
> not been measured. Until `docs/findings/PHASE0_PREREGISTRATION.md` has a filled Results
> section with a non-null verdict, treat everything here as a draft that survives only if
> the correlation clears RR ≥ 3.0. **No product code is written before that.**
>
> Read this before your first change. It explains the layering, the contracts between
> layers, and the reasoning behind every stack choice. If something here contradicts the
> code, the code is wrong or this file is stale — fix one of them in the same PR.

---

## 0. Scope decisions — what we deliberately do not build

Recorded at the top because they are the two most likely things to be reversed by
enthusiasm. Reversing either requires a PR that re-argues it.

### 0.1 We do not build a call graph

Graphify, CodeGraph and GitNexus hold ~165k GitHub stars between them, are MIT or
near-MIT, ship over MCP, and iterate faster than three people can. **We consume one.**
`ingest/` adapts an upstream graph and adds a thin call-site census, because upstream
tools emit edges but none emits the *denominator* — and the denominator is coverage.

Every improvement they ship improves our product. Competing with them is a feature race
we lose.

### 0.2 We do not build a runtime oracle in v1

~180× tracing overhead, a dynamic graph ~12% the size of the static one at 82% statement
coverage, and ~59% of what it recovers is builtins we discard. The economics do not close,
and designing around a layer that will not ship distorts everything upstream. **Removed,
not deferred.** Revisit only if PyXray's "no inputs required" claim survives verification.

**What remains is `probe/` + `label/` over someone else's graph** — roughly 800 lines and
one number. That is the entire defensible surface.

### 0.3 Delivery is pull, never push — and this is load-bearing

SWE-PRBench (arXiv 2603.26130) measured 8 frontier models across three context
configurations and found all of them degrade as structured context is added, *"even when
context is provided via structured semantic layers including AST-extracted function context
and import graph resolution."* Cause identified: attention representation, not content
selection. Not a length effect — configs A and C differ by 500 tokens.

**That is our Oracle 1 + Oracle 2, delivered in-prompt, making review worse.**

Architectural consequence, binding on every surface in `serve/`:

- The MCP server answers **specific queries**. It never emits a context blob.
- `callers_of(symbol)` returns the edges for that symbol. Not the file. Not the module.
- PR comments carry the blast radius for changed symbols only, never a coverage dump.
- **Anything that resembles "here is more context, good luck" is forbidden by this section.**

Whether pull-based delivery actually escapes the effect is **untested** — see
`docs/BUILD_PLAN.md` the pull-based retrieval test, which measures it against their public harness before any
code in `serve/` is written.

### 0.4 Languages: Python and TypeScript/JavaScript only

Nothing else until both arms of the correlation test report. The architecture below the probe layer is
language-agnostic; `probe/` is not, and each language is a separate research problem rather
than a new adapter. Rust and Go are explicitly excluded as lead products: their residual is
small enough that a coverage number would read 95%+ and carry no information.

---

## 1. What the system does, in one paragraph

`quantamind` reads a repository, builds a call graph using several independent resolvers,
records **which resolver produced each edge and which call sites no resolver could
handle**, and serves that labeled graph to AI coding agents over MCP. The differentiator
is not the graph. Free tools already build graphs. The differentiator is that every answer
carries a confidence label and every gap is named. Source code never leaves the customer's
network; only derived facts are stored.

---

## 2. Why this design (the three findings it rests on)

| Finding | Source | Design consequence |
|---|---|---|
| All practical static analysis is deliberately unsound; no sound whole-program analyzer exists for any mainstream language | *In Defense of Soundiness*, CACM 2015 | We never claim completeness. Coverage is a first-class output. |
| Soundness → imprecision → unscalability is a causal chain | ibid. | We do **not** try to build a more complete general analyzer. We add narrow resolvers where the answer is structurally guaranteed. |
| Soundness is unnecessary for IDE-class clients | ibid. | An AI agent is an IDE-class client. Our target is *calibration*, not soundness. |
| Static Python call graphs miss ~51% of observed runtime edges — but ~59% of the misses are builtins and ~12% are name-resolution artifacts | DyPyBench, FSE 2024 | Builtins are filtered out of coverage math. Name normalization is its own module, not an afterthought. |
| PyCG produced no graph at all for 11 of 50 projects (timeout / 60GB OOM / crash) | DyPyBench | Entry-point-scoped analysis is mandatory. `UNANALYZED` is a real label. |
| Judge (ISSTA'19) measures unsoundness as *capability profile × feature prevalence* | Reif et al. | Our coverage score uses the same decomposition. Neither half needs ground truth on customer code. |

Full reasoning and citations: `docs/PROJECT_CONTEXT.md`.

---

## 3. Layers

Strict left-to-right dependency. A layer imports only from layers to its left.
Enforced by `scripts/guard/check_conventions.py`.

```
types → discover → ingest → resolve → probe → label → store → serve
                            (the MRO and framework resolvers, optional)
```

`resolve/` sits between `ingest/` and `probe/`: it may consume the upstream graph and adds
narrow recovery on top, but nothing downstream distinguishes an edge by which of the two
produced it — that is what `Provenance` is for.

**The order is declared once, in `discovery.LAYER_ORDER`, and that declaration is
authoritative.** It has previously appeared three different ways across this file,
`AGENTS.md` and the guard's own docstring — including a `parse` layer that
`docs/BUILD_PLAN.md` had deleted. A layering guard reading one order while the
documentation states another is a guard that passes while enforcing the wrong thing.

### `discover/` — what is this repository?
Walks the tree. Detects language, Python version, frameworks (Django / Flask / FastAPI /
Celery / SQLAlchemy / pytest), package layout, entry points, test command.
**Output:** `RepoProfile` (frozen dataclass).
**Must not:** parse code, run anything, touch the network.

### `ingest/` — the graph, and the denominator
Two jobs, deliberately paired because they must agree on symbol identity.

1. **Adapt an upstream graph.** One adapter per source (`codegraph.py`, `graphify.py`,
   `pycg.py`), behind a single `GraphSource` protocol. Swapping adapters must change the
   edges and leave the coverage arithmetic untouched — that is a the call-site census layer gate.
2. **Call-site census.** A thin tree-sitter pass counting *every* call site, including
   ones nothing resolves. Upstream tools emit edges; none emits the denominator, and
   without a denominator there is no coverage number.

**Output:** `Graph` (edges from upstream) + `CallSite[]` (ours).
**Must not:** attempt resolution, rank edges, or improve on upstream. If an adapter starts
growing resolution logic, that logic belongs in `resolve/` and must be argued for.
**Why this is not `parse/` + `resolve/static.py`:** see `ARCHITECTURE.md` “We do not build a call graph”. Building our own graph is a
race against 165k stars of MIT code shipping daily.

### `resolve/` — narrow recovery only (the MRO and framework resolvers, conditional)
Exists **only** for edges upstream tools structurally cannot produce, and only where the correlation test
exposure data shows the risk concentrates.

| Resolver | Mechanism | Handles |
|---|---|---|
| `mro.py` | AST + class graph | `super()` chains — PyCG misses these entirely |
| `frameworks/django.py` | `urls.py`, signals, admin registry | URL→view, signal→receiver |
| `frameworks/celery.py` | task registry | string-dispatched tasks |
| `frameworks/sqlalchemy.py` | relationship declarations | ORM lazy edges |
| `frameworks/pytest.py` | fixture graph | fixture→test |

Each resolver returns `(edges, unresolved)`. **Returning fewer edges is legitimate.
Returning a guess is not.**
**Must not:** call an LLM; duplicate what the upstream graph already resolves; or attempt
general-purpose analysis. Soundness → imprecision → unscalability is causal (`ARCHITECTURE.md` “Why this design”). Narrow
resolvers escape that chain because framework semantics *guarantee* the answer; a general
analyzer does not.
**Deleted by decision:** `static.py` (upstream's job) and `runtime.py` (`ARCHITECTURE.md` “We do not build a runtime oracle in v1”).

### `probe/` — where is this repo unknowable?
The Python row of the soundiness table, which does not exist in the literature. Scans for
constructs known to defeat static analysis: `eval`, `exec`, computed `getattr`/`setattr`,
`importlib`, metaclasses, `__getattr__`, registering decorators, monkeypatching, C
extensions, `globals()`/`locals()`.
**Output:** `FeatureHit(site, feature, confidence_impact)`.
This is the prevalence half of the Judge decomposition and it is the module a competitor
cannot copy from a paper, because nobody has written it for Python.

### `label/` — what do we claim, and how sure are we?

```python
class Confidence(Enum):
    RESOLVED   = "resolved"    # ≥2 independent resolvers agree
    FRAMEWORK  = "framework"   # single framework resolver, structurally guaranteed
    RUNTIME    = "runtime"     # observed executing; never a false positive
    AMBIGUOUS  = "ambiguous"   # multiple candidates, cannot disambiguate
    UNTESTED   = "untested"    # static only, never observed running
    UNRESOLVED = "unresolved"  # no resolver could handle it — reason attached
    UNANALYZED = "unanalyzed"  # analysis timed out / OOM'd on this region
```

`coverage(region) = (resolved + framework + runtime) / total_call_sites`, with builtin
calls excluded from both numerator and denominator — DyPyBench showed they are ~59% of the
apparent gap and are useless to a developer.

### `store/` — the pack
SQLite, versioned schema, pinned to a commit SHA. Per-directory staleness, never global.
Contains symbol names, edges, labels, coverage. **Never source text, never argument
values.** That constraint is architectural, not configurable — it is what removes the
security review from the sales cycle.

### `serve/` — the surfaces
1. **MCP server** (primary) — `callers_of`, `reaches`, `coverage`, `unresolved`
2. **PR comment renderer** — blast radius per changed symbol
3. **Localhost read-only view** (`127.0.0.1`) — debugging and demos only, not a product

---

## 4. Tech stack, and why each choice

| Concern | Choice | Why this and not the alternative |
|---|---|---|
| Language | **Python 3.12+** | The thing we analyze is Python; resolvers need `ast`, `symtable`, `importlib`. 3.12 gives us `sys.monitoring`, which is dramatically cheaper than the source-rewriting instrumentation DyPyBench measured at ~180× overhead. |
| Packaging | **uv** | Deterministic, fast, single tool for venv + lock + run. |
| Call-site census | **tree-sitter** (vendored grammars) | Thin pass, ours. Produces the coverage denominator, which no upstream tool emits. Grammars pinned — a bump silently changes parse trees. |
| Call graph | **upstream, via adapter** (CodeGraph / Graphify / PyCG) | See `ARCHITECTURE.md` “We do not build a call graph”. We do not build a graph. PyCG remains a supported adapter and is what the correlation test measures with, because it is the crudest and therefore the conservative instrument. |
| Storage | **SQLite** (embedded) | Local-first, zero-ops, no server, ships inside the customer boundary. The winning pattern in this category. |
| Serving | **MCP over stdio + local HTTP** | One integration serves Claude Code, Codex, Cursor. Survives any single vendor shipping its own indexer. |
| CLI | **Typer** | Type-hint driven, matches the mypy-strict discipline. |
| Lint / format | **ruff** | Replaces flake8 + isort + black. |
| Types | **mypy --strict** | Non-negotiable for a correctness product. |
| Tests | **pytest** + **hypothesis** | Property tests matter here: graph invariants (no unlabeled edge, coverage ∈ [0,1], layering acyclic) are exactly what property testing is for. |
| Task runner | **just** | `justfile` is readable; make is not. |
| CI | **GitHub Actions** | Where the guards live. |

**Deliberately not used:** vector databases (code drifts, embeddings leak, and Anthropic
publicly abandoned this path); Neo4j (an external server breaks the local-first
constraint); LangChain (we make no LLM calls in the core pipeline); Rust (revisit only if
The label layer profiling shows tree-sitter binding overhead dominates — do not pre-optimize).

---

## 5. Repository layout

Directories marked ⏳ are declared here but do not exist yet — they arrive in the phase that
authorises them. `docs/CODEBASE.md` describes what is on disk today.

```
quanta_mind/
├── AGENTS.md                  agent memory, ≤200 lines
├── CLAUDE.md                  one line: @AGENTS.md  (committed, NOT a symlink —
│                              `ln -sf` needs Developer Mode on Windows and fails silently)
├── ARCHITECTURE.md            this file
├── BRIEFING.md                founder-facing: the pitch, the risks, the five questions
├── README.md
├── CONTRIBUTING.md            branch and PR protocol, prerequisites
├── justfile                   requires bash — Git Bash on Windows
├── pyproject.toml             every version pinned exactly
├── src/quantamind/
│   ├── __init__.py            ⏳ the only file until the correlation test reports
│   ├── types/                 ⏳ shared frozen dataclasses and enums
│   ├── discover/              ⏳ ≤15 files
│   ├── ingest/                ⏳ upstream graph adapters + call-site census
│   ├── resolve/               ⏳ the MRO and framework resolvers only, narrow recovery
│   │   └── frameworks/        ⏳ one file per framework
│   ├── probe/                 ⏳
│   ├── label/                 ⏳
│   ├── store/                 ⏳
│   └── serve/                 ⏳
├── tests/
│   ├── conftest.py            puts scripts/guard on sys.path
│   ├── unit/                  fast, hermetic
│   ├── property/              hypothesis invariants
│   ├── live/                  ⏳ real pipeline, real repos, golden files
│   ├── adversarial/           ⏳ fault injection, `VALIDATION.md` “Fault injection”
│   └── fixtures/              ⏳ repos/ (submodules) + golden/
├── research/                  measurement, NOT the product
│   └── phase0/                standalone uv project: own lock, own interpreter (3.10)
│       ├── ENVIRONMENT.lock   read this before touching the instrument
│       ├── src/phase0/        15 modules + pipeline/ subpackage
│       ├── tests/             125 tests
│       ├── data/              gitignored — raw jsonl
│       └── results/           committed — the published artifact
├── scripts/
│   ├── guard/                 the enforcement layer, stdlib only
│   └── verify/                ⏳ the call-site census layer — see its README for why it is empty
├── .claude/settings.json      hooks; inert if moved back to the root
├── .github/workflows/         ci.yml + guards.yml
├── docs/
│   ├── PROJECT_CONTEXT.md     research + business + competitors
│   ├── BUILD_PLAN.md          phased plan with gates
│   ├── VALIDATION.md          anti-silent-failure doctrine
│   ├── CODEBASE.md            folder-wise map, updated every PR
│   ├── findings/              PHASE0_PREREGISTRATION.md, PHASE0_RUNBOOK.md
│   └── plans/                 per-branch design notes, session records
└── vendor/                    ⏳ pinned third-party source (grammars)
```

---

## 6. Invariants (property-tested, not just asserted)

1. Every edge has a `Confidence` and a non-empty `Provenance`.
2. `coverage ∈ [0, 1]` for every region, always.
3. `resolved + framework + runtime + ambiguous + untested + unresolved + unanalyzed`
   equals total non-builtin call sites. Nothing is lost.
4. The layer import graph is a DAG with the declared topological order.
5. Re-indexing an unchanged commit produces a byte-identical pack.
6. The pack contains no substring longer than 40 chars matching any source file line.
   *(This is how we prove "we never store code" rather than assert it.)*

---

## 7. Known limitations — state these to customers before they find them

- **The founding correlation is unmeasured.** Until the correlation test reports, we do not know that
  `unresolved` predicts breakage. Do not claim it to a customer.
- **The delivery mechanism is unvalidated.** Structured context degrades review quality when
  pushed into a prompt (`ARCHITECTURE.md` “Delivery is pull, never push”). We assume pull-based tool calls behave differently. The pull-based retrieval test
  measures it. Until then this is a hypothesis, and it should be stated as one.
- Our coverage is inherited from the upstream graph's limits plus our own resolvers'.
  When upstream regresses, our numbers move. Adapter versions are pinned and recorded in
  every pack for exactly this reason.
- There is **no runtime oracle in v1** (`ARCHITECTURE.md` “We do not build a runtime oracle in v1”). Coverage reflects what is statically
  knowable, not what actually executes. Say so.
- `eval`, computed identifiers, deploy-time plugin loading and C extensions are
  **undecidable**, not unimplemented. They will always land in `UNRESOLVED`.
- Coverage is a measure of *our* certainty, not of *code quality*. A 100%-coverage module
  can still be terrible code.
