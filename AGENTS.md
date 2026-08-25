<!--
  MAINTAINER NOTE (stripped before the model sees it — costs zero tokens).
  Hard cap: 200 lines. Current budget usage is tracked by scripts/guard/check_agents_md.py.
  Rule of thumb from 2026 practice: past ~80 lines adherence starts dropping, past ~200
  whole blocks get ignored. If you want to add a rule here, first ask whether it can be a
  hook or a CI check instead. If it can, it must be. A rule that lives only in this file
  is a wish, not a rule.
  This file is symlinked as CLAUDE.md so Claude Code, Codex CLI and Cursor all read it.
-->

# QuantaMind (`quantamind`)

Every AI reviewer reads the whole diff at one depth. **We decide where to look first and only
read hard there.** A model-free pass ranks the changed files by how often each has needed a
follow-up fix, and that ranking decides where inference goes.

**The founding correlation test returned NULL** (RR 1.040), killing the earlier product; **this one
inherits none of it.** What justifies it is the only claim here that reproduced out-of-sample:
**top-three-by-fix-history misses 1.21% of the changes a later fix returns to against alphabetical
order's 3.12% — six repositories the method never saw, n = 2,400, p < 1e-6, 6 of 6 positive, 0.05
points from the original eight.** The model-free half replicated; raw model findings are **66.7 to
82.1% wrong**, and an isolated judge of a DIFFERENT family clears every claim before it ships. See
`docs/product/QUANTAMIND.md`, `docs/product/evidence-ledger.md`; `research/` is evidence, not code.

---

## Commands

```bash
uv sync --all-extras            # install
uv run quantamind review <pr>   # NOT BUILT, exits 2  documented-command:unbuilt
uv run quantamind serve         # webhook endpoint; reviews. POSTING_ENABLED=0 rehearses
just check                      # ruff + mypy + guards + unit tests  (run before every commit)
just verify                     # check + live data verification      (run before every PR)
uv run pytest tests/unit -x     # fast loop, ~10s
uv run pytest tests/live        # live runs against real repos, ~4min, NOT mocked
```

`just check` is the gate. If it is red, nothing else matters.

---

## Non-negotiables

These are enforced by hooks and CI. They are listed here so you understand *why*, not so
you remember to obey — the machine will stop you either way.

1. **A green test is not a verified test.** Every behavioural test must assert on data
   produced by a real run, not a mock. `tests/live/` runs the real pipeline against real
   repositories and diffs the output against a checked-in golden file. A test that only
   proves "no exception was raised" is a silent failure waiting to ship.  → `scripts/guard/check_assert_quality.py`

2. **Never emit an unlabeled edge.** Every edge carries a `Confidence` and a `Provenance`.
   There is no default. `Confidence.RESOLVED` requires two independent resolvers agreeing.
   Emitting an edge without provenance is the one bug that destroys the product's reason
   to exist. → enforced by `tests/unit/test_no_bare_edges.py` and a mypy exhaustiveness check

3. **Silence must be typed.** When we cannot resolve a call site we emit an
   `Unresolved(site, reason, construct)` record. We never emit nothing. "No edge here" and
   "we failed here" must never be the same value on the wire.
   → `tests/property/` conservation invariant (`ARCHITECTURE.md` “Invariants”, item 3)

4. **≤200 lines per source file**, docs and `.md` excluded.
   → `scripts/guard/check_structure.py`

5. **≤15 files per directory**, excluding `__init__.py`.
   → `scripts/guard/check_structure.py`

6. **One public concern per module.** A module exports one class or one function family.
   If you need "and" to describe what a file does, split it.
   → **ADVISORY** — no mechanism. Judgement call, caught in review or not at all.

7. **No cross-layer imports.** Layers are `types → store → ingest → parse → rank →
   allocate → infer → verify → render → serve`. Left only — never right, never sideways
   into a sibling's internals. This is what stops `verify` importing `infer`: the layer
   adjudicating the model's claims cannot start trusting them.
   → `scripts/guard/check_conventions.py`

