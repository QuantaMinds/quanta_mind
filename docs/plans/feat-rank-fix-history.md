# `rank/` — the fix-history ranker

**Required by `AGENTS.md` "Working rules" before any edit to `rank/`.** This layer decides where
we look, so a wrong turn here is a correctness bug rather than a style bug. Nothing in `rank/` is
written until this document has been read by a second person.

**The whole product is now this layer plus the ones that feed it.** `infer/` and `verify/` are not
built and not planned — seven review designs failed pre-registered bars. So `rank/` is no longer
one stage among ten; it is the thing customers pay for, and its output is published unmediated.

---

## What ships

The policy, **copied from the harness that measured it, not re-chosen**:

| parameter | value | where it comes from |
|---|---|---|
| score of a file | commits touching it in the **365 days before** the change | `research/phase0/external/defect_return.py` |
| ordering | `sorted(files, key=lambda f: (-score[f], f))` | same |
| tie-break | **alphabetical by path** | same |
| budget | **top 3** | same |
| decay | **none — a flat count** | same |

**Every parameter is copied deliberately.** A parameter re-picked for production is a parameter
tuned on the corpus that validated it, and this project has already voided measurements that way.
If a value here looks improvable, that is a pre-registered experiment on a fresh corpus, not an
edit to this table.

**The evidence:** 20 repositories, 7,989 events, three disjoint samples. History misses **1.53%**
of the changes a later fix returns to; alphabetical **2.97%**; chance **3.37%**. McNemar exact
p = 1.3 × 10⁻¹⁴, positive in 17 of 20.

---

## Decision one — the unit is the FILE, and `types/change.py` currently says otherwise

**This is the decision that most needs a second reader.**

`ChangedUnit` in `src/quantamind/types/change.py` opens by asserting:

> *"The unit that matters is the FUNCTION, not the file … a file-level type would let file-level
> ranking back in silently, and file-level ranking measures which file is busy, not which one
> comes back."*

**The project's own measurements contradict the second half of that sentence.** Defect-return is
precisely the "which one comes back" test, and the file arm wins it:

| arm | top-3 miss | n |
|---|---|---|
| **file-level** | **1.22%** | 1,969 paired events, 8 repos |
| function-level, 3-unit budget | **8.84%** | same events |
| function-level, 5-unit budget | 3.50% | same events |

+7.62 points, McNemar exact p < 0.0001, discordant b = 157 / c = 7. At **matched coverage**
(top-3 files against top-5 functions) the gap narrows to **+2.29 points** and still favours files.
Nested file-then-function scored **54.2% against its own 61.0% null** — below a non-informative
ranker.

**And only the file arm replicated.** The function arm was measured once, on the eight-repository
development sample. The 20-repository out-of-sample replication that the company's claim rests on
ranks files. Shipping function-level allocation means shipping the arm that lost, on evidence that
never left the sample it was developed on.

### The resolution

**Budget is spent on FILES. Functions order the reading *within* a funded file.**

This keeps the one function-level result that is real — function *ordering* hits the right unit
first 75.0% of the time against 58.9% for any-function-in-the-top-file — without betting coverage
on the arm that lost. Ordering is presentation; allocation is what determines the miss rate.

### What this obliges

1. **Correct the `ChangedUnit` docstring.** It asserts *whether*, and what it asserts is refuted.
   `AGENTS.md` rule 14. The rationale it records is real history and should be kept as history,
   marked as superseded, not silently deleted.
2. **Correct the `CoverageLine` docstring and the `types/` entry in `docs/engineering/CODEBASE.md`.**
   Both quote **8.84%** as the cold-miss rate. That is the function-level figure. Under file-level
   allocation the figure is the file one, and quoting the losing arm's number understates our
   coverage while sounding conservative.
3. **A file-level unit type is needed.** `ChangedUnit.qualified_name` is a function name and
   `__post_init__` refuses an empty one, so a file cannot be represented as a `ChangedUnit`
   without lying about what the field means. Proposal: `RankedUnit.unit` becomes a
   `ChangedFile`, and `ChangedFile` holds the functions it contains. **Do not** overload
   `qualified_name` with a path — that is how a file-level ranking gets in silently, which is the
   thing the original docstring was right to fear even though its reason was wrong.

