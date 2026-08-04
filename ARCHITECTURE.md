# Architecture

> Read this before your first change. It explains the layering, the contracts between
> layers, and the reasoning behind every stack choice. If something here contradicts the
> code, the code is wrong or this file is stale — fix one of them in the same PR.

---

## 1. What the system does, in one paragraph

`qmctx` reads a repository, builds a call graph using several independent resolvers,
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
Enforced by `scripts/guard/check_layering.py`.

```
discover → parse → resolve → probe → label → store → serve
```

### `discover/` — what is this repository?
Walks the tree. Detects language, Python version, frameworks (Django / Flask / FastAPI /
Celery / SQLAlchemy / pytest), package layout, entry points, test command.
**Output:** `RepoProfile` (frozen dataclass).
**Must not:** parse code, run anything, touch the network.

### `parse/` — what symbols and call sites exist?
tree-sitter over every source file. Produces symbol definitions, import statements, and
**every call site**, including ones we cannot resolve. Counting call sites is how we get a
denominator; without it there is no coverage number.
**Output:** `ParseUnit` per file → `SymbolTable`, `CallSite[]`.
**Must not:** attempt resolution. Parsing and resolving are different jobs.

### `resolve/` — which call site points where?
Independent resolvers, each declaring what it can and cannot handle:

| Resolver | Mechanism | Handles |
|---|---|---|
| `static.py` | vendored PyCG fork, entry-point scoped | direct calls, imports, closures |
| `types.py` | pyright / LSP | cross-file resolution, inheritance, generics |
| `mro.py` | AST + class graph | `super()` chains (PyCG misses these entirely) |
| `frameworks/django.py` | `urls.py`, signals, admin registry | URL→view, signal→receiver |
| `frameworks/celery.py` | task registry | string-dispatched tasks |
| `frameworks/sqlalchemy.py` | relationship declarations | ORM lazy edges |
| `frameworks/pytest.py` | fixture graph | fixture→test |
| `runtime.py` | `sys.monitoring` trace, nightly | anything the tests actually executed |

Each resolver returns `(edges, unresolved)`. **Returning fewer edges is legitimate.
Returning a guess is not.**
**Must not:** call an LLM. Resolution is deterministic. (LLM candidate filtering is a
future `resolve/llm.py`, and it will be gated behind an explicit confidence downgrade.)

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
| Parsing | **tree-sitter** (vendored grammars) | Incremental, error-tolerant, multi-language. Grammars are pinned because a grammar bump silently changes parse trees. |
| Static CG base | **fork of PyCG** (vendored) | Pure Python, zero dependencies, MIT, and upstream is archived with forks explicitly invited. Its weaknesses are documented (flow-insensitive, analyzes unreachable dependencies, OOMs past ~2k LOC unscoped). We fix entry-point scoping first. Evaluate Jarvis as an alternative base — see `docs/BUILD_PLAN.md` Phase 1. |
| Type resolution | **pyright** via LSP | Best-in-class Python inference, runs as a subprocess, no license entanglement. |
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
Phase 2 profiling shows tree-sitter binding overhead dominates — do not pre-optimize).

---

## 5. Repository layout

```
qmctx/
├── AGENTS.md                  (CLAUDE.md → symlink)
├── ARCHITECTURE.md            this file
├── README.md
├── CONTRIBUTING.md            branch and PR protocol
├── justfile
├── pyproject.toml
├── src/qmctx/
│   ├── discover/              ≤15 files
│   ├── parse/
│   ├── resolve/
│   │   └── frameworks/        one file per framework
│   ├── probe/
│   ├── label/
│   ├── store/
│   ├── serve/
│   └── types/                 shared frozen dataclasses and enums
├── tests/
│   ├── unit/                  fast, hermetic
│   ├── property/              hypothesis invariants
│   ├── live/                  real pipeline, real repos, golden files
│   └── fixtures/
├── scripts/guard/             the enforcement layer
├── docs/
│   ├── PROJECT_CONTEXT.md     research + business + competitors
│   ├── BUILD_PLAN.md          phased plan with gates
│   ├── VALIDATION.md          anti-silent-failure doctrine
│   ├── CODEBASE.md            folder-wise map, updated every PR
│   └── plans/                 per-branch design notes
└── vendor/                    pinned third-party source (pycg, grammars)
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

- Runtime coverage is bounded by the customer's test coverage, and test coverage skews
  away from the messy integration paths where agents break things. Our weakest oracle is
  thinnest at the highest-risk code. Say so.
- `eval`, computed identifiers, deploy-time plugin loading and C extensions are
  **undecidable**, not unimplemented. They will always land in `UNRESOLVED`.
- Coverage is a measure of *our* certainty, not of *code quality*. A 100%-coverage module
  can still be terrible code.
