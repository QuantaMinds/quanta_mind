# QuantaMind

Every AI reviewer reads the whole diff at one depth. **We decide where to look first, read hard
only there, and state what we could not analyse.**

A model-free pass ranks the changed functions and decides where inference goes. A parser checks
the model's structural claims before publication. Every review ends with its coverage.

**Status: no product code yet.** `src/quantamind/` holds the package root and nothing else. The
evidence exists, the plan exists, the layers are empty. Start at
`docs/plans/implementation.md`.

---

## Where to look

**Read these four. Everything else is reference or history.**

| I want to… | File |
|---|---|
| Understand the product, and see the evidence for every claim | `docs/product/QUANTAMIND.md` |
| Build it — stages, gates, tests, telemetry, revenue | `docs/plans/implementation.md` |
| Know the folder structure and the layer rules | `docs/plans/product-skeleton.md` |
| Publish anything public — what we may and may not say | `docs/product/publishing-rules.md` |
| Answer "what is QuantaMind" or "how are you different" out loud | `docs/product/what-to-say.md` |

```
docs/product/       what we are building, and the site that sells it
docs/plans/         how it gets built
docs/engineering/   how the repository works
docs/findings/      the research, including the nulls
docs/superseded/    the falsified product, kept only for provenance
```

**Before your first change: `AGENTS.md`.** It is the constitution, capped at 210 lines, and
every rule in it names the guard that enforces it. Reading it is faster than being stopped by it.

### Reference

| File | What it holds |
|---|---|
| `docs/engineering/CODEBASE.md` | Folder-by-folder map. CI fails if behaviour changes and this does not |
| `docs/engineering/VALIDATION.md` | Why a green test is not verified data |
| `docs/engineering/CORRECTIONS.md` | How a published number gets corrected |
| `docs/product/HISTORY_SIGNAL_WALKTHROUGH.md` | How the product works, told as a week in an engineer's life |
| `docs/plans/gravity-reviewer-build-plan.md` | Model and API decisions: effort, caching, the request ceiling, cost |
| `ARCHITECTURE.md` | Layers, contracts, invariants |
| `CONTRIBUTING.md` | Branch, PR and review protocol |
| `docs/findings/` | The research write-ups, including the results that came back null |
| `research/` | The evidence base. Never product code, never imported by `src/` |
| `scripts/guard/` | The enforcement layer — the rules that are real |

### Superseded, kept for provenance

`BRIEFING.md`, `docs/superseded/BUILD_PLAN.md` and `docs/superseded/PROJECT_CONTEXT.md` describe the **falsified**
product. Each opens with a banner saying so. They survive only because
`docs/findings/PHASE0_PREREGISTRATION.md` cites them, and a preregistration is not edited to
accommodate a tidy-up. **Do not take guidance from them.**

---

## Commands

```bash
uv sync --all-extras            # install
uv run quantamind review <pr>   # one review locally, posts nothing
uv run quantamind serve         # the webhook service on 127.0.0.1:7331
just check                      # ruff + mypy + guards + unit tests — before every commit
just verify                     # check + live data verification — before every PR
```

`just check` is the gate. If it is red, nothing else matters.

---

## What this project already knows

**The founding correlation test returned null** — relative risk 1.040 against a preregistered
stop threshold of 1.5. It falsified the earlier product, which was unsoundness labels served
over MCP. **That architecture was never built and this one inherits none of it.**

What justifies this one: the ranked function is the one a later fix returns to, well above its
rate elsewhere, replicated by an independent rater from a different model family. The numbers,
their confidence intervals, and the four measurements that were withdrawn are all in
`docs/product/QUANTAMIND.md`.

**Four instrumentation failures and two more found since** are recorded rather than quietly
fixed, because a document that never reports its own errors gives a reader no way to calibrate
the rest of it.