---

## Decision two — what `rank/` emits when it cannot discriminate

The harness that produced the headline **skips** an event when every file scores the same:
`if len(set(vals)) == 1: continue`. Correct for measuring discrimination, **wrong as a product
spec — production cannot skip a pull request.** Nobody had said how often that case arrives.

**Measured today** — `research/phase0/external/degenerate_rate.py`, same admissibility, every
event classified rather than filtered. 9,600 admissible events across the 12 out-of-sample
repositories:

| case | share | history miss | alphabetical miss |
|---|---|---|---|
| discriminating | **95.39%** | 1.37% | 3.18% |
| flat history (all files tie, non-zero) | 2.98% | 0.70% | 0.70% |
| **no history (every file scores zero)** | **1.64%** | **4.46%** | 4.46% |

**Three things follow.**

**The headline is not materially conditional on the exclusion.** Pooling all three classes gives
1.40% against alphabetical's 3.13%, against the published 1.53% / 2.97% on the differently-sampled
headline run. The filter was not hiding a weakness. *This was worth checking precisely because it
could have gone the other way.*

**In the degenerate classes the ranker IS the alphabetical control** — identical to two decimal
places in both rows, which is not a coincidence but an identity: when every score ties, `(-score,
path)` reduces to `path`. **A ranking that silently degrades to alphabetical while still rendering
as "ranked by fix history" is a claim we cannot support.**

**No-history changes are where we miss most — 4.46%, 3.3× the discriminating rate.** These are the
changes with nothing to rank on and they are the ones most likely to come back. Presenting an
alphabetical list there as a risk ordering is the exact failure this product accuses competitors
of.

### The rule

`Ranking` gains a state distinguishing *ordered by history* from *no history to order by*. Every
unit in a non-discriminating change is `Allocation.COLD` — **read, but not because we ranked it** —
and `render/` says so in those words. This is `AGENTS.md` rule 3 applied to the ranker itself:
"we ranked these" and "we had nothing to rank" must not be the same value on the wire.

**Do not** implement this as a `bool`. `Ranking.fired` already exists and means something else;
a second boolean produces four states of which two are meaningless.

---

## Decision three — what counts as a fix

The outcome rule is: **a commit whose message contains one of `fix`, `bug`, `revert`, `hotfix`,
`regression`, `broken`, landing within 90 days, touching the same file.**

**Hand-checked, only 14% were genuine repairs.** It is a proxy, and it is *load-bearing twice
over* — it defines both the outcome we measure against and the score we rank by.

**It stays as-is for v1, for a reason that is not inertia.** Both arms are scored by the identical
rule, so message noise attenuates the measured gap rather than manufacturing it — a rule that
fired at random would drive both arms toward the same number, not ours above the control. The
gap survived at p = 1.3 × 10⁻¹⁴, so the signal is not the noise.

**What this forbids us from saying.** Any *absolute* statement — "this file has had six bugs" — is
not supported; 86% of those commits are not bug repairs. `render/` may say **"touched by 6 commits
mentioning a fix"** and may not say **"had 6 bugs"**. The difference is the whole honesty claim.

**Deferred, pre-registered:** a stricter signal (linked issue, revert-of, "Fixes #") measured
against the current rule on a fresh corpus, bar fixed first. **Not on the v1 path** — a stricter
rule is only better if it improves ranking, and nobody has measured that.

---

## Decision four — cold start

A repository we have never indexed has no prior-touch index, and the first review must not wait.

**Ranking needs history *before* the change, not history of *our reviews*** — so the index is
built from the customer's existing git history at install time and there is no warm-up period.
`store/` builds it once per repository, then updates incrementally.

**What breaks it:** a shallow or blob-filtered clone. `git log --name-only` needs trees; a
`--filter=blob:none` clone serves them but **`git log -p` exits non-zero and emits a truncated
patch stream, a defect that voided four measurements.** `ingest/` asserts the exit code, and
`Repo.clone_filter` already exists to record which kind of clone produced an index.

