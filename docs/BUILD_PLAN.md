# Build Plan

> **Nothing in Phases 1+ is authorised until `docs/findings/PHASE0_PREREGISTRATION.md`
> has a filled Results section and a non-null verdict.**
>
> The previous version of this file described nine phases of architecture built on an
> unmeasured assumption. That is the same shape as the failure we have already paid for:
> a real problem, a plausible mechanism, and no evidence anyone bleeds from it. This
> version front-loads the measurement and cuts everything that is not defensible.

---

## Phase 0 — The correlation test (1 week, zero product code)

**Full protocol: `docs/findings/PHASE0_PREREGISTRATION.md`. Read it, do not summarise it.**

**Question:** does `unresolved` predict breakage in AI-authored changes?

**Method in one line:** 2×2 over AIDev agent PRs — exposure is *vanilla PyCG could not
resolve a call site to the changed symbol at the parent commit*; outcome is *a revert or
fix commit touched that file within 7 days*. Report relative risk with a 95% CI.

Three design decisions make this test valid. Each is argued in the pre-registration:

- **Outcome is behavioural, not AST-based.** The AIDev breaking-change labels are produced
  by static analysis, which is structurally blind to the breakage this thesis is about.
  Using them as ground truth would manufacture a false null.
- **Analysis is relative risk, not a count.** With ~15% of call sites unresolved, "15% of
  breakages were at unresolved sites" is zero signal that reads as confirmation.
- **Instrument is vanilla PyCG.** The crudest available, therefore the conservative one.
  Adding resolvers can only shrink the exposed group, so a crude null stays null. It also
  removes any dependency on code we have not written.

**Gate:** RR ≥ 3.0, CI lower bound > 1.5 → proceed to Phase 1.
**Soft gate:** RR 1.5–3.0 → proceed, but rewrite `PROJECT_CONTEXT.md §5` first; the pitch
becomes "prioritise review attention," not "prevent breakage."
**Kill criterion:** RR < 1.5, or CI includes 1.0 → **stop and publish the null.**
**No-result criterion:** fewer than 20 breakages in the exposed arm → underpowered. Widen
the corpus. Do not report it as negative.

**Deliverable:** `PHASE0_PREREGISTRATION.md §8` filled and signed.

---

## Phase 0b — Symptom vocabulary (1 week, only if Phase 0 is non-null)

Open thread #7. Fifty verbatim practitioner complaints from r/ExperiencedDevs,
r/programming, HN and the Cursor forum, coded for whether developers ever describe the
*missing-caller* mechanism rather than context-window or hallucination.

**Decision rule:** <5 of 50 using missing-caller language → the sales motion starts with
education. Price and plan for it, and record it in `PROJECT_CONTEXT.md §5` before any
sales conversation.

This is the step that was skipped last time. One week now, six weeks later.

---

## Scope decision — taken before Phase 1, recorded so it is not silently reversed

### We do not build a graph

Graphify, CodeGraph and GitNexus hold roughly 165k GitHub stars between them, are MIT or
near-MIT, ship over MCP, and iterate faster than three people can. CodeGraph went 0 → 47k
stars in five months.

**We consume one as a dependency.** `ingest/` adapts an upstream graph and adds a thin
tree-sitter call-site census — because upstream tools emit edges but none of them emits the
*denominator*, and the denominator is what coverage is computed from.

Every improvement they ship becomes an improvement to our product. We stop competing with
projects we cannot outrun and start depending on them.

**Deleted from the plan:** `parse/` as a layer, `resolve/static.py`, and any ambition to
resolve better than upstream.

### We do not build a runtime oracle in v1

DyPyBench measured DynaPyt-style tracing at ~215 minutes per project against a ~71-second
uninstrumented baseline — roughly 180×. The dynamic graph came out ~12% the size of the
static one, even at 82% statement coverage. Of what it recovers, ~59% is builtin calls we
discard anyway.

**The economics do not close, and designing around a layer that will not ship distorts
everything upstream of it.** `resolve/runtime.py` is removed, not deferred.

If PyXray's claim — dynamic analysis without requiring inputs, NumPy and PyTorch in
minutes — survives verification, this returns as a clean new module. Verify first,
reinstate second.

**Result: the product is `probe/` + `label/` over someone else's graph.** Roughly 800 lines
and one number. That is the entire defensible surface, and three people can build it.

---

## Phase 1 — Ingest + call-site census (4 days)

`types/`, `discover/`, `ingest/`, `store/`.

Adapters for CodeGraph and Graphify behind one interface. Tree-sitter call-site census
producing the denominator. SQLite pack, SHA-pinned.

