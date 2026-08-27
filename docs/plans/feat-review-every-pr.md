# Review every pull request — open the gate, and make the ranking pay for it

**Status: PLAN. Nothing here is built.** Required by AGENTS.md "Working rules" because it changes
`rank/` and `verify/` — the layers that decide where we look and what we publish.

## Why this changes

The product speaks on **~11% of pull requests**. That is not a defect: `store/calibration.baseline`
fires on the top decile of a repository's CHANGES and a top decile is a tenth by construction. It
was the correct rule for the thing this was — a *ranking* that had to justify interrupting someone.

It is the wrong rule for a *reviewer* that a business buys, where a connected repository must
produce a review on every pull request. A buyer comparing against CodeRabbit, Greptile or Qodo sees
silence on nine of ten changes and concludes it is broken.

**And the gate is inverted where it costs most.** `rank/order.fires()` returns False when
`files <= BUDGET` (3). A three-file change is the CHEAPEST possible deep review — the whole diff
fits in one prompt. The current rule mutes exactly the pull requests we can most afford to read
entirely, because it was asking "is the ORDERING worth showing?" and on three files an ordering
saves nobody anything. For a reviewer the same fact reads the other way: **small means read it all**.

## The redesign: one decision becomes three

| decision | today | after |
|---|---|---|
| **Speak?** | `fires()` — ~11% | Always. Every reviewable pull request gets a comment |
| **How deep, on which files?** | not modelled — `allocate/` is an EMPTY directory | `allocate/depth.py` |
| **Publish which findings?** | a parser locates the quote, and nothing else | `verify/publishable.gate()` — built, measured, never wired |

The ranking stops being the output and becomes the **cost lever**. That is the honest use of the
one claim that replicated out-of-sample — top-three-by-fix-history misses 1.21% against
alphabetical's 3.12% — because that claim is about WHICH FILES TO READ FIRST, which is exactly what
an inference budget needs and is not a claim about when to stay quiet.

## `allocate/depth.py` — the new layer

```
Depth.FULL     every changed file goes to the model
Depth.FOCUSED  only the top-k ranked files go to the model
```

`plan(ranking, files, cap) -> Allocation(depth, paths, why)`

- `files <= FULL_CEILING` → **FULL**. Cheap, and the ranking adds nothing at this size.
- otherwise → **FOCUSED** on the top-k. This is where the replicated claim earns its keep.
- `Discrimination.NO_HISTORY` → still FOCUSED, still speaks, and `why` RECORDS that the order was
  alphabetical fallback rather than history. **This is the slice that misses most — 4.46% against
  1.21% — so it must be labelled on the value, never inferred by a reader.**

`why` is mandatory on every `Allocation`. An allocation without a stated reason is the same class
of bug as an unlabeled edge: the residual becomes indistinguishable from a decision.

## What the comment always carries

1. Orientation — the ranked files and the coverage line
2. Findings that cleared `publishable.gate()`, or an explicit "none cleared"
3. **The residual — what was NOT read, named.** On a FOCUSED review this is most of the change.
   "The residual is the product": a reviewer that reads 3 of 40 files and does not say so is
   claiming a coverage it does not have.

## What must NOT change

- **The ranking ORDER.** The 1.21%/3.12% result is about ordering. Touching the sort invalidates
  the only claim that reproduced out-of-sample. This plan changes *consumption* of the ranking only.
- **`fires()` is not deleted.** Its output stops being a mute switch and becomes an input to
  allocation: "this change is in the repository's top decile" is a real signal for spending MORE,
  not for speaking at all.

## Tests that encode the old product decision

Several unit tests assert silence — on `files <= BUDGET` and on below-decile changes. They are not
wrong; they encode the decision this plan reverses. They get **rewritten to assert the new
behaviour** (a comment is always produced, and the DEPTH differs), never deleted. A deleted test is
indistinguishable from a test that never existed.

## What could still silently fail

- **Noise at ten times the volume.** Raw findings are 66.7–82.1% wrong across four blind pools.
  `publishable.gate()` is the only defence and has never run in production. If it admits
  everything we ship the error rate at 10x reach.
  → **A gate rejecting ~0% or ~100% is broken, not lucky.** Both get asserted, not eyeballed.
- **Cost per pull request becomes unbounded.** Every change now pays inference. A hard cap on files
  read and on requests is part of A2, not a follow-up.
- **The ranking quietly stops mattering.** If `FULL` wins on most real changes, inference is not
  being allocated by rank and the cost-lever story is false. → record the FULL/FOCUSED split and
  read it before repeating the claim.

## Measurement, fixed before the runs

- Coverage: **100%** of reviewable pull requests receive a comment, from ~11%.
- Gate rejection rate: strictly between 0% and 100%.
- FULL vs FOCUSED split: reported, no bar — it is the evidence for whether ranking allocates.
- **Published findings per pull request: reported, no bar yet.** This is the number that decides
  whether "a comment on every PR" is sellable against the incumbents, and no amount of plumbing
  changes it. Today's comparable is 0.013–0.037 correct findings per pull request.

## Phases

| | |
|---|---|
| **A1** | `allocate/depth.py` + tests. No behaviour change yet |
| **A2** | Wire `deep_review.deep()` into `serve/review_delivery.py` behind the allocation, with the cost cap |
| **A3** | Wire `verify/publishable.gate()` before anything publishes |
| **A4** | Replace the mute with depth; rewrite the tests that encode the old decision |
| **A5** | Record depth, cost and gate outcomes in the store; surface them in `render/dashboard.py` |

Phase B (accounts, Stripe, entitlement, warm-up worker) and Phase C (web dashboard, CI, SSO) are
packaging and are not in this plan. They are worth nothing until A produces a review worth selling.
