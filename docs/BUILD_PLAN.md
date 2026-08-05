# Build Plan

> **Nothing in Phases 1+ is authorised until `docs/findings/PHASE0_PREREGISTRATION.md`
> has a filled Results section and a non-null verdict.**
>
> The previous version of this file described nine phases of architecture built on an
> unmeasured assumption. That is the same shape as the failure we have already paid for:
> a real problem, a plausible mechanism, and no evidence anyone bleeds from it. This
> version front-loads the measurement and cuts everything that is not defensible.

---

## The correlation test (1 week, zero product code)

**Thresholds: `docs/findings/PHASE0_PREREGISTRATION.md`.**
**Execution: `docs/findings/PHASE0_RUNBOOK.md` — day by day, with harness tests, controls,
expected outputs and the failure-diagnosis tree. Read both, do not summarise either.**

**Scope: Python arm first, then TS/JS. No other language until both report.**

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

**Gate:** RR ≥ 3.0, CI lower bound > 1.5 → proceed to the call-site census layer.
**Soft gate:** RR 1.5–3.0 → proceed, but rewrite ``PROJECT_CONTEXT.md` “Business case”` first; the pitch
becomes "prioritise review attention," not "prevent breakage."
**Kill criterion:** RR < 1.5, or CI includes 1.0 → **stop and publish the null.**
**No-result criterion:** fewer than 20 breakages in the exposed arm → underpowered. Widen
the corpus. Do not report it as negative.

**Controls gate (Day 2, blocking):** a positive control of 30 synthetic PRs — where
breakage is *known* to be caused by an unresolvable `super()` edge — must yield RR ≥ 5.
**Until the instrument is shown capable of detecting a planted positive, a null result is
uninterpretable and must not be believed.** Negative controls on nonsense variables
(filename initial, line-count parity) must yield RR ≈ 1.

**Deliverable:** `PHASE0_PREREGISTRATION.md` “Results” filled and signed, both arms, with the
eight-item authenticity checklist in `PHASE0_RUNBOOK.md` “Authenticity checklist” complete.

---

## Symptom vocabulary (1 week, only if the correlation test is non-null)

Run for both Python and JS/TS communities — the vocabulary may differ, and JS developers
face a failure mode Python does not (the bundler boundary).

Open thread #7. Fifty verbatim practitioner complaints from r/ExperiencedDevs,
r/programming, HN and the Cursor forum, coded for whether developers ever describe the
*missing-caller* mechanism rather than context-window or hallucination.

**Decision rule:** <5 of 50 using missing-caller language → the sales motion starts with
education. Price and plan for it, and record it in ``PROJECT_CONTEXT.md` “Business case”` before any
sales conversation.

This is the step that was skipped last time. One week now, six weeks later.

---

## Does pull-based retrieval escape attention dilution? (1 week)

**Runs after the correlation test, before any the call-site census layer code. This is a precondition for the product, not
a nice-to-have.**

**The problem.** SWE-PRBench (arXiv 2603.26130) evaluated 8 frontier models across three
context configurations and found all of them degrade as structured context is added — *"even
when context is provided via structured semantic layers including AST-extracted function
context and import graph resolution."* Not a length effect: config A and C differ by 500
tokens. The identified cause is attention representation, not content selection.

**That context is our Oracle 1 + Oracle 2, delivered in-prompt.** Our entire mechanism
assumes better structural context improves agent output. For prompt-delivered context, that
is now contradicted by direct measurement.

**The untested distinction.** They *pushed* context into the prompt. We have the agent
*pull* via MCP tool calls. `callers_of(symbol)` returning 7 labeled edges is not 800 tokens
of file content beside a diff — different position, different volume, different attention
profile. Their limitations section points here but does not test it.

**Experiment.** Take 30 Type3 PRs from SWE-PRBench — their Type3 Latent category is our
thesis verbatim: *"The issue resides in files that import or depend on the changed files."*
Using their public harness and dataset, compare:

