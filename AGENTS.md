<!--
  MAINTAINER NOTE (stripped before the model sees it — costs zero tokens).
  Hard cap: 200 lines. Current budget usage is tracked by scripts/guard/check_agents_md.py.
  Rule of thumb from 2026 practice: past ~80 lines adherence starts dropping, past ~200
  whole blocks get ignored. If you want to add a rule here, first ask whether it can be a
  hook or a CI check instead. If it can, it must be. A rule that lives only in this file
  is a wish, not a rule.
  This file is symlinked as CLAUDE.md so Claude Code, Codex CLI and Cursor all read it.
-->

# QuantaMind Context (`qmctx`)

We build the layer that tells a coding agent **what it does not know** about a repository.
Static analysis is unsound by design. We measure the unsoundness, label it per call site,
and serve the labels over MCP so agents abstain instead of guessing.

**The correlation test is not done.** The founding correlation is unmeasured, so no product code is
written yet — see `docs/findings/PHASE0_PREREGISTRATION.md`. If you are asked to implement
a layer, check that file has a filled Results section first. If it does not, say so.

Read `ARCHITECTURE.md` before your first change. Read `docs/PROJECT_CONTEXT.md` for why.

---

## Commands

```bash
uv sync --all-extras            # install
uv run qmctx index .            # build a context pack for the current repo
uv run qmctx serve              # MCP server on 127.0.0.1:7331
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

7. **No cross-layer imports.** Layers are `types → discover → ingest → resolve → probe →
   label → store → serve`. Left only — never right, never sideways into a sibling's
   internals. → `scripts/guard/check_conventions.py`

8. **Every file opens with a docstring** stating: what it does, why it exists, what it
   imports and from which layer, and who consumes it.
   → `scripts/guard/check_conventions.py`

9. **Branch per change.** `feat/`, `fix/`, `chore/`, `docs/`, `spike/`. No direct commits
   to `main`. One logical change per PR.
   → `scripts/guard/check_branch_name.py` + `scripts/guard/hooks/hook_pre_edit.py` + branch protection

10. **Docs move with code.** A PR that changes behaviour and does not touch
    `docs/CODEBASE.md` fails CI. → `scripts/guard/check_docs_sync.py`

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
    counted and printed every run, not an escape hatch. → `scripts/guard/check_no_vague_refs.py`

    ```
    §7's gate  →  `PHASE0_RUNBOOK.md` “The 20-PR hand-labelling gate”  no-vague-refs:allow
    Phase 0    →  the correlation test                                 no-vague-refs:allow
    ```

13. **Move files with `git mv`, and never leave two modules with one name.** A stale
    duplicate passed every guard: git tracked both copies, nothing imported the old
    name, and the copy left behind was missing the logic the analysis rested on. On a
    project whose thesis is provenance, letting git lose a rename is not a small irony. → `scripts/guard/check_module_identity.py`

14. **A comment may explain *why*, never assert *whether*.** A claim of a safety property
    — "this is caught later", "callers always hold the lock" — belongs in an assertion, a
    test, or a returned value. A cleanup path said "a leftover is caught by the strict pass
    on the next attempt"; the next attempt was a different repo, nothing checked, 1.6 GB
    accumulated. `sweep()` returns the count instead — observable, not claimed.

    **Ask what a check outputs when the thing it checks is broken. If the answer is "the
    same thing", it is not a check.** *Wrong logic*: `all(b >= a)` said True on a flat
    gradient. *Unreachable*: `history_rewritten` sat in `scan()`, which runs only on
    admitted records, so it never met its cases — zero across 515 attempts, identical to a
    genuine null. **When a fix breaks a test, ask whether it *asserted* the old behaviour
    or merely *relied* on it.** Two tests certified the corpus-for-GitHub substitution —
    invert them. A control fixture carried `parent_sha=""` and scored 2/2 only because its
    consumer re-resolved — rebuild it. The second is harder to see: the assertion is right,
    and the data was constructible only while the bug lived. **Only a known-answer test
    tells these from a real negative, and only sabotaging the WHOLE mechanism tests the
    known-answer test** — sabotaging the entry point alone left one of ours green and
    reading as coverage: this rule, found inside a sabotage. → **ADVISORY** — notice the verb.

15. **A documented command must run, or carry `documented-command:unbuilt`.** `python -m`
    with no `__main__` ignores flags, writes nothing, exits 0 — the runbook's "Days 3–5" reported success and did nothing. → `scripts/guard/check_documented_commands.py`

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
- Timeouts on every subprocess and every I/O call. Default 30s, declared explicitly.

---

## Working rules

- **Plan before you edit.** For anything touching `resolve/` or `label/`, write the plan to
  `docs/plans/<branch>.md` first and have it reviewed. These layers decide what we claim
  to know; a wrong turn here is a correctness bug, not a style bug.
- **Fix root causes.** Do not suppress an error, do not add a fallback that fabricates
  data, do not widen a type to make mypy pass. If a resolver cannot resolve something,
  that is a *result*, not a failure — emit `Unresolved`.
- **Reference `file.py:42`, never paste code** into plans or PR descriptions.
- **Scope investigations.** "Read the resolve layer" not "understand the codebase".
- **When you disagree with a rule here, say so in the PR.** Do not silently work around it.

---

## Operational notes

- `tests/live/fixtures/repos/` contains pinned git submodules. They are large. `just check`
  skips them; `just verify` needs them. Run `just fixtures` once after cloning.
- tree-sitter grammars are vendored under `vendor/`. Do not `pip install` them; the
  versions are pinned because grammar changes silently alter parse trees.
- The SQLite pack format is versioned. Changing `store/schema.py` requires a migration and
  a bump to `PACK_FORMAT_VERSION`. There is no "just delete the pack" fallback in prod.
- PyCG is vendored and archived upstream. Our fork lives in `vendor/pycg/`. Upstream will
  not accept patches — see `docs/PROJECT_CONTEXT.md#pycg`.

---

## Definition of done

A change is done when all seven are true. Not six.

1. `just verify` is green
2. A live test asserts on real output, and the golden file was reviewed by a human
3. Coverage of the changed module did not decrease
4. `docs/CODEBASE.md` reflects the change
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
- **We do not build a graph.** Upstream MIT projects ship daily and we cannot outrun them.
  We consume one and own the number none of them computes. Resist every temptation to
  improve their graph instead of measuring it.
- **Assume the next reader knows nothing.** Every file explains itself to someone who
  joined this morning.
