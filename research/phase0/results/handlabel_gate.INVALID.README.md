# The 20-PR gate scored 16/20 and the result is INVALID

The score is real. The labels behind four of it are not.

## What happened

`_key.csv` was opened only after `human_labels.csv` was committed, and scoring reported:

    agreement 16/20 (80%)   gate >=16 -> PASS
    kappa 0.682   unsure 1   median 9 min

Four of those twenty labels — **3, 7, 17 and 20** — were recorded as CLEAN on the stated
reason "zero commits in the 7-day window". There were no commits in the window because
**the window could not be read**. Every one of those four PRs merged into a branch that
has since been deleted:

| label | PR | base ref | resolves |
| --- | --- | --- | --- |
| 3 | policyengine-us#6069 | `BenOgorek/qbid-suite` | **404** |
| 7 | policyengine-us#6052 | `BenOgorek/qbid-suite` | **404** |
| 17 | policyengine-us#6071 | `just-qbid-logic` | **404** |
| 20 | PteraSoftware#32 | `release-3.1.0` | **404** |

The evidence gatherer written for this labelling session ended its window query with
`or []`. A 404 became an empty list, an empty list read as "nothing landed after this PR",
and "nothing landed" was recorded as a judgement that nothing broke.

**That is the defect this entire session existed to remove**, reproduced by the tooling
built to validate the fix for it. `window.candidates` returned `[]` for both "no commits"
and "could not look", and A38 replaced it with a raise. The gatherer here reintroduced the
same collapse one layer up, in a throwaway script, and it went unnoticed because an empty
window produces a confident-looking CLEAN rather than an error.

## It produced at least one wrong label

Label 20 is provably wrong on its stated reason. `camUrban/PteraSoftware#32` merged at
`2025-07-07T00:49:29Z`; commit `4098184ef7f1` — "I reformatted my files using black and
fixed even more typos" — lands at `02:10:53Z`, eighty minutes later and squarely inside
the window. The classifier saw it. The label says nothing landed.

Whether that commit REPAIRS the PR is a separate question and arguably it does not:
"fixed even more typos" reads as continuing incomplete work rather than undoing wrong
work. But the label did not reach CLEAN by that argument. It reached CLEAN by not looking.

## Why the score cannot simply be recomputed

Labels 3, 7 and 17 agreed with the classifier, so the arithmetic survives dropping label
20 alone. That does not rescue the gate:

- Three labels agreeing with the machine while resting on no evidence is not agreement.
  It is two instruments being silent about the same hole.
- The key is now open. Any re-label of these four by the same labeller is anchored, which
  is the exact contamination the sealed key exists to prevent.

## What the gate needs

A fresh draw and a fresh labeller, with the gatherer fixed first:

1. Resolve a deleted base ref rather than swallowing it — the merge commit is still
   reachable from the default branch, and the window can be walked from there.
2. An unreadable window must RAISE, never return empty. Same rule as `window.candidates`.
3. A label whose stated evidence is "zero commits in the window" must record whether the
   window was READ and found empty, or could not be read at all.

Until then this repository has no passed hand-labelling gate, and the outcome variable's
32.04% agent-arm breakage rate is unvalidated by human judgement.
