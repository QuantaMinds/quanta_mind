# Caching the touch index — 32 seconds a pull request, and the one way it goes wrong silently

**Branch:** `feat/touch-index-cache`. **Status: PLAN, not built.** Written first because this is
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

**A commit reachable from the review's base but not from `HEAD`.** The incremental read walks to
`HEAD`; a pull request opened from a branch that `HEAD` has not merged may have base history outside
that walk. `as_of` bounds the *review*, but the *index* is built to `HEAD`. Whether this can produce
a short count needs deciding before build, not after — it is the one case where over-indexing does
not save us.

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
