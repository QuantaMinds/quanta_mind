# Does blast radius predict the fix-return outcome? — pre-registration

**Written and committed 2026-08-29, BEFORE the six-repository corpus is cloned or scored.**
Prior result: `docs/findings/graph/D2D_BLAST_RADIUS_INCONCLUSIVE_2026-08.md` — flask alone gave
**2 discordant pairs against a floor of 20**, and the shipped signal did not reach significance
either, so that run answered nothing.

## The question

Does ranking a change's files by **import in-degree** put the file a later fix returns to in the
top three more often than **alphabetical order** does?

Secondary, recorded but not the gate: does it beat **prior fix count**, the shipped signal, and
does it add anything on top of it?

## The corpus, chosen now

**Selection rules, applied before any arm is scored.** Each is a fact about the repository that
cannot correlate with which ranker wins.

1. **Python-majority**, because `parse/imports.py` reads Python.
2. **Never seen by this project.** Excluded: the pinned six (`ansible`, `celery`, `django`,
   `pandas-dev/pandas`, `scikit-learn`, `scrapy`), the reviewer corpus (`transformers`,
   `curator`, `langchain`, `cartography`, `vllm`, `browser-use`, `skyvern`, `airflow`), and
   `pallets/flask`, which produced the inconclusive run.
3. **Large changes.** Flask's problem was power: 314 of 393 events touched ≤3 files, where a
   budget of three reads everything and no arm can miss. These are libraries whose commits
   routinely span more files.
4. **Deep history**, so events are plentiful without reaching into the last 90 days —
   `research/phase0/corpus_age.py` exists because a corpus drawn from the present cannot answer
   a question about the future.

**The six:**

| repository | why it qualifies |
|---|---|
| `sqlalchemy/sqlalchemy` | large ORM, wide refactors, deep history |
| `numpy/numpy` | large, long-lived, changes span many modules |
| `scipy/scipy` | as above, different maintainer culture |
| `matplotlib/matplotlib` | large, heavy internal coupling |
| `pytest-dev/pytest` | mid-size, high internal import density |
| `encode/django-rest-framework` | mid-size, framework-shaped, unseen |

**This list is final.** Adding a repository after seeing a result, or dropping one that reads
badly, makes the number meaningless — the point of writing it here first.

## The arms

Identical to the prior run, scored with `serve/retrospective.py`'s hit definition and
`rank/events.admissible` imported rather than restated.

- **`importers`** — descending import in-degree at the event's own commit, ties by path.
- **`alphabetical`** — the non-informative control.
- **`prior_fixes`** — the shipped signal, for context.

Budget is three. Events touching ≤3 files are **excluded**, because every arm hits by
construction and including them dilutes the test toward parity.

## The bar, fixed now

**PASS:** ≥20 discordant pairs between `importers` and `alphabetical`, AND exact two-sided
McNemar **p < 0.05** in favour of `importers`.

**FAIL:** ≥20 discordant pairs and p ≥ 0.05, or a significant result favouring `alphabetical`.

**INCONCLUSIVE:** fewer than 20 discordant pairs. **This is a real outcome and it is reported as
one.** The floor comes from `A6_WHAT_A_REVIEW_PRODUCES_2026-08.md`, where a retrospective refused
its own verdict at 10.

**Per-repository results are recorded but the gate is on the pooled count.** Six chances to find
one repository where importers win is six chances to be wrong; the pooled test is the test.

## What happens on each outcome

- **PASS** — D2b and D2d come off hold and are built on a measured signal.
- **FAIL** — D2d is dropped from the build order. Import in-degree does not go in a comment.
- **INCONCLUSIVE** — D2b/D2d stay on hold. No third attempt on a seventh repository, which is
  how a null becomes a hunt.

## What could still silently fail

- **Leakage.** In-degree must be computed at the event's own commit; at HEAD it would include
  importers added *after* the fix being predicted. The harness reads `git ls-tree` at the event
  sha, and the flask run is the regression check.
- **A repository that clones but yields no admissible events** would silently shrink the corpus
  to five. Per-repository event counts are printed and reported.
- **The degenerate exclusion cutting differently per arm.** It is applied to events, before any
  arm is scored, so it cannot.
