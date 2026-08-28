# Speak only where the budget binds — product-readiness item 2

**Branch:** `feat/gate-on-binding-changes`. **Status: PLAN.** Touches `rank/`, so this is written
first. → `docs/plans/product/product-readiness.md`, item 2.

## The claim being acted on

`roi-preregistration.md` failed B1 at **28.9% effort reduction against a 50% bar**, and named the
mechanism rather than excusing it:

| files touched | share |
|---|---|
| 2 | 45.66% |
| 3 | 20.39% |
| **≤ 3 — the budget asks for everything** | **66.04%** |

**On two thirds of changes a three-file budget saves nothing by construction.** `read = min(3,
n_files)`, so at three files or fewer we tell the customer to read every file they already have,
in an order. That is not a workflow change and there is nothing to sell in it.

Restated on the third where it binds:

| policy | miss | effort saved |
|---|---|---|
| **top 3 by fix history** | **4.11%** | **50.3%** |
| top 3 alphabetically | 9.20% | 50.3% |

**Both halves travel together**: the lift is three times larger there and so is the absolute miss.

## The change

`rank/order.fires()` gains a `binds` condition: **the change must touch more files than the budget
can read.** Definition copied from the study, not re-invented — `reviewer_effort.py:75` uses
`read = min(BUDGET, len(files))` with `BUDGET = 3`, so binding is `len(scores) > budget`.

**It is a NARROWING of when we speak, not a change to the ordering.** The ranker's ordering is
what carries `1.21% against 3.12%, p < 1e-6`; nothing here touches it. What changes is the
population we speak on, and that population has its own measured numbers above.

## What this costs, and it is not free

**We go quiet on 66% of changes we currently might speak on.** That is the point — but it must be
measured, not assumed, because the firing rate is already a property of the customer's repository
(6.3% to 29.0% across four repositories) and this multiplies it down.

**A repository of small changes may now never hear from us at all.** `firing.Selectivity` already
names the case where a rule cannot select anything as `CONCENTRATED` rather than reporting a rate
of zero. **A repository that is silent because its changes are small needs the same treatment** —
a named state, not an absence. Without it, "we never spoke" and "your changes are all small" are
the same silence, which is the failure this project exists to refuse.

## Bars, fixed here

| | bar |
|---|---|
| **correctness** | the ordering is unchanged on every change that still fires — same ranked list, byte-identical comment |
| **the gate binds** | no change with `files ≤ budget` fires, proven on real repositories |
| **legibility** | a repository silenced by size reports WHY, distinguishable from having no history |
| **measured, not assumed** | the new firing rate is reported per repository on at least three real repositories of different size |

## How it is verified

Live, on the clones already on disk — flask, django, home-assistant/core — reporting the firing
rate before and after, and the file-count distribution behind it. **A rate that does not fall is a
bug**, since two thirds of changes are expected to stop qualifying.

## What could still silently fail

**CHECKED BEFORE BUILDING, AND IT IS REAL.** `research/phase0/external/commit_stream.py:23`
yields **`.py` files only**. The product's `scores` spans `.py .pyi .ts .tsx .js`. The two
populations are therefore not the same:

- On a **Python-only** repository they coincide and the measured numbers transfer directly.
- On a **polyglot** repository the product counts more files per change, so **more changes bind
  than the study's population would predict**. A change of two `.py` and two `.ts` files is
  non-binding to the study and binding to the product.

**The direction of the change is unaffected** — speaking where the budget cannot save anything is
wrong under either count. **But 4.11% miss and 50.3% saved are Python-only figures and must be
quoted as such.** Re-deriving them over the full reviewable set is a separate measurement and is
not done here.

**`scores` is over ranked units, so unsupported files are already excluded** before `fires()` sees
them — which is the right population for a budget that only reads what it can parse.
