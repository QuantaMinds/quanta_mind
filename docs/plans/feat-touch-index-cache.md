# Caching the touch index — 32 seconds a pull request, and the one way it goes wrong silently

**Branch:** `feat/touch-index-cache`. **Status: BUILT and verified. The one open question at the
bottom was investigated on 2026-08-27 — see the section after the rule.** Written first because this is
`rank/`-adjacent: the index decides where we look, and the failure mode produces a normal-looking
ranking computed against the wrong past.

## The cost, measured

| repository | commits | Half A | of which `read_touches` |
|---|---|---|---|
| pallets/flask | ~1,500 | 0.6s | — |
| django/django | ~34,000 | 4.6s | — |
| **home-assistant/core** | **115,776** | **32.7s** | **32.1s, 338,907 touches** |

`run_review._index()` calls `read_touches()` on **every** review. The CLI hands it a
`TemporaryDirectory`, so re-reading is honest there. The webhook hands it `settings.database_path`,
a durable store — so a large customer pays a full history read per pull request into a store that
already holds the answer. → `docs/engineering/CODEBASE.md`, the section on the ranker re-ingesting.

## The failure this must not have

**A stale index ranks a change against a history that stopped before it, and the output looks
entirely normal** — same shape, same coverage line, a ranking drawn from the wrong past. Neither
`ingest/` nor the reader can tell. That is the same shape as the fetch-failure rule already in
`serve/working_clone.py`, and it is why this is a plan rather than a patch.

**The correctness condition, stated once:** the index must contain every touch with
`committed_at < as_of`. Over-indexing is safe — `touches.counts()` filters by `as_of` — so the
danger is entirely one-sided. **Missing touches are invisible; extra touches are not a bug.**

## Two traps, both of which this project has hit in other forms

### 1. A timestamp watermark is WRONG. Git history is not chronologically ordered.

"Read everything with `committed_at` greater than the newest row we have" is the obvious design and
it silently drops commits. A rebase, a cherry-pick or a merge of a long-lived branch introduces
commits whose committer date is **older** than rows already indexed. Those touches would never be
read, the count would be quietly low, and every check would pass.

**The watermark is a commit SHA and the incremental read is `git log <watermark>..HEAD`**, which is
reachability, not time. This is the same class as the shape window bug: `--since=30.days.ago` was a
clock answer to a history question. → `ingest/review_window.py`.

### 2. A rewritten history makes the watermark a lie

Force-push, rebase, or a squash-merge that replaces commits leaves a stored SHA that is no longer an
ancestor of `HEAD`. `git log <watermark>..HEAD` then returns a set that omits real history.

**Guard: `git merge-base --is-ancestor <watermark> HEAD` before every incremental read. Not an
ancestor → full re-read, and say so in the output.** The existing store has a `history_rewritten`
field that ran only on admitted records and was zero across 515 — a check that could not fire.
This one must be exercised by a test that actually rewrites a history.

## Design

**Schema 3 → 4.** A `touch_watermark` table: `(repo_id, head_sha, languages, indexed_at)`.

- `head_sha` — the commit the index was built to. The ancestry check runs against it.
- `languages` — the sorted `REVIEWABLE_SUFFIXES` the index was built with. **If the product gains a
  language, every existing index is incomplete for it and an incremental read would never backfill
  it.** A different value invalidates the cache. This is the trap that has no natural symptom.
- `indexed_at` — for the operator, not for correctness. Nothing branches on it.

**`store/touches.py` gains `extend()` beside `index()`.** `index()` keeps its DELETE-then-INSERT
contract exactly as documented — replace, never append, because touches carry no commit identity and
appending the same commit twice doubles its counts. `extend()` appends **only** the touches from
commits in `<watermark>..HEAD`, in the same transaction as the watermark update, so a crash cannot
leave the index ahead of or behind its watermark.

**`run_review._index()` becomes a decision, with three outcomes and all three reported:**

