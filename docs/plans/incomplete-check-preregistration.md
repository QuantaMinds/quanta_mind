# Pre-registration — ask for incomplete verification, not for defects

**Written before the corpus is fetched.** Across 129 adjudicated findings from three designs, the
correct ones share one shape almost unanimously.

## The observation this tests

**Seven of the eight correct findings are a check that does not check what it appears to check:**

| finding | shape |
|---|---|
| `total_reasoning_blocks` incremented, never asserted > 0 | assertion passes vacuously |
| `all(worker_support)` returns True on an empty list | check passes vacuously |
| `w2_scale` assert omits the dimension its sibling checks | assertion misses a case |
| case-sensitive scan misses capitalised variants | check misses a case |
| compares package names, ignores versions | check misses a case |
| `if both dirs exist` — one-present falls through | condition misses a case |
| line-by-line split misses multi-line patterns | check misses a case |

**Why it is plausible rather than a coincidence:** an incomplete check is a *local, structural*
property — visible by comparing the check against what it claims to cover. It needs no simulation
of the program. Every failure class we measured is the opposite: *"this will raise"*, *"this
leaks"*, *"this races"* — predictions about execution.

**And it is a hypothesis drawn from the data it would be scored on**, which is the trap the anchor
filter fell into. That is why this runs on a corpus never used before.

## The change

The schema stops asking for a defect and asks for an incomplete check:

| field | |
|---|---|
| `check_symbol` | the identifier of the assertion, condition or guard |
| `check_kind` | `assertion` \| `condition` \| `guard` \| `comparison` |
| `missed_case` | a **concrete** input or state the check fails to cover |
| `relation` | one sentence: what the check appears to guarantee, and why it does not |

**Both halves are parser-checkable**: the check is a syntactic construct, and the missed case is a
concrete value rather than a prediction.

## Population

**Six repositories used in no previous measurement**: `fastapi`, `pydantic`, `rich`, `dbt-core`,
`prefect`, `sentry`. Every repository touched so far — the original eight, the fresh six, the third
six — is excluded.

## The bar, unchanged

**Under 50% wrong**, blind adjudication, same rubric. Against a background base rate of **7.2%
correct across 195 findings**, and **0–2.8% on unseen corpora specifically**.

## What each outcome means

**Clears** — the model can find one defect class reliably, and the product narrows to it. **That is
a much smaller product than "AI code review"** and the documents would have to say so: *"we find
checks that do not check"*, not *"we find bugs"*.

**Fails** — the shape of the eight correct findings was a coincidence of which defects happened to
exist in that corpus, and the review half has no salvageable question left. **Five designs, five
failures, and the honest conclusion is that this model cannot review this code at any useful
precision.**

## Two things to record whatever happens

**Volume.** Even at high precision, one narrow class raises the question of how often it occurs. **A
finding rate below roughly one per pull request makes the precision academic**, and that number
must be reported beside the wrong-rate rather than after it.

**And the comparison must be like for like.** The bar is the same 50%, the raters are blind, and the
corpus is fresh. **No credit for the schema being narrower** — a narrower question that produces
fewer, better findings is the point, but it has to beat the same threshold.
