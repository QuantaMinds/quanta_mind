# Build Plan

> Sequenced so that the cheapest thing that could kill the thesis is tested first.
> Every phase has a **gate** (what must be true to proceed) and a **kill criterion**
> (what result means stop). Do not start Phase N+1 until Phase N's gate is green.
>
> The single most valuable property of this plan is Phase 0. It costs two days and it can
> end the project. Run it before writing product code.

---

## Phase 0 — Prove the thesis (2 days, no product code)

**Question:** after excluding builtins and name-resolution artifacts, what fraction of the
edges static analysis misses are *framework idioms we can deterministically recover*?

The published finding is that static Python call graphs miss ~51% of observed runtime
edges, but that ~59% of the missing callees are builtin methods (`str.strip`) and ~12% are
fully-qualified-name mismatches. Neither is useful to a developer. **Nobody has classified
the remainder.** That classification is our founding number.

**Steps**
1. Pull the DyPyBench Docker image; reproduce the PyCG vs DynaPyt comparison.
2. Extract the set of dynamic-only edges.
3. Classify each: `builtin` / `name-artifact` / `framework-idiom` / `true-dynamism`.
4. Write up the distribution.

**Gate:** ≥40% of the non-builtin, non-artifact remainder is framework idiom.
**Kill criterion:** <20% framework idiom. If the residual is mostly `eval`-class true
dynamism, the recoverable ceiling is too low to build a company on. Stop, and publish the
result — it is a useful paper either way.

**Deliverable:** `docs/findings/phase0-edge-classification.md` + the raw data.

---

## Phase 1 — Choose the static base (3 days)

PyCG is archived, pure Python, zero-dependency, and its authors explicitly invite forks.
It is also flow-insensitive, analyzes unreachable dependencies, and failed outright on 11
of 50 DyPyBench projects (6 timeouts, 3 OOM at 60GB, 2 crashes). Jarvis reuses PyCG's code
and claims to fix scoping and precision. PyPt is a third option.

**Steps**
1. Run PyCG, Jarvis and PyPt against the JCG Python test adapters (they already exist at
   `github.com/opalj/JCG` — do not rebuild this).
2. Measure: which fails, on what, how fast, and how instrumentable each is.
3. Pick one. Vendor it under `vendor/`. Pin it.

**Gate:** the chosen base completes on all six live fixtures within 10 minutes each, with
entry-point scoping applied.
**Kill criterion:** none complete on the ≥1M-line fixture even when scoped. Then scale is
the product problem, not unsoundness, and the plan changes.

---

## Phase 2 — Skeleton + parse + store (1 week)

`discover/`, `parse/`, `store/`, and the CLI. No resolution yet.

**Why parse before resolve:** counting call sites gives us the coverage *denominator*. A
system that can honestly say "this file has 412 call sites and I resolved none of them"
is already more useful than one that silently returns an empty graph.

**Gate**
- `just check` green
- `just verify-determinism` green (3 runs byte-identical)
- `just verify-no-source-leak` green — invariant 6 proven, not asserted
- call-site counts match a hand-count on a 200-line fixture

---

## Phase 3 — The label layer (1 week)

`label/` and `types/`. `Confidence`, `Provenance`, `Unresolved`, coverage math with
builtins excluded from both numerator and denominator.

**Gate:** all six invariants from `ARCHITECTURE.md §6` pass as property tests. Specifically
invariant 3 (conservation) — no call site may vanish between stages.

**Note:** build this *before* the resolvers. If the labeling contract is added afterwards,
resolvers will have been written to return bare edges and you will retrofit provenance,
which is how default confidence values get introduced. That is silent failure #1.

---

## Phase 4 — Static + type resolvers (1 week)

`resolve/static.py` (vendored base, entry-point scoped) and `resolve/types.py` (pyright).

**Gate:** on the Flask fixture, every symbol has exactly one canonical FQN across both
resolvers — this is silent failure #4, and Flask is the repository where the published
mismatch was observed.

---

## Phase 5 — MRO and framework resolvers (2–3 weeks) ← **the moat**

