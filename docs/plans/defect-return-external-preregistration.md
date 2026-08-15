# Pre-registration — defect-return on repositories the ranker was not developed on

**Written before a single repository is cloned.** This is the test the whole company now rests on.
Everything else about the ranking half is either measured on the original eight repositories or
has already returned a null.

## The exact claim under test

> On repositories the ranker was never developed against, does ranking changed files by prior
> touch count beat an **alphabetical** ordering at containing the file a later fix returns to?

**On the original eight this is the one thing that works**: file top-3 misses **1.44%** of events
against an alphabetical control's **3.31%** — a lift of **+1.87 points** — and on the held-out
pair, 0.69% against 4.15%, a lift of **+3.46**. **That result has never been reproduced outside
those eight repositories, and both out-of-sample tests attempted so far (human-comment location,
twice) returned nulls in which the ranker scored *below* alphabetical.**

## Method — parameters copied verbatim, not chosen

Every parameter below is taken from `research/phase0/allocation_variants.py` as it already stands.
**Copying rather than choosing is the point**: a parameter re-picked for a fresh corpus is a
parameter tuned on it.

| parameter | value |
|---|---|
| event admission | commits touching **2–12** `.py` files |
| outcome window | a later commit within **90 days** |
| fix words | `fix`, `bug`, `revert`, `hotfix`, `regression`, `broken` |
| target | files shared between the change and the later fix |
| ranking signal | commits touching that file in the **year** before, strictly before the event |
| budget | top **3** files |
| control | **alphabetical** over the same files at the same budget |
| per-repo cap | **400** events |
| exclusion | events where every file scores identically (no ranking to test) |

**Repositories: `scikit-learn`, `pandas`, `django`, `ansible`, `scrapy`, `celery`** — the same six
used for the attention rerun, none among the original eight.

**Blob-filtered clones are acceptable here and this needs stating**, because the constitution warns
that `git log -p` breaks on them. This test reads **file names only** (`--name-only`), which needs
tree objects and not blobs, so the filter is sound. **The exit code is asserted on every read** and
a non-zero exit is fatal, not a zero.

## The readings, fixed now

Let **M_h** be the history top-3 miss rate and **M_a** the alphabetical control's.

| reading | rule |
|---|---|
| **CONFIRMED** | M_a − M_h > 0 **and** McNemar exact **p < 0.05** **and** ≥ 4 of 6 repositories individually show M_h < M_a |
| **NULL** | M_h ≥ M_a, **or** McNemar p ≥ 0.05 |
| **INCONCLUSIVE** | fewer than **500** admissible events, or fewer than **20** discordant pairs |

**The discordant-pair floor matters more than the event count.** Miss rates here are 1–4%, so
McNemar's power comes entirely from the b and c cells. Twenty is the minimum at which a two-to-one
split is distinguishable from chance; below it the test cannot see the effect size being sought,
and reporting a null from it would repeat the instrument error already made twice in this project.

**Consistency guard, identical to the attention rerun**: a pooled win carried by one repository is
the eight-repository artifact happening again, not a refutation of it. **No repository may be
dropped after the fact except for a read failure recorded in the skip ledger.**

## What each outcome means, decided now

**CONFIRMED** — the ranking half has external validity for the first time. It does not resurrect
the review half, and it does not restore "we allocate attention the way a good reviewer would",
which failed on its own terms twice. It establishes exactly one thing: **the ranker points at the
file a later fix returns to, on repositories it has never seen.** That is enough to build the
measurement-layer product on, and it is the first result in this project that would survive a
sceptical outsider asking "yes, but does it work anywhere else?"

**NULL** — **the +1.87-point result is a property of eight repositories, not of ranking.** Three
out-of-sample tests, three nulls. At that point the honest position is that **the ranking half has
no demonstrated external validity at all**, and what remains is:

- **the corrected attribution rule** — 67.9% of file-overlap verdicts blame a change sharing no
  symbol with the fix, three corpora, **computed without the ranker**
- **typed coverage** — a construction, not a measurement: `Unresolved(site, reason, construct)`
  cannot be built without all three fields, so silence is always labelled

**That is a real product and it is a much smaller one than the one currently written down.** It is
an honesty layer over someone else's reviewer, not an attention allocator. **The documents would
need rewriting from the top, and this pre-registration says so before the number exists precisely
so that rewrite is not negotiated afterwards.**

**INCONCLUSIVE** — say so, name the missing power, and do not report the point estimate as
directional. The failure mode this project has hit twice is an instrument that could not have
detected the effect being asked about; the discordant-pair floor exists to catch it a third time.
