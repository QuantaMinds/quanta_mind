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


---

# BEFORE THAT RUN — two checks that reorder the queue

## 1. Production relevance could not be measured, and the reason is my sampling

**Every finding sits on a pull request merged days ago.** Median forward history in the clones:
**0.4 days. Zero of 14 pull requests have the 90 days the outcome rule requires.**

| repo | PR | forward history |
|---|---|---|
| langchain | 39646 | **0.0 days** |
| vllm | 52374 | 0.2 |
| cartography | 3130 | 0.8 |
| transformers | 47152 | 4.2 |

**The harness refused to report rather than printing a spurious zero.** But the corpus cannot answer
whether these findings track real defects, because there is no "later" in it yet.

**This is the recency error from the review-comment corpus, committed a second time.** I fetched the
most recently merged pull requests — the exact wrong sample for any question about what happens
next. **Any future run that wants the defect-return check must draw pull requests merged at least
90 days ago, and that constraint belongs in the fetcher rather than in a reader's memory.**

## 2. Executing the claims settles a whole failure bucket in seconds

Four of the wrong findings are *"wrong about Python itself"*. Each is decidable by a three-line
snippet, and none of them needed the repository:

| the model's claim | executed |
|---|---|
| *"closing a coroutine that was never started raises"* | `close()` returned cleanly — **false** |
| *"`shape.insert(0, n)` can raise ValueError"* | returned `[4]` — **false** |
| *"aware datetimes in different zones compare unequal"* | `08:40+00:00 == 11:40+03:00` → `True` — **false** |
| *"`all()` on an empty list is falsy"* | `all([]) → True` — **the model was right** |

**The model asserted three things about Python that Python contradicts in one line each.** It also
got the fourth right, and that one is a genuine defect.

**So an execution gate is not a research programme — it is a subprocess.** For claims of the form
*"this expression raises / returns / compares like so"*, generate the snippet, run it, and publish
only what survives. That is exactly the execution-grounded verification the literature reports, and
it costs milliseconds.

**It does not fix the other buckets** — *"refuted by code a few lines away"* and *"misreads what the
code does"* need the repository, not a snippet. But it removes an entire class, deterministically,
and the class is one where the model is confidently wrong.

## Revised order

1. **Execution gate on executable claims** — cheap, deterministic, removes a measured class.
2. **The incomplete-check schema** — as pre-registered above, on the fresh six.
3. **Defect-return relevance** — needs a corpus of pull requests merged 90+ days ago, which is a
   different fetch and should be built once, properly, with the age constraint enforced in code.