In order of expected yield from Phase 0:
1. `resolve/mro.py` — `super()` chains. The static base misses these entirely, and they
   are pure inheritance structure, so recovery is exact.
2. `resolve/frameworks/django.py` — URL dispatch, signals.
3. `resolve/frameworks/celery.py` — task registry.
4. `resolve/frameworks/sqlalchemy.py` — relationships.
5. `resolve/frameworks/pytest.py` — fixtures.

**One resolver per PR. One branch per resolver.** Each ships with: a live test asserting a
minimum edge count on its fixture, and an entry in the capability profile.

**Gate per resolver:** coverage on its fixture increases, and no previously-`RESOLVED`
edge changes target. A resolver that *moves* existing edges is a regression, not a feature.

**This is the only phase a competitor cannot copy from a paper.** Everything before it is
assembly of published work. Budget accordingly.

---

## Phase 6 — The probe layer (1 week)

`probe/` — the Python feature-prevalence scanner. This is the half of the Judge
decomposition that does not exist for Python: JCG has Python *adapters* (capability
profiles), but the prevalence infrastructure is JVM-bytecode-specific.

**Deliverable that doubles as marketing:** the Python row of the soundiness table.
The 2015 manifesto's table covers C/C++, Java/C# and JavaScript. There is no Python row,
and the authors noted no reliable survey of dangerous-feature usage exists. Writing it is
a publishable original contribution regardless of whether the company works.

**Gate:** prevalence scan completes on the ≥1M-line fixture in under 60 seconds.

---

## Phase 7 — MCP server (3 days)

Four tools: `callers_of`, `reaches`, `coverage`, `unresolved`. Every response carries
`pack_sha`, and it must match `git rev-parse HEAD` or the response is marked stale.

**Gate:** a real Claude Code session against the Django fixture, in which the agent
declines to edit an `UNRESOLVED` site and says why. Record it. That recording is the demo.

---

## Phase 8 — PR comment + free tier (1 week)

Blast-radius comment on every PR. Free forever for public repositories — that is how the
comments appear in other people's pull requests, which is the distribution loop.

**Gate:** 20 external repositories install it and 8+ are still active at day 30.
**Kill criterion:** <15% day-30 retention. The abstention story does not land with
developers regardless of what the benchmark says.

---

## Phase 9 — Runtime tier (2 weeks, deliberately last)

`resolve/runtime.py` via `sys.monitoring`.

Deliberately last because the published DynaPyt measurement was ~215 minutes per project
against a ~71-second uninstrumented baseline — roughly 180× overhead — and because ~59% of
what it recovers is builtins we discard anyway. It is a nightly confirmation oracle, not a
primary source.

**Investigate first:** PyXray claims dynamic analysis without requiring inputs, analyzing
NumPy and PyTorch in minutes. If that holds, this phase is a different design. **Verify the
claim before building.**

**Gate:** overhead under 20× on the Django fixture, and a run that observes zero edges is
reported as a failed run, not as "no dynamic edges."

---

## Validation checklist — run at every phase gate

```bash
just check                  # fast gate
just verify                 # live data verification
just verify-determinism     # if store/ or label/ changed
```

Then, in writing:

- [ ] Phase gate condition met, with the number recorded in `docs/findings/`
- [ ] Kill criterion explicitly evaluated and not triggered
- [ ] `docs/CODEBASE.md` regenerated and the diff reviewed
- [ ] Every new module has a WHAT/WHY/IMPORTS docstring
- [ ] Every new rule added to AGENTS.md has an entry in `.claude/settings.json`
      `$enforcement_map`, or is tagged ADVISORY
- [ ] `docs/VALIDATION.md` silent-failure table extended if this phase introduced a new
      way to fail quietly
- [ ] PR answers: *what could still silently fail here?*

---

## Sequencing rationale, stated plainly

Phase 0 can kill the project for the cost of two days. Phases 2–4 assemble published work
and carry low technical risk. Phase 5 is the only defensible engineering. Phase 9 is the
most expensive and least informative, which is why it is last despite being the most
exciting.

If you find yourself wanting to start with Phase 9 because runtime tracing is more
interesting than writing Django URL resolvers — that instinct is the reason most projects
in this space fail.
