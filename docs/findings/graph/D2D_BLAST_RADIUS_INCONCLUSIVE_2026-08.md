# Does blast radius predict the fix-return outcome? Inconclusive, and D2d is on hold

**Run 2026-08-29 on `pallets/flask`, 393 admissible events, 1,207 file-rows.**
Harness `scripts/measure/predicts.py`; rows in `research/phase0/results/`.

D2a measured that ~44% of import statements resolve in-tree. That says the graph is buildable and
**nothing** about whether it predicts anything. This is the test that was named as not-yet-run.

## The result

Ranked by each signal, top three, hit when the top three intersect the files a later fix returned
to — `serve/retrospective.py`'s own definition, and `rank/events.admissible` imported rather than
restated.

| arm | hits | miss rate |
|---|---|---|
| by import in-degree (D2a) | 75 / 79 | 5.1% |
| by prior fix count (shipped) | 77 / 79 | 2.5% |
| alphabetical (control) | 73 / 79 | 7.6% |

**And the paired test says none of it means anything yet.**

| comparison | discordant pairs | exact p |
|---|---|---|
| importers vs alphabetical | **2** | 0.500 |
| prior fixes vs alphabetical | **6** | 0.219 |
| prior fixes vs importers | **4** | 0.625 |

**This project's floor is 20 discordant pairs** — `A6_WHAT_A_REVIEW_PRODUCES_2026-08.md` records a
retrospective refusing its own verdict at 10. There are 2 here. **The honest reading is that the
test could not answer the question, not that blast radius fails.**

The shipped signal not reaching significance either is the clearest evidence that this is a power
problem rather than a result: the fix-history claim replicated at n = 2,400 across six unseen
repositories. Here it has 79 events and 6 discordant pairs.

## The one thing that did separate, and it points both ways

| file-rows | mean in-degree | share with any importer |
|---|---|---|
| returned to by a later fix (758) | 1.63 | **54%** |
| not returned to (449) | 1.75 | **38%** |

**The mean runs the wrong way and the presence rate runs the right way.** Files a fix came back to
have *fewer* importers on average and are *more often* imported at all. A story can be told for
either; neither is a result at this n, and reporting the favourable half alone is how a signal
gets shipped on nothing.

## Why the sample is this small

393 events yielded only **79 non-degenerate** ones. A budget of three reads everything when a
change touches three files or fewer, so no arm can miss and the event carries no information —
`retrospective.py` already strata-splits on exactly this. Flask's changes are mostly small: 314 of
393 events were degenerate.

## What this means for the build order

**D2b and D2d do not start.** The point of measuring the base rate before shipping was to avoid
building on a signal whose value nobody knew, and the value is still unknown. Building the stored
graph and the review signal now would be shipping on 2 discordant pairs.

**What would answer it:** the same corpus shape the ranking claim used — six repositories the
method has not seen, chosen for larger changes, to reach 20+ discordant pairs. `research/phase0`
already has the corpus machinery. That is a day of compute, not a design question.

**What must not happen:** running more repositories, finding one where importers win, and
reporting that. The corpus is chosen before the arms are compared, or the number means nothing.