**A young repository is the no-history case above**, not a special one. It falls out of Decision
two and needs no separate path.

---

## The modules

Layer order is `types → store → ingest → parse → rank → render`. ≤200 lines each, ≤15 per
directory, one public concern each.

| module | owns |
|---|---|
| `store/schema.py` | the versioned SQLite schema and `SCHEMA_VERSION` |
| `store/touches.py` | the prior-touch index — write and query by `(path, timestamp)` |
| `ingest/history.py` | `git log --name-only`, exit code asserted, timeout declared |
| `ingest/diff.py` | the pull request's changed paths |
| `parse/units.py` | functions within a changed file, `Unresolved` when it cannot |
| `rank/score.py` | the 365-day count. One function. No I/O. |
| `rank/order.py` | `(-score, path)`, the budget, and the `Allocation` labels |
| `rank/discriminate.py` | the three-case classification from Decision two |
| `render/comment.py` | the comment, coverage line first |

**`rank/` must not import `ingest/`.** It receives the index; it does not fetch it. That is what
keeps `rank/score.py` a pure function testable without a repository.

---

## The pre-registered bar

**Fixed before the build. If the live test misses it, the ranker does not ship — it does not get
a threshold adjusted to meet it.**

1. **Golden-file identity.** On at least three pinned submodule repositories, `rank/`'s ordering
   over the same events **matches `defect_return.py`'s ordering exactly**. Not "similar" — the
   same list. A reimplementation that reorders anything has changed the policy, and the policy is
   the thing with the p-value.
2. **Miss rate within its interval.** Top-3 miss on the pinned repositories falls inside
   **0.82–1.81%**, the file-level 95% Wilson interval. Outside it, the reimplementation differs
   from what was measured, whichever direction it lands.
3. **The three cases are reachable in the live test.** A discriminating change, a flat-history
   change and a no-history change each appear in the golden file with a different rendered line.
   **A case that never appears in a fixture is a case nothing tests.**
4. **Sabotage before trust.** Break `rank/score.py` to return a constant and the live test must
   fail. Per the standing rule, break the **whole** mechanism, not the entry point — sabotaging an
   entry point left one of this project's tests green and reading as coverage.

**A same-number result on a re-run is a warning, not a confirmation.** If a rewritten ranker
returns exactly the headline figure, the likeliest explanation is that it is reading the same
cached artefact rather than recomputing. The golden-file identity check is what distinguishes
these.

---

## What could still silently fail

**The index and the query can disagree about a path.** A rename makes `store/` hold the old path
and the diff carry the new one, so the file scores zero and ranks last — **indistinguishable from
a genuinely new file**, and it lands in the no-history class that misses at 4.46%. `git log
--follow` is per-path and does not compose with `--name-only`. *Not solved by this plan.* The
live test must include a renamed file and assert the observed behaviour, so it is at least
recorded rather than discovered.

**The 365-day window is measured on repositories with more than a year of history.** All 20 are
mature projects. A repository younger than the window has a truncated denominator and nothing has
measured that.

**`MAX_FILES = 12`.** The harness only admitted changes touching 2–12 files. Production sees
larger ones and no measurement covers them. `render/` should say when a change is outside the
range the ranking was validated on.

**Percentile thresholds move with repository size.** `Score.percentile` exists because an absolute
threshold fired on 11% of one repository and 53% of another. Any firing rule is per-repository or
it is broken.

**Alphabetical control strength varies by layout.** home-assistant's `components/<x>/` layout puts
the churn-heavy `__init__.py` alphabetically first, so alphabetical there beats chance by +1.75
while sitting at or below chance in five of six other repositories. **Quote the pooled figure
against chance, never a single repository's against alphabetical.**

---

## Out of scope

- Any model call. `Settings.inference_enabled` stays `False` and `Review.ran_model` stays
  falsifiable.
- A stricter fix-signal (pre-registered, deferred).
- Function-level *allocation* — measured, lost, and never replicated.
- Decay weighting, recency weighting, author weighting. Each is a fresh-corpus experiment with a
  bar fixed first, not a tuning knob.