8. **Every file opens with a docstring** stating: what it does, why it exists, what it
   imports and from which layer, and who consumes it.
   → `scripts/guard/check_conventions.py`

9. **Branch per change.** `feat/`, `fix/`, `chore/`, `docs/`, `spike/`. No direct commits
   to `main`. One logical change per PR.
   → `scripts/guard/check_branch_name.py` + `scripts/guard/hooks/hook_pre_edit.py` + branch protection

10. **Docs move with code.** A PR that changes behaviour and does not touch
    `docs/engineering/CODEBASE.md` fails CI. → `scripts/guard/records/check_docs_sync.py`

11. **Research dependencies stay out of the product.** `research/` is a separate uv
    project on a different interpreter. Nothing in `src/` or `scripts/` may import
    pandas, scipy, statsmodels, gitpython, pyyaml, pycg or tree-sitter.
    → `scripts/guard/check_no_research_imports.py`

12. **Every reference names something, never a number.** No section symbols, no phase
    numbers — point at a file path, a class, a function, or a heading's text, something
    that cannot change without someone renaming it on purpose. Numbers break silently:
    insert one heading and every citation points elsewhere, no test fails, and the sentence
    still reads correctly. Eight were dangling when this rule was written. Below: one of
    each banned form, the marker suppressing the guard so the rule can show what it bans —
    counted and printed every run, not an escape hatch. → `scripts/guard/records/check_no_vague_refs.py`

    ```
    §7's gate  →  `PHASE0_RUNBOOK.md` “The 20-PR hand-labelling gate”  no-vague-refs:allow
    Phase 0    →  the correlation test                                 no-vague-refs:allow
    ```

13. **Move files with `git mv`, and never leave two modules with one name.** A stale
    duplicate passed every guard: git tracked both copies, nothing imported the old
    name, and the copy left behind was missing the logic the analysis rested on. On a
    project whose thesis is provenance, letting git lose a rename is not a small irony. → `scripts/guard/check_module_identity.py`

14. **A comment may explain *why*, never assert *whether*.** A safety claim — "this is caught
    later", "callers always hold the lock" — belongs in an assertion, a test, or a returned
    value. A cleanup path claimed a leftover was caught next attempt; it was a different repo,
    nothing checked, 1.6 GB accumulated. `sweep()` returns the count instead.

    **Ask what a check outputs when the thing it checks is broken. If the answer is "the same
    thing", it is not a check.** *Wrong logic*: `all(b >= a)` said True on a flat gradient.
    *Unreachable*: `history_rewritten` ran only on admitted records — zero across 515, identical
    to a genuine null. *Proxy*: an anchor check read 98.1% while raters found them wrong. *Two
    populations*: `candidate in ours_caught` was false for all 194 — both sides `str`. **A clean
    zero is a broken comparison until shown otherwise** — 0 in-window commits then 1,298; 0 of
    1,990 on a bad pathspec; a code search reading 0 tests in a directory full of them.
    **Name the population on both sides of an `in`; a filter admitting NOTHING must raise; and
    every oracle needs a test NAMING the artefact it must find** — "does it return something"
    passes while the instrument is silent. **Only a known-answer test tells these from a real
    negative, and only sabotaging the WHOLE mechanism tests it.** → **ADVISORY** — notice the verb.

15. **A documented command must run, or carry `documented-command:unbuilt`.** `python -m`
    with no `__main__` ignores flags, writes nothing, exits 0 — the runbook's "Days 3–5" reported success and did nothing. → `scripts/guard/records/check_documented_commands.py`

---

## Language and style