**Gate**
- `just verify-determinism` green — 3 runs byte-identical
- `just verify-no-source-leak` green — invariant 6 proven, not asserted
- call-site count matches a hand-count on a 200-line fixture
- swapping the upstream adapter changes edges but not the coverage arithmetic

**Kill criterion:** no upstream graph exposes enough per-call-site detail to compute a
denominator. Then we do need our own parse layer, and the scope decision above reverses —
re-argue it in a PR, never reverse it silently.

---

## Phase 2 — The label layer (1 week) ← **half the product**

`label/`. `Confidence`, `Provenance`, `Unresolved`, coverage math with builtins excluded
from both numerator and denominator.

Built **before** the probe layer so that no code path ever emits a bare edge. Retrofitting
provenance is how default confidence values get introduced — silent failure #1.

**Gate:** all six invariants in `ARCHITECTURE.md §6` pass as property tests, especially
conservation: no call site may vanish between stages.

---

## Phase 3 — The probe layer (1–2 weeks) ← **the other half, and the moat**

`probe/`. The Python feature-prevalence scanner: `eval`, `exec`, computed
`getattr`/`setattr`, `importlib`, metaclasses, `__getattr__`, registering decorators,
monkeypatching, C extensions, `globals()`/`locals()`.

This is the prevalence half of the capability × prevalence decomposition. JCG already ships
Python *capability* adapters — use them, do not rebuild them. The prevalence half is
JVM-bytecode-specific and does not exist for Python.

**Deliverable that doubles as marketing:** the Python row of the soundiness table. The 2015
manifesto covers C/C++, Java/C# and JavaScript, notes no reliable survey of
dangerous-feature usage exists, and asks for precisely this. Publishable regardless of
commercial outcome.

**Gate:** prevalence scan completes on a ≥1M-line fixture in under 60 seconds.

---

## Phase 4 — MRO and framework resolvers (2–3 weeks)

Only the resolvers that recover edges upstream tools structurally cannot, ordered by where
Phase 0's exposure data showed the risk concentrates:

1. `resolve/mro.py` — `super()` chains. PyCG misses these entirely; pure inheritance
   structure, so recovery is exact.
2. `resolve/frameworks/django.py`, `celery.py`, `sqlalchemy.py`, `pytest.py`

One resolver per PR, per branch, each shipping with a live test asserting a minimum edge
count on its fixture.

**Gate per resolver:** coverage on its fixture rises, and **no previously-`RESOLVED` edge
changes target.** A resolver that moves existing edges is a regression, not a feature.

**Note the demotion.** In the previous plan this was called the moat. It is not — it is a
feature race against projects shipping daily. The moat is Phase 3. Build resolvers only
where Phase 0 says it pays.

---

## Phase 5 — MCP server (3 days)

`serve/`. Four tools: `callers_of`, `reaches`, `coverage`, `unresolved`. Every response
carries `pack_sha`; a mismatch with `git rev-parse HEAD` marks it stale.

**Gate:** a recorded Claude Code session against the Django fixture in which the agent
declines to edit an `UNRESOLVED` site and says why. That recording is the demo.

---

## Phase 6 — PR comment + free tier (1 week)

Blast-radius comment per PR. Free forever on public repositories — that is the distribution
loop, because the comments appear in other people's pull requests.

**Gate:** 20 external repos install, ≥8 still active at day 30.
**Kill criterion:** <15% day-30 retention. The abstention story does not land with
developers, whatever the benchmark says.

---

## Validation checklist — every phase gate

```bash
just check                  # fast gate
just verify                 # live data verification
just verify-determinism     # if store/ or label/ changed
```

- [ ] Gate condition met, number recorded in `docs/findings/`
- [ ] Kill criterion explicitly evaluated and not triggered
- [ ] `docs/CODEBASE.md` regenerated, diff reviewed
- [ ] New modules carry WHAT / WHY / IMPORTS docstrings
- [ ] New rules registered in `.claude/settings.json` `$enforcement_map`, or tagged ADVISORY
- [ ] New failure mode added to `docs/VALIDATION.md §4`
- [ ] PR answers: *what could still silently fail here?*

---

## Sequencing rationale

Phase 0 can end the project for one week's cost, and until it is done every other phase is
speculation with good file structure. Phases 1–2 are assembly plus arithmetic. Phase 3 is
the only thing nobody else is doing. Phase 4 is a feature race we enter only where the data
says it pays.

Two temptations, named so they can be recognised in the moment:

**Building a better graph.** It is the fun part, it is tractable, and you will lose to a
47k-star MIT project. Consume theirs.

**Building the runtime tracer.** It is the most interesting engineering here and the least
economically viable. Deleted, not deferred, for exactly that reason.