| Arm | Context |
|---|---|
| (a) | config A, diff-only — their best-performing configuration |
| (b) | config A **plus an MCP tool** the model may call for callers of changed symbols |

Same model, same judge, same scoring formula. Their judge is validated at κ=0.75.

**Why Type3 specifically:** it does not improve with full context in their results —
Sonnet 0.17→0.13→0.14, DeepSeek 0.12→0.12→0.11, GPT-4o-mini 0.10→0.10→0.11, all flat, and
listed among hard categories as *"Type3 near-zero."* If pull-based retrieval moves a flat
line, that is a clean signal.

**Gate:** (b) beats (a) on Type3 composite score. Then we have direct evidence that
tool-call delivery escapes attention dilution — and a publishable result.

**Kill criterion:** (b) ≤ (a). Then the delivery mechanism is wrong, and no amount of graph
quality fixes it. Redesign before the call-site census layer rather than after.

**Cost:** one week, someone else's dataset, someone else's harness, no product code.

**Note the sequencing logic:** the correlation test asks whether unresolved sites predict breakage.
The pull-based retrieval test asks whether telling an agent about them helps. **Both must be true.** A positive
The correlation test with a negative the pull-based retrieval test means the signal is real and undeliverable.

---

## Scope decision — taken before the call-site census layer, recorded so it is not silently reversed

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

## Ingest + call-site census (4 days)

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

## The label layer (1 week) ← **half the product**

`label/`. `Confidence`, `Provenance`, `Unresolved`, coverage math with builtins excluded
from both numerator and denominator.

Built **before** the probe layer so that no code path ever emits a bare edge. Retrofitting
provenance is how default confidence values get introduced — silent failure #1.

**Gate:** all six invariants in ``ARCHITECTURE.md` “Invariants”` pass as property tests, especially
conservation: no call site may vanish between stages.

---

## The probe layer (1–2 weeks) ← **the other half, and the moat**

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

## MRO and framework resolvers (2–3 weeks)

Only the resolvers that recover edges upstream tools structurally cannot, ordered by where
The correlation test's exposure data showed the risk concentrates:

1. `resolve/mro.py` — `super()` chains. PyCG misses these entirely; pure inheritance
   structure, so recovery is exact.
2. `resolve/frameworks/django.py`, `celery.py`, `sqlalchemy.py`, `pytest.py`

One resolver per PR, per branch, each shipping with a live test asserting a minimum edge
count on its fixture.

**Gate per resolver:** coverage on its fixture rises, and **no previously-`RESOLVED` edge
changes target.** A resolver that moves existing edges is a regression, not a feature.

**Note the demotion.** In the previous plan this was called the moat. It is not — it is a
feature race against projects shipping daily. The moat is the probe layer. Build resolvers only
where the correlation test says it pays.

---

## MCP server (3 days)

`serve/`. Four tools: `callers_of`, `reaches`, `coverage`, `unresolved`. Every response
carries `pack_sha`; a mismatch with `git rev-parse HEAD` marks it stale.

**Gate:** a recorded Claude Code session against the Django fixture in which the agent
declines to edit an `UNRESOLVED` site and says why. That recording is the demo.

---

## PR comment + free tier (1 week)

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
- [ ] New failure mode added to `docs/`VALIDATION.md` “The silent-failure suite”`
- [ ] PR answers: *what could still silently fail here?*

---

## Sequencing rationale

The correlation test can end the project for one week's cost, and until it is done every other phase is
speculation with good file structure. Phases 1–2 are assembly plus arithmetic. The probe layer is
the only thing nobody else is doing. The MRO and framework resolvers is a feature race we enter only where the data
says it pays.

Two temptations, named so they can be recognised in the moment:

**Building a better graph.** It is the fun part, it is tractable, and you will lose to a
47k-star MIT project. Consume theirs.

**Building the runtime tracer.** It is the most interesting engineering here and the least
economically viable. Deleted, not deferred, for exactly that reason.