| condition | action |
|---|---|
| no watermark, or `languages` differ | full read (as today) |
| watermark not an ancestor of HEAD | full read, **and print that history was rewritten** |
| watermark is an ancestor | `git log <watermark>..HEAD`, extend |

**A skipped read must not be silent.** The coverage line already exists to say what was not done;
this prints which of the three paths ran and how many commits were read. A cache whose hit rate is
unobservable is a cache nobody can debug.

## Bars, fixed before building

| | bar |
|---|---|
| **correctness** | an incrementally-built index is **byte-identical** to a freshly-built one — same digest, not "close" |
| **rewrite safety** | after a rewritten history, the incremental path **refuses and falls back**, proven by a test that rewrites one |
| **language change** | adding a suffix invalidates the cache, proven by a test that changes the set |
| **speed** | second review on home-assistant/core **under 2s**, against 32.7s today |

**Correctness bar first. If the digests differ the feature does not ship, however fast it is.**

## How it is verified

- **`scripts/verify/assert_deterministic.py` already compares digests across three runs.** Extend it
  to compare *fresh* against *incremental*. That is the known-answer test and it is nearly free.
- **A live test that rewrites history**: index, `git commit --amend`, index again, require the full
  re-read path and a correct final index. Sabotage the whole mechanism, not the entry point.
- **`just verify` reads VALUES, not FORM.** `check_schema_shape.py` fires on the DDL's first move,
  so the golden is rebuilt as part of the schema bump, not after.

## What could still silently fail

**A commit reachable from the review's base but not from `HEAD`.** → **INVESTIGATED below.** It is
real, it predates the cache, it reaches 27 of 100 pull requests on `apache/airflow`, and `--all` is
not the fix because the research this reproduces walks HEAD too.

**The watermark and the rows can disagree.** They are written in one transaction, but nothing
recomputes the index against git to confirm they still match. The digest comparison catches it in
CI; production has no such check, and `verify-pack-vs-git` is a per-path recomputation that could be
adapted.

**A second repository with the same `owner/name`.** `ensure_repo` keys on host and name; two clones
of the same name would share a watermark. Not new, but caching makes it consequential.

## What this does not do

It does not make the first review faster — a cold index still reads everything. It moves a 32-second
cost from every pull request to the first one, which is the right shape for a webhook and does
nothing for a one-shot CLI run.

---

# INVESTIGATED — 2026-08-27. It is real, it predates the cache, and `--all` is not the fix.

## 1. The cache did not introduce it

`read_commits()` with no `since` passes **no revision**, so `git log` defaults to HEAD. The full
read was always HEAD-bounded. The cache walks `<watermark>..HEAD` and inherits exactly the same
horizon — it neither widened nor narrowed it.

## 2. It is real, and the size is easy to show

A repository with three commits to `a.py` on `main` and four more on an unmerged `release/1.0`:

```
git log main       -- a.py   3
git log release/1.0 -- a.py  7
read_touches(...)            3      <- what the product sees
```

A pull request opened against `release/1.0` is ranked with `a.py` scored **3**, on a branch that has
touched it **7** times. The ranking is comparative, so this only moves an outcome when the missing
commits are **concentrated in some changed files and not others** — which is the normal case, since
a release branch touches a particular set of files.

## 3. It is not rare, and it is repo-dependent

Last 100 closed pull requests, share targeting a non-default branch:

| repository | |
|---|---|
| home-assistant/core | **0 / 100** |
| django/django | 3 / 100 |
| **apache/airflow** | **27 / 100** |

**Nothing here is an edge case for a customer who works on release branches.**

## 4. `--all` is not the fix, and this is the part that matters

`research/phase0/external/git_reads.py` — the harness that produced the claim this company rests on
— **also passes no revision, and also walks HEAD.** The product matches the research exactly.

Switching the product to `--all` would index history the research never counted, changing the
touch counts that carry `1.21% against 3.12%, p < 1e-6`. Gate 2a requires the productionised
ordering to reproduce `defect_return.py`'s. **A correctness improvement that silently re-bases the
one validated claim is not an improvement.**

## 5. The right revision is already computed, and thrown away

