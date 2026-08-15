# Pre-registration — grade the anchor as a region, not a line

**Written before re-adjudication.** If a finding cites line 73, treat the claim as anchored when
the code it describes lies anywhere in **lines 63–83**. Same findings, same raters' rubric in every
other respect, one rule changed.

## Why this is a legitimate question and not moving the goalposts

**It changes what the product promises**, and that is the point. *"The defect is at line 73"* and
*"the defect is in this 21-line region"* are different products. The second is weaker, and a
reviewer can still act on it — the region is smaller than the function.

**The comparison must therefore be stated as a change in the claim, never as an improvement in the
model.** If the wrong-rate drops, the model did not get better; we asked it for less.

## What the mechanical check already says

| | |
|---|---|
| anchor failures where the rater named the true line | 14 |
| offset ≤ 10 lines | **12 of 14 (86%)** |
| offsets observed | 1, 1, 1, 1, 1, 3, 3, 3, 3, 4, 5, 6, 12, 17 |

**And the window cuts both ways.** Of 32 wrong findings on the unseen run, 14 are *"the cited line
lacks the code"* — a wider window rescues those. But **6 are *"refuted by code one to three lines
away"***, and widening the window pulls the refutation into view, making those claims more clearly
wrong rather than less.

## The arithmetic, fixed in advance

| anchor failures rescued | wrong-rate |
|---|---|
| all 14 | **46.2%** — clears |
| 10 | 56.4% — fails |
| 7 | 64.1% — fails |

**It clears the 50% bar only if the window rescues every anchor failure and costs nothing
elsewhere.** That is a narrow condition and it is stated now so a near-miss is not read as a
success.

## Setup

**Population**: the 39 findings from the unseen line-anchor run, where the strict rubric gave
**82.1% wrong, zero correct**. Fresh raters, blind, one rule changed:

> An anchor counts as supporting the claim if the code it describes lies within **±10 lines** of
> the cited line. Everything else is unchanged: a claim false about the code is still WRONG, a
> claim that cannot be decided is still UNFALSIFIABLE.

**Bar: under 50% wrong.** Unchanged.

## What each outcome means

**Clears** — the reviewer's diagnoses are better than its pointing, and a product promising a
*region* is viable where one promising a *line* is not. The verifier changes from checking a line
to checking a window, which is a smaller and more achievable guarantee.

**Fails** — the anchors were never the binding constraint, which is what three prior fixes already
suggested, and widening the window trades precision away for nothing. **Then the review half is
closed on the strongest evidence yet: strict anchors, symbol anchors, and forgiving anchors all
land in the same place.**


---

# RESULT — **FAILS at 66.7%**, and the failure is precise about why

| | strict line | **±10 window** |
|---|---|---|
| CORRECT | 0.0% | 2.6% |
| **WRONG** | 82.1% | **66.7%**, Wilson [51.0%, 79.4%] |
| UNFALSIFIABLE | 10.3% | 20.5% |
| TRIVIAL | 7.7% | 10.3% |

**26 of 39 wrong against a bar of 50%. p = 0.120 on the change.** The pre-registration said it
clears only by rescuing all 14 anchor failures into CORRECT. **It rescued 6, and 1 reached
CORRECT** — the other 5 went to UNFALSIFIABLE and TRIVIAL.

## The window did exactly what it was supposed to. That is the finding.

| bucket | strict | ±10 window |
|---|---|---|
| **describes code that is not there** | **14 of 32 (43.8%)** | **2 of 26 (7.7%)** |

**The anchor problem is solved.** From the largest failure class to two findings. And the
wrong-rate barely moved, because **the anchor was never what most of these were failing on.**

## Why the remaining 26 are wrong

| n | share | reason |
|---|---|---|
| **9** | **34.6%** | claims a **merged, passing test** is broken |
| 5 | 19.2% | refuted by code a few lines away |
| 5 | 19.2% | misreads what the code does |
| 4 | 15.4% | wrong about Python itself |
| 2 | 7.7% | describes code that is not there |
| 1 | 3.8% | arithmetic it could have performed itself |

**Forgiving the anchor converts WRONG into UNFALSIFIABLE, never into CORRECT.** Removing a reason
to reject a claim does not make the claim true. An unfalsifiable finding is still unpublishable —
a reviewer cannot act on it either.

## The one bucket that deserves a caveat, and it does not rescue the result

**Nine of 26 assert that a test which demonstrably passes is broken.** A reviewer at review time
does not know the test passes — but **the developer does, and finds out in seconds.** Those cost
trust rather than correctness.

**Excluding that entire bucket as an artefact of grading merged pull requests: 17 of 39 = 43.6%
wrong.** Below the bar — and it is not a legitimate exclusion, because the claims are still false
and the developer still pays to discover it. **Recorded because someone will propose it, and the
answer is that the honest number is 66.7% with the caveat attached, not 43.6% with it removed.**

## What this closes

**Strict line anchors, symbol anchors, and forgiving ±10 anchors all land in the same place**:
82.1%, 77.8%, 66.7% wrong. Three different anchoring schemes, one corpus, no design clears 50%.

**And one real defect was found twice.** `get_namespace(X)` called without `xp=xp`, discarding the
caller's argument, was independently marked CORRECT by the symbol-anchor raters and the window
raters — different designs, different rater pools, same bug. **The model is not incapable of
finding a defect. It produces one real finding surrounded by thirty-eight that are not.**
