# QuantaMind

> **QuantaMind — Focus: model-free triage of where to look first in a large change, ranked by which
> files a later fix has returned to, with a published coverage line naming what was not analysed.**

Every AI reviewer reads the whole diff at one depth. **We decide where to look first, read hard
only there, and state what we could not analyse.** Every other tool in the category tells you what
is *wrong*; we do not, because we measured that half and it did not survive.

A model-free pass ranks the changed files by how often a later fix has returned to them, and that
ranking decides where the model reads. **Raw findings are never published**: one isolated judge, a
DIFFERENT model family from the reviewer, clears every claim first — a same-family judge agreed
with a careful rater on 34.9% and certified the reviewer's own hallucinations. Every review ends
with its coverage line.

**Status: seven of ten layers built.** The chain from git history to a rendered comment runs end
to end and is verified against real repositories. `allocate/`, `infer/` and `verify/` are empty
**and scheduled** — the reviewer runs on Gemini over the ranked files, behind the isolated judge.

**No count of modules appears here on purpose.** The one that used to said five layers were empty
when four of them were not. **Start at `docs/plans/implementation.md`, section "Where this is
now"** — it carries a table regenerated from the filesystem and kept honest by
`scripts/guard/records/check_plan_state.py`, which fails the build when the two disagree.

---

## Where to look

**Read these four. Everything else is reference or history.**

| I want to… | File |
|---|---|
| Understand the product, and see the evidence for every claim | `docs/product/QUANTAMIND.md` |
| Build it — stages, gates, tests, telemetry, revenue | `docs/plans/implementation.md` |
| Know the folder structure and the layer rules | `docs/plans/product/product-skeleton.md` |
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
uv run quantamind review <pr>   # NOT BUILT, exits 2   documented-command:unbuilt
uv run quantamind serve         # webhook endpoint; authenticates, does NOT review
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