`serve/review_delivery.py:99` calls `base_commit()` and gets a `Base` carrying **both** `sha` and
`committed_at`. It passes `as_of=committed_at` to `review()` and **discards the sha**. The history
that should be walked is `git log <base.sha>` — everything reachable from the change's own base,
which is precisely the population the ranking is about.

**But base-walking is NOT equivalent to HEAD-walking plus the `as_of` filter, and the difference is
the same non-monotonicity this whole design turns on.** A commit dated before `as_of` that *landed*
after it — a rebase, a cherry-pick — is counted by HEAD-walk-plus-timestamp and is **not** reachable
from the base. So the two policies disagree on exactly the histories where time and reachability
disagree, and switching is a change to the measured policy, not a bug fix.

## What follows

**Not fixed, and now for a stated reason rather than an unexamined one.** Walking from the base is
probably more correct and is certainly not free: it changes the counts, it needs re-validation
against gate 2a, and it breaks the single-watermark cache, since different bases need different
walks.

**What should happen first is a measurement, not a patch**: on a repository with real release-branch
traffic, how often does base-walking change the top-three selection at all? If it never moves the
ranking, this is a documented horizon and nothing more. If it does, it is a pre-registered arm with
gate 2a re-run, not a quiet edit to a `git log` invocation.


---

# MEASURED — 2026-08-27. The horizon moves the counts and almost never moves the reading.

`research/phase0/external/walk_horizon.py`, on `apache/airflow` — the repository with the most
release-branch traffic of the three sampled (27 of 100 recent pull requests target a non-default
branch). **78 merged release-branch pull requests**, each scored twice: touches reachable from HEAD
(what the product does) and from the pull request's own merge-base (what arguably it should).

| reading | result |
|---|---|
| counts differ at all | **63 / 78 — 81%** |
| **which three files are read** | **0 / 78** |
| which file is rank 1 | 3 / 78 |
| **which file gets the DEEP read** | **2 / 78 — 2.6%** |

**The horizon is real and it is nearly always invisible.** Four fifths of these pull requests are
scored from a different number under the two walks, and in none of them did that change which files
the product would read. The ranking is comparative, the shortfall is broadly spread, and a
uniformly lower count selects the same three files.

**Rank 1 is the exception, and it is separate** because the allocator funds rank 1 with a deep read
and ranks 2 and 3 shallow. Of the three order changes, one keeps rank 1 and merely reorders two
shallow slots. Two swap the deep-read target. The clearest is #71042, a two-file change:

```
HEAD-walk rank 1:  task-sdk/tests/task_sdk/definitions/test_callback.py
base-walk rank 1:  task-sdk/src/airflow/sdk/definitions/callback.py
```

The test file wins on the default branch's history; the source file wins on the branch the change
was actually opened against. **A 2.6% chance of pointing the expensive read at the wrong one of two
files** is the whole measured cost of the horizon.

## The verdict, against the cost of changing it

**Not worth changing on this evidence.** Switching to a base-walk changes the touch counts that
carry `1.21% against 3.12%, p < 1e-6`, requires gate 2a to be re-run, and breaks the
single-watermark cache because different bases need different walks. It buys a 2.6% correction to
which file is read deeply, in a repository chosen for having unusually heavy release-branch traffic.
In `home-assistant/core` the rate would be zero, because 0 of 100 pull requests target a non-default
branch at all.

**The HEAD horizon is now a documented property with a number on it, not an unexamined risk.**

## What this measurement does NOT establish

**One repository, one kind of divergence.** Airflow's release branches are cut from main and live
briefly. A long-lived fork whose history diverges for months is the case that would move the set,
and it is not represented here.

**88 of 166 candidates were skipped for changing fewer than two reviewable files** — a one-file
ranking cannot differ, so excluding them is conservative rather than convenient, but it means the
measured population is the larger changes.

**0 of 78 is not zero.** The rule of three puts the 95% upper bound on the set-difference rate at
about 3.8%. "Not observed in 78" is the claim; "cannot happen" is not.
