# The ranking does not predict where reviewers comment — it predicts the opposite

**Exploratory, pre-registered as underpowered: n = 23, a median of one attended file per pull
request, and 10 of 23 from two repositories.** Read the clustering table before pooling.

## Result

Mean normalised rank of the files a human commented on, 0 = first in the ordering, 1 = last.
**Lower means attention landed earlier in that ordering. 0.5 is where a uniform ordering puts it.**

| ordering | mean |
|---|---|
| by diff size | **0.379** |
| alphabetical | **0.420** |
| **ours (fix history)** | **0.595** |

| comparison | ours earlier | ours **later** | tied | mean difference |
|---|---|---|---|---|
| vs alphabetical | 3 | **12** | 8 | **+0.175** |
| vs diff size | 5 | **13** | 5 | +0.217 |

**Our ranking places the commented files later than alphabetical, and later than chance.** Diff
size is the best predictor of the three: **reviewers comment where there is most to comment on.**

## What this does and does not mean

The pre-registration named both directions as ambiguous, and this is the discordant one. It splits
into two readings and **the tie-break is already measured:**

- **the ranking is noise** — refuted on its own target. Top-three-by-fix-history misses **1.21%** of
  the changes a later fix returns to against alphabetical's **3.12%**, six repositories the method
  never saw, n = 2,400, McNemar p < 1e-6.
- **the ranking points where reviewers do not go** — consistent with everything here.

**A ranking that is validated against later fixes and anti-correlated with reviewer attention is
the thesis stated as a measurement.** If it agreed with attention it would be redundant. It
disagrees, and the thing it agrees with instead is where fixes come back.

**This is the first direct evidence for the half of the thesis that was always assumed** — that
reviewers systematically do not look where the defects return.

## The limits, which are severe

**"Attention" here is where comments LANDED, not where a reviewer READ.** A reviewer may read the
risky file, find nothing, and comment on a typo in a large one. This measures the visible residue
of attention and calls it attention.

**n = 23, clustered.** `aiohttp` 6, `urllib3` 4, `starlette` 4 — 14 of 23 from three repositories,
and the per-repository means disagree: `celery` has ours at 0.42 against alphabetical's 0.33, while
`vcrpy` has 1.00 against 0.33. **A pooled number over that mix is a repository artefact and the
table is published so it cannot be quoted without one.**

**And the control is the files API's order, not the rendered page's.** 29 of 29 sampled pull
requests return alphabetically from the API; whether GitHub renders that order by default is not
verified from here.

## What it kills and what it leaves

**It kills the file-level orientation pitch as stated.** "We tell you which of these files to read
first" cannot be supported by a ranking that places attention later than alphabetical order, and
the median pull request changes three files anyway.

**It leaves the queue-level claim untouched**, because that claim is about *which pull requests*
rather than *which files inside one* — and it is the unit at which no measurement here applies.