- Python 3.12+. `from __future__ import annotations` in every module.
- `mypy --strict`. No `Any` without an adjacent comment explaining the escape.
- Dataclasses are `frozen=True, slots=True` unless mutation is the point.
- No banned name tokens: `util`, `utils`, `helper`, `helpers`, `manager`, `common`,
  `misc`, `shared`, `base`, `core`, `data`, `stuff`. They hide missing abstractions.
  → `scripts/guard/check_conventions.py`
- Errors carry the call site: `raise ResolveError(site=site, reason=...)`, never bare
  `raise ValueError("failed")`.
- No bare `except:`. No `except Exception: pass`. Ever.
- Timeouts on every subprocess call. 30s default, explicit. → `check_subprocess_timeouts.py`

---

## Working rules

- **Plan before you edit.** For anything touching `rank/` or `verify/`, write the plan to
  `docs/plans/<branch>.md` first and have it reviewed. These layers decide where we look
  and what we publish; a wrong turn here is a correctness bug, not a style bug.
- **Fix root causes.** Do not suppress an error, do not add a fallback that fabricates
  data, do not widen a type to make mypy pass. If a resolver cannot resolve something,
  that is a *result*, not a failure — emit `Unresolved`.
- **A corpus drawn from the present cannot answer a question about the future.** Twice — recent
  pages measured activity phase; newly merged PRs gave 0.4 days of forward history against a
  90-day rule. → `research/phase0/corpus_age.py`, which fails at fetch time
- **On a failure or a null, investigate before you fix.** Classify every wrong case by *why*,
  print the distribution, then make the suspected cause a mechanical check and cross-tabulate it
  against the outcome — **a cause that does not separate outcomes is a story.** Three fixes moved
  nothing (p = 0.53); one deep-dive found the mechanism. **Diagnosis or detector — say which.**
- **Reference `file.py:42`, never paste code** into plans or PR descriptions.
- **Scope investigations.** "Read the resolve layer" not "understand the codebase".
- **When you disagree with a rule here, say so in the PR.** Do not silently work around it.

---

## Operational notes

- `just verify` clones `.verify-clone` itself and needs no setup. **Gate 2b is separate**: `just
  fixtures` (~1.3 GB, commits pinned in `tests/fixtures/pinned.json`) then `just gate-2b`.
- **tree-sitter is NOT a dependency.** `pyproject.toml` declares `dependencies = []`. This line
  claimed it was pinned there; it never was. `parse/` reads git's funcname header and nothing else.
- `store/schema.py`: migration + `SCHEMA_VERSION` bump, no re-index in prod. **`just verify` reads
  VALUES, not FORM** — `check_schema_shape.py` fires on the DDL's first move; build the golden THEN.
- **`git log -p` exits non-zero on a blob-filtered clone** and emits a truncated patch stream.
  Any code reading patch content asserts the exit code. This defect voided four measurements.

---

## Definition of done

A change is done when all seven are true. Not six.

1. `just verify` is green
2. A live test asserts on real output, and the golden file was reviewed by a human
3. Coverage of the changed module did not decrease
4. `docs/engineering/CODEBASE.md` reflects the change
5. Module docstrings updated where imports changed
6. The PR description states what could still silently fail and why you think it will not
7. A second reviewer ran `just verify` locally

---

## Principles

- **Honest beats complete.** A 78% coverage number we can defend is worth more than a
  100% claim we cannot. Every competitor ships the second one.
- **Deterministic beats clever.** If a parser can answer it, a model must not.
- **The residual is the product.** What we cannot resolve is not our failure to hide; it
  is the thing the customer is paying us to find.
- **We do not build a better bug-finder — we build the judge.** Four blind pools: **66.7–82.1%
  wrong RAW**; anchor repair, structured context, a rejection filter and hunk expansion moved
  nothing. **Nothing publishes until an isolated judge of a DIFFERENT family clears it** — a
  same-family one agreed with a careful rater on **34.9%**. → `docs/plans/preregistrations/reviewer/design14-model-lever-preregistration.md`
- **Assume the next reader knows nothing.** Every file explains itself to someone who
  joined this morning.
