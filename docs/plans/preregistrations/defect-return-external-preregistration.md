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


---

# RESULT — 2026-08-14. **CONFIRMED.**

| | |
|---|---|
| n | **2,400** events, **6** fresh repositories, 400 each |
| history top-3 miss | **1.21%**, Wilson [0.84%, 1.73%] |
| alphabetical control miss | **3.12%**, Wilson [2.50%, 3.90%] |
| **lift** | **+1.92 points** |
| relative risk | alphabetical misses **2.59×** as often |
| discordant | b = 62 (history wins), c = 16 (control wins) |
| **McNemar exact** | **p < 0.000001** |
| repositories where history beats the control | **6 of 6** |

**All three pre-registered conditions met**: control beaten, p < 0.05, and ≥ 4 of 6 repositories
individually positive. The floors were cleared with room — 2,400 events against a 500 minimum, 78
discordant pairs against a 20 minimum.

## The replication is the part that matters

| | history | control | lift |
|---|---|---|---|
| original 8 repositories, n = 1,969 | 1.44% | 3.31% | **+1.87** |
| **fresh 6 repositories, n = 2,400** | **1.21%** | **3.12%** | **+1.92** |

**The two lifts differ by 0.05 points.** This is the first result in the project to reproduce
out-of-sample, on repositories chosen after the method was fixed, with every parameter copied
rather than re-picked.

## Per repository, and where the effect actually lives

| repo | n | history | control | lift | b | c | p |
|---|---|---|---|---|---|---|---|
| scrapy | 400 | 2.25% | 9.25% | **+7.00** | 30 | 2 | **0.00000** |
| celery | 400 | 1.00% | 2.50% | +1.50 | 9 | 3 | 0.146 |
| scikit-learn | 400 | 3.00% | 4.00% | +1.00 | 12 | 8 | 0.503 |
| ansible | 400 | 0.25% | 1.00% | +0.75 | 4 | 1 | 0.375 |
| django | 400 | 0.25% | 1.00% | +0.75 | 4 | 1 | 0.375 |
| pandas | 400 | 0.50% | 1.00% | +0.50 | 3 | 1 | 0.625 |

**Only scrapy is individually significant, and that has to be said before the headline is used.**
At a ~1% miss rate, 400 events yield 4–20 discordant pairs, which is nowhere near enough to detect
a one-point difference in a single repository. The individual repositories are *counted*, not
tested — as the pre-registration said they would be.

## Leave-one-out — the result does not rest on scrapy

| excluded | n | lift | p |
|---|---|---|---|
| (none) | 2,400 | +1.92 | < 0.000001 |
| **scrapy** | 2,000 | **+0.90** | **0.011** |
| scikit-learn | 2,000 | +2.10 | < 0.000001 |
| every other repo | 2,000 | +2.00 to +2.20 | < 0.00001 |

**Dropping any single repository, scrapy included, leaves the effect significant.** But scrapy
roughly **doubles** it: without it the lift is +0.90 rather than +1.92. **So the honest effect size
is a range — +0.90 to +1.92 points — and the conservative end is the one to quote.** Scrapy's
alphabetical control misses 9.25%, far worse than anywhere else, which is what a repository with
`scrapy/` and `tests/` at opposite ends of the alphabet looks like.

## Three caveats that travel with the number

**The 400-event cap takes the EARLIEST 400 admissible events per repository**, because the log is
read oldest-first. So this measures early repository history, not recent. It is the same behaviour
as the original harness, which is why the comparison is fair — and it means neither result speaks
to a mature codebase.

**"Defect-return" is the outcome-rule proxy, not a defect oracle.** A later commit within 90 days
whose message contains a fix word and touches the same file. Its own limit is measured: **only 14%
of admitted pairs are genuine repairs.**

**The control is alphabetical, not random.** Alphabetical ordering is not neutral in a Python
repository — it correlates with directory layout. That makes it a *harder* control than random in
some repositories and an easier one in others, and it is the control the original result used,
which is the only reason the two are comparable.

## What this changes

**The ranking half has external validity.** The claim that survived every retraction in this
project — that ranking changed files by prior touch count beats a trivial ordering at containing
the file a later fix returns to — now holds on six repositories it was never developed against, at
an effect size within 0.05 points of the original.

**It does not resurrect the review half**, which was measured at 3 of 66 correct by consensus. It
does not restore *"we allocate attention the way a good reviewer would"*, which failed twice on its
own terms. **Knowing where to look and being right about what you see remain separate, and only the
first is now demonstrated off-corpus.**

---

# SECOND REPLICATION — a third disjoint sample, pre-registered before cloning

**Repositories: `numpy`, `sqlalchemy`, `matplotlib`, `pytest`, `poetry`, `home-assistant/core`.**
None appears in the original eight or the fresh six. Chosen for domain spread — numerics, an ORM,
plotting, a test framework, packaging, and a large IoT platform — because both prior samples were
weighted toward ML and web tooling.

**Everything else is identical and nothing is tuned**: same harness, same parameters copied from
`allocation_variants.py`, same alphabetical control, same 400-event cap, same readings.

| reading | rule |
|---|---|
| **CONFIRMED** | control beaten, McNemar **p < 0.05**, and ≥ 4 of 6 repositories individually positive |
| **NULL** | history at or above the control, or p ≥ 0.05 |
| **INCONCLUSIVE** | < 500 events or < 20 discordant pairs |

**What a failure here would mean, decided now.** Two replications and one failure would put the
effect at "holds on some repository populations and not others", which is a materially weaker claim
than the one now in `AGENTS.md` — and the constitution would have to say so. **A third sample is
worth running precisely because the first replication was strong enough to be worth attacking.**


---

