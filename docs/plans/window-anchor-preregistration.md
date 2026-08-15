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