# SECOND REPLICATION — RESULT: **CONFIRMED**, and it exposes a flaw in how the number is reported

| repo | history | alphabetical | lift |
|---|---|---|---|
| poetry | 0.50% | 4.50% | +4.00 |
| matplotlib | 0.50% | 3.50% | +3.00 |
| pytest | 0.75% | 3.00% | +2.25 |
| numpy | 1.25% | 1.75% | +0.50 |
| **home-assistant/core** | **2.50%** | **2.50%** | **0.00** |
| sqlalchemy | 0.50% | 0.00% | −0.50 |

**Pooled: history 1.00%, alphabetical 2.54%, and the pre-registered reading is CONFIRMED.** Three
disjoint samples, twenty repositories, same direction each time.

## Investigating the tie — the first hypothesis was wrong

**Predicted:** home-assistant's changes have flat fix-history, so no ranking can discriminate.
**Measured: false.** Its rank-1-to-rank-2 score gap is **15.19**, *larger* than numpy (7.63),
pytest (9.23) and poetry (9.58) — all repositories where the ranker wins comfortably.

## What actually happened, with the column that was missing

Adding **exact hypergeometric chance**, computed per event, separates the two policies properly:

| repo | history vs chance | alphabetical vs chance |
|---|---|---|
| **home-assistant/core** | **+1.75** | **+1.75** |
| numpy | +1.11 | +0.61 |
| sqlalchemy | −0.04 | +0.46 |
| pytest | +2.17 | −0.08 |
| poetry | +2.80 | −1.20 |
| matplotlib | +1.34 | −1.66 |

**The ranker did not fail on home-assistant. It beat chance by +1.75 there — comparable to
matplotlib and numpy. The control got better.** In five of six repositories alphabetical ordering
sits at or below chance; in home-assistant it is +1.75.

**The reason is layout.** `homeassistant/components/<integration>/…` means the alphabetically first
file in a change is usually that component's `__init__.py` or `config_flow.py` — which is also the
churn-heavy one. **The control accidentally encodes importance there**, so it stops being
non-informative.

**And sqlalchemy's −0.50 is a ceiling effect, not a loss.** Alphabetical missed **0.00%** against a
chance baseline of 0.46%: with 3.53 files per change and a budget of three, there was almost
nothing left to win.

## The correction this forces on the headline

**The published figure — "1.21% against an alphabetical control's 3.12%" — is measured against a
baseline whose strength varies by repository layout.** Part of that gap is the control being weak,
not the ranker being strong.

**The invariant comparison is against exact chance, and it is the one to quote:**

> Third sample, pooled: chance 2.52%, alphabetical 2.54% (**−0.02**, i.e. *no better than
> chance*), history 1.00% (**+1.52**).

**That is a stronger claim, not a weaker one** — it says the ranker beats the arithmetic baseline
rather than beating one arbitrary ordering — and it removes a line of attack a sceptic would
otherwise find. `publishing-rules.md` requires the control be stated with the number; it should now
require the **chance** baseline, because alphabetical alone is not a stable reference.


---

# THE CHANCE BASELINE, ALL THREE SAMPLES — the published figure is conservative, not inflated

Exact hypergeometric chance recomputed per event for every sample, including the original eight.

| sample | n | chance | alphabetical | vs chance | history | vs chance |
|---|---|---|---|---|---|---|
| 1 — the original eight | 3,189 | 4.31% | 3.17% | **+1.14** | 2.16% | **+2.14** |
| 2 — the fresh six | 2,400 | 2.97% | 3.12% | −0.16 | 1.21% | +1.76 |
| 3 — numpy … home-assistant | 2,400 | 2.52% | 2.54% | −0.02 | 1.00% | +1.52 |
| **pooled, 20 repositories** | **7,989** | **3.37%** | **2.97%** | **+0.40** | **1.53%** | **+1.84** |

**McNemar on the pooled set: b = 172, c = 57, p = 1.34 × 10⁻¹⁴. History beats the control in 17 of
20 repositories.** Wilson interval on the history miss rate: **[1.28%, 1.82%]**.

## The worry was backwards

**The concern was that alphabetical might be an unusually weak control, inflating the lift. The
opposite is true: alphabetical is mildly *informative*, +0.40 points better than chance pooled, and
+1.14 in the original eight.**

**So the published `history vs alphabetical` figure UNDERSTATES the effect.** Against a truly
non-informative baseline the ranker is **+1.84** points, not +1.44. The number in the pitch is the
conservative one, which is where a number should sit.

**And an earlier entry in this file overstated the problem.** It said part of the headline gap was
"the control being weak, not the ranker being strong". At the pooled level that is wrong —
alphabetical lands within 0.16 and 0.02 points of chance in samples 2 and 3, and *above* it in
sample 1. **Correcting a good result too eagerly is the same error as defending a bad one too
long**, and it happened here in the direction of understatement.

## What genuinely does not survive: per-repository lift

Alphabetical's strength swings by **3.4 points** across repositories, entirely on directory layout:

| repo | alphabetical vs chance |
|---|---|
| home-assistant | **+1.75** — `components/<integration>/` puts the churn-heavy file first |
| numpy | +0.61 |
| scrapy | −0.81 |
| poetry | −1.20 |
| matplotlib | **−1.66** |

**Quote the pooled figure. Never quote a single repository's lift** — there the control is not a
fixed reference and the number is mostly a fact about folder naming.

**Also corrected by this column: scrapy's +7.00 lift is largely a high baseline.** Its chance miss
is 8.44%, far above any other repository. Against chance it is +6.19 — still the strongest, but the
+7.00 flattered it, and the earlier note that "scrapy roughly doubles the effect" should be read
with that in mind.
