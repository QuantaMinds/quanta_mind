# Every guard, audited: what goes in, what comes out, and where it stays silent

**Run 2026-08-29 over all 24 guard scripts in `scripts/guard/`, 23 of which `just check` invokes.**
Raw data: `research/phase0/results/guard_audit.json`.

The question this answers is not "do the guards pass" — they do. It is **what each one reads,
what it emits, and what it does when handed something it was not written for**, because that is
where a rule stops being a rule without anyone noticing.

## Summary

| | count |
|---|---|
| guard scripts | 24 |
| **fire correctly on a real violation — ALL tested end to end** | **23 of 23 executable** |
| defects found by that testing | **1**, fixed |
| "silent" results that were MY probe being wrong | **5 of 5** |
| report how much they examined | **6 of 24** |
| pass without saying what they examined | **15 of 24** |
| **report a count AND still exit 0 at zero coverage** | **5** |
| exit 0 when pointed at a path that does not exist | 15 |

**The guards work. The gap is that most cannot tell you they worked**, and five of the six that
can would report success having examined nothing.


## Every guard, four dimensions

Each guard was run against: the real repository (**clean**), a violation it must catch
(**fires**), a near-miss it must ignore (**near**), and a tree where its population is empty
(**empty**). Raw data: `research/phase0/results/guard_audit_4d.json`.

| # | guard | reads | clean | fires | near | empty |
|---|---|---|---|---|---|---|
| 1 | `check_agents_md.py` | AGENTS.md: length, and every guard pointer resolves | pass ✓ | fires ✓ | — | refuses ✓ |
| 2 | `check_assert_quality.py` | every test_*.py under the root: assertions and live purity | pass ✓ | fires ✓ | silent ✓ | refuses ✓ |
| 3 | `check_branch_name.py` | the branch name against CONTRIBUTING.md's scheme | pass ✓ | fires ✓ | — | **silent** |
| 4 | `check_constant_time_compare.py` | serve/webhook_github.py's HMAC comparison | pass ✓ | fires ✓ | — | refuses ✓ |
| 5 | `check_conventions.py` | every .py in src/ and scripts/: layering, docstrings, bann | pass ✓ | fires ✓ | silent ✓ | refuses ✓ |
| 6 | `check_enforcement_map.py` | .claude/settings.json both ways: tokens resolve, guards in | pass ✓ | fires ✓ | — | refuses ✓ |
| 7 | `check_module_identity.py` | module basenames per package, and unreachable modules | pass ✓ | fires ✓ | — | refuses ✓ |
| 8 | `check_no_partial_clone.py` | every git clone argument list in the source trees | pass ✓ | fires ✓ | silent ✓ | **silent** |
| 9 | `check_no_research_imports.py` | src/ and scripts/ for research-only packages | pass ✓ | fires ✓ | silent ✓ | refuses ✓ |
| 10 | `check_structure.py` | file lengths and per-directory file counts | pass ✓ | fires ✓ | silent ✓ | refuses ✓ |
| 11 | `check_subprocess_timeouts.py` | every subprocess call site in the source trees | pass ✓ | fires ✓ | silent ✓ | refuses ✓ |
| 12 | `citations/freshness.py` | every figure marked re-check <Month YYYY> | pass ✓ | fires ✓ | silent ✓ | **silent** |
| 13 | `citations/resolve.py` | every citation in prose: .md paths and file.py:NNN | pass ✓ | fires ✓ | silent ✓ | refuses ✓ |
| 14 | `records/check_burned_corpora.py` | every REPOS* literal in quote/corpus.py | pass ✓ | fires ✓ | silent ✓ | **silent** |
| 15 | `records/check_decided_vocabulary.py` | QUANTAMIND.md against three recorded decisions | pass ✓ | fires ✓ | silent ✓ | refuses ✓ |
| 16 | `records/check_docs_sync.py` | every src/quantamind/ directory vs CODEBASE.md | pass ✓ | fires ✓ | — | **silent** |
| 17 | `records/check_documented_commands.py` | `python -m <module>` in docs vs real entry points | pass ✓ | fires ✓ | silent ✓ | **silent** |
| 18 | `records/check_documented_recipes.py` | `just <recipe>` and `quantamind <cmd>` in the docs | pass ✓ | fires ✓ | silent ✓ | refuses ✓ |
| 19 | `records/check_no_vague_refs.py` | tracked text files, for section and phase numbers | pass ✓ | fires ✓ | silent ✓ | **silent** |
| 20 | `records/check_plan_state.py` | the plan-state block vs the real layer counts | pass ✓ | fires ✓ | — | refuses ✓ |
| 21 | `records/check_schema_shape.py` | the DDL in store/schema.py against RECORDED_DIGEST | pass ✓ | fires ✓ | — | refuses ✓ |
| 22 | `records/check_stage_table.py` | summary rows, stage headings and numbered steps vs src/ | pass ✓ | fires ✓ | — | refuses ✓ |
| 23 | `records/check_withdrawn_amendments.py` | WITHDRAWN/ABANDONED rows in the preregistration | pass ✓ | fires ✓ | silent ✓ | **silent** |

**23 of 23 correct on clean, violation and near-miss.** Not one false positive and not one
missed violation, across every guard in the repository.

**Now 5 remain silent, down from 17 when this audit started.** Twelve guards carry a coverage
floor. The five left have populations too small for a floor to mean anything, and saying so is
better than inventing one:

| guard | population | why no floor |
|---|---|---|
| `check_branch_name` | 1 branch name | there is nothing to count |
| `citations/freshness` | 1 dated figure | a floor of 1 is not a check |
| `check_burned_corpora` | 6 REPOS literals | too few to distinguish collapse from change |
| `check_documented_commands` | 6 invocations | as above |
| `check_docs_sync` | 11 directories | marginal; it already fails loudly when a directory is missing from the docs |

**The three named as worth having now have one**, verified in both directions — exit 1 from a
collapsed tree, exit 0 on the real repository: `check_no_partial_clone` (10), 
`check_withdrawn_amendments` (20), `check_no_vague_refs` (40).

**A floor caught my own miscount while being added.** `check_withdrawn_amendments` fired on a
healthy repository because I counted rows with `findall` over the whole document, while
`AMENDMENT_ROW` is anchored with `^` and compiled without `re.M` — it matches per line, as the
guard's own `check()` does. The floor refused before the number could be believed.

### Superseded: what this said before

**8 remain silent when their population is empty**, and for most of them a floor would be
theatre rather than protection — the population is too small for one to mean anything:

| guard | population today | floor worth having? |
|---|---|---|
| `check_branch_name` | 1 branch name | no — there is nothing to count |
| `citations/freshness` | 1 dated figure | no |
| `check_burned_corpora` | 6 REPOS literals | marginal |
| `check_documented_commands` | 6 invocations | marginal |
| `check_docs_sync` | 11 directories | marginal |
| `check_no_partial_clone` | 29 files with a clone call | **yes** |
| `check_withdrawn_amendments` | 56 amendment rows | **yes** |
| `check_no_vague_refs` | 178 markdown files | **yes** |

## What is passed between guards, and the one blind spot

Every guard draws its population from `scripts/guard/discovery.py`, so an over-broad exclusion
there shrinks all 23 at once. Measured: of **519 tracked `.py` files, 518 reach the guards.**

The single exclusion is `research/phase0/external/results/__init__.py`, caught by `results`
being an excluded directory name. **It is not a defect** — the file is five lines whose own
docstring reads *"Data, never code"*, and the 203 tracked files under `data/` and `results/`
directories are run outputs and golden fixtures. Reporting the path without opening it would
have been a false alarm.

**FIXED.** `data` and `results` are no longer bare names. `scripts/guard/exclusions.py` scopes
them to `research/`, so the harness clones that once timed out the pre-edit hook are still
pruned while `src/quantamind/data/` or `scripts/results/` would now be seen. Verified three
ways: the walk yields the same 1,763 files in the same 0.02s, so no pruning was lost; research
scratch paths are still excluded; and product paths under those names are not.

Reverting either property fails a named test in `tests/unit/test_guard_exclusions.py`. A
pre-existing test asserting `"data" in EXCLUDED_DIRS` caught the change and was updated to
assert the scoped behaviour rather than loosened.

The exclusion policy moved to its own module because `discovery.py` was already at exactly the
200-line cap. That is a real seam: `exclusions.py` decides what is out of bounds, `discovery.py`
decides how to reach the rest, and every one of the 23 guards draws its population through the
first — so it should be reviewable without reading a traversal.

## Every guard fires — and one did not, until it was fixed

All 23 executable guards were given the violation they exist for and each returned non-zero.
`plan_claims.py` is a library imported by `check_stage_table`, not a standalone check, and
`coverage.py` is new and carries its own tests.

**`check_assert_quality` accepted `assert True`.** It classified `Name`, `Attribute`, `Call` and
`x is not None` as weak; a bare `Constant` fell through every branch and scored as a STRONG
assertion. So did `assert 1`, `assert "x"`, `assert [1]`, `assert not False` and `assert 1 == 1`.
This is the guard enforcing *a green test is not a verified test*, and it accepted the most
vacuous test that can be written. Fixed in `42079a5` with `test-vacuous-assert`; the
false-positive direction is tested as hard, because a rule that fires on `assert compute() == 1`
gets deleted and takes the hole with it.

**Five guards first appeared silent, and all five were my probe, not the guard.** Recorded
because the difference is the entire discipline:

| guard | why my probe missed |
|---|---|
| `check_decided_vocabulary` | I asserted "rank by file, per developer". The losing side is **"ranks functions"** and **"per seat"** — I had the decision backwards |
| `check_withdrawn_amendments` | I put the row in `CODEBASE.md`; it reads `PHASE0_PREREGISTRATION.md` |
| `check_docs_sync` | I replaced one mention of `allocate/`; the word appears **11 times** and the guard correctly still found it |
| `check_stage_table` | my substitution found no `.py` in the step it picked, so the "violating" line was identical to the real one |
| `check_burned_corpora` | my literal did not match the `REPOS\w*\s*=\s*\(` shape it scans |

**A silent guard is a claim about the guard OR about the probe, and the probe is the more likely
of the two.** Each of the five fires once given a violation it can actually see.

## The finding that matters: five guards pass at zero

`AGENTS.md` rule 14 says *a filter admitting NOTHING must raise*. These five report a coverage
count on the real repository and exit 0 when that count is zero:

| guard | examines today | at zero |
|---|---|---|
| `records/check_decided_vocabulary.py` | 590 paragraphs | passes |
| `records/check_documented_recipes.py` | 82 invocations | passes |
| `check_subprocess_timeouts.py` | 35 call sites | passes |
| `records/check_no_vague_refs.py` | 3 suppressions | passes |
| `citations/freshness.py` | 1 dated citation | passes |

**This is not hypothetical.** If a directory moves, a glob narrows, or a rename breaks discovery,
each of these prints success. `check_subprocess_timeouts` guards a rule about hanging
subprocesses; the day its file discovery breaks it reports "0 call sites checked" and goes green.

The project has hit this exact shape before — `history_rewritten` ran only on admitted records,
returned zero across 515, and was indistinguishable from a genuine null.

## What was fixed, and what was not

**Two of the five now have a floor.** `check_subprocess_timeouts` and
`records/check_documented_recipes` call `scripts/guard/coverage.assert_examined`, which raises
when a guard examined fewer things than the repository must contain. Verified both ways: exit 1
from a tree where discovery collapses, exit 0 on the real repository.

**The floor applies only to this repository, and says when it does not.** A floor is a fact about
these contents; against a test fixture with three files it would fail every time. So
`is_project(root)` gates it — and prints `floor for X not applied` rather than waiving in silence,
because a check that quietly stops applying is the defect being fixed, not a fix. Sabotaging
either the floor or the announcement fails a named test.

**Three still have none:** `records/check_decided_vocabulary` (590 paragraphs),
`records/check_no_vague_refs` (3 suppressions) and `citations/freshness` (1 dated citation). The
first is worth doing; the last two have counts too small for a floor to mean much, and saying so
is better than inventing one.

## Guards that pass without reporting coverage

Fifteen exit 0 saying `ok` and nothing else. They may be examining everything or nothing; the
output cannot distinguish those, and neither can a reviewer:

- `check_agents_md.py`
- `check_branch_name.py`
- `check_constant_time_compare.py`
- `check_conventions.py`
- `check_enforcement_map.py`
- `check_module_identity.py`
- `check_no_partial_clone.py`
- `check_no_research_imports.py`
- `check_structure.py`
- `citations/resolve.py`
- `plan_claims.py`
- `records/check_burned_corpora.py`
- `records/check_docs_sync.py`
- `records/check_documented_commands.py`
- `records/check_plan_state.py`
- `records/check_schema_shape.py`
- `records/check_withdrawn_amendments.py`

This is weaker than the five above — most have no natural denominator — but it is why the audit
had to run each guard against an empty tree rather than read its output.

## The catalogue

Each entry: what it reads, what it emits, and how it behaves on an empty tree, a missing path,
and a binary file.

### `check_agents_md.py`

**Checks:** Three checks on the agent memory file. 1. Length — at most 200 lines. Past ~80 lines adherence starts dropping; past ~200 whole blocks get ignored. 2. Pointers — every `scripts/guard/*.py` the file names must exist. 3. C

**Emits:** `[agents-md]`, `[line]`

**On the real repo:** exit 0, coverage not reported — `[agents-md] ok`

**Empty tree:** exit 2. **Missing path:** exit 2. **Path argument:** used.

### `check_assert_quality.py`

**Checks:** Statically inspects every test function and fails CI when the test cannot possibly have verified a behaviour — no assertions, assertions only on truthiness, assertions only against mocks, or a live test that never touche

**Emits:** `[assert-quality]`

**On the real repo:** exit 1, coverage not reported — `[assert-quality] 28003 violation(s): .venv/lib/python3.12/site-packages/mypy/test/test_con`

**Empty tree:** exit 0. **Missing path:** exit 2. **Path argument:** used.

### `check_branch_name.py`

**Checks:** Fails when the current branch does not match the scheme in CONTRIBUTING.md: feat/ fix/ chore/ docs/ spike/, with fix/ requiring a leading issue number.

**Emits:** `[branch-name]`

**On the real repo:** exit 0, coverage not reported — `[branch-name] ok`

**Empty tree:** exit 0. **Missing path:** exit 0. **Path argument:** used.

### `check_constant_time_compare.py`

**Checks:** Parses `serve/webhook_github.py` and fails unless the HMAC digest is compared with `hmac.compare_digest` and never with `==` or `!=`.

**Reads:** `src/quantamind/serve/webhook_github.py`

**Emits:** `[constant-time]`

**On the real repo:** exit 0, coverage not reported — `[constant-time] ok — the signature comparison is constant-time`

**Empty tree:** exit 1. **Missing path:** exit 1. **Path argument:** used.

### `check_conventions.py`

**Checks:** Three checks that protect separation of concerns and readability. 1. Layering — a module may import only from layers to its left in the declared order (types < discover < ingest < resolve < probe < label < store < serve)

**Reads:** `__init__.py`

**Emits:** `[conventions]`

**On the real repo:** exit 0, coverage not reported — `[conventions] ok`

**Empty tree:** exit 2. **Missing path:** exit 2. **Path argument:** used.

### `check_enforcement_map.py`

**Checks:** Two checks, one in each direction. 1. Resolution — every `guard:`, `ci:` and `hook:` token in the map must name something that exists: a guard file, a justfile recipe or workflow job, or a hook event actually registered.

**Reads:** `__init__.py`, `settings.json`

**Emits:** `[enforcement-map]`

**On the real repo:** exit 0, coverage not reported — `[enforcement-map] ok`

**Empty tree:** exit 2. **Missing path:** exit 2. **Path argument:** used.

### `check_module_identity.py`

**Checks:** Two checks over each package. Duplicate basenames across a package tree, and modules unreachable from any import inside their own tree.

**Reads:** `__init__.py`

**On the real repo:** exit 0, coverage not reported — `[module-identity] ok`

**Empty tree:** exit 0. **Missing path:** exit 0. **Path argument:** ignored, scans a fixed root.

### `check_no_partial_clone.py`

**Checks:** Scans every `git clone` argument list in the source trees for a `--filter` option, in any form: a literal `--filter=blob:none`, a separated `"--filter", "blob:none"`, or an f-string building either.

**Reads:** `scripts/guard/check_no_partial_clone.py`

**On the real repo:** exit 0, coverage not reported — `[no-partial-clone] ok`

**Empty tree:** exit 0. **Missing path:** exit 0. **Path argument:** ignored, scans a fixed root.

### `check_no_research_imports.py`

**Checks:** Fails if anything under src/ or scripts/ imports a package that belongs to research/ only -- pandas, scipy, statsmodels, git, yaml, pycg, tree_sitter.

**Emits:** `[research-imports]`

**On the real repo:** exit 0, coverage not reported — `[research-imports] ok`

**Empty tree:** exit 0. **Missing path:** exit 2. **Path argument:** used.

### `check_structure.py`

**Checks:** Fails CI when any source file exceeds 200 lines, or any directory holds more than 15 files (excluding __init__.py).

**Reads:** `__init__.py`

**Emits:** `[structure]`

**On the real repo:** exit 0, coverage not reported — `[structure] ok`

**Empty tree:** exit 0. **Missing path:** exit 2. **Path argument:** used.

### `check_subprocess_timeouts.py`

**Checks:** Walks every `subprocess.run`, `.Popen`, `.call`, `.check_call` and `.check_output` in the source trees and requires an explicit `timeout=` keyword. Reports the file and line of each one that lacks it.

**Emits:** `[subprocess-timeouts]`

**On the real repo:** exit 0, examined 35 — `[subprocess-timeouts] 35 subprocess call site(s) checked [subprocess-timeouts] ok`

**Empty tree:** exit 0. **Missing path:** exit 0. **Path argument:** ignored, scans a fixed root.

> **PASSES AT ZERO.** It reports how much it examined and exits 0 when that is none, so a broken discovery reads as a clean run.

### `citations/freshness.py`

**Checks:** Finds every figure marked `re-check <Month YYYY>` in the documents and fails when that date has passed. One rule: if a number carries a re-check date, the date is enforced.

**Emits:** `[citation-freshness]`

**On the real repo:** exit 0, examined 1 — `[citation-freshness] ok [citation-freshness] 1 dated figure(s) tracked, 0 suppressed with `

**Empty tree:** exit 0. **Missing path:** exit 0. **Path argument:** used.

> **PASSES AT ZERO.** It reports how much it examined and exits 0 when that is none, so a broken discovery reads as a clean run.

### `citations/resolve.py`

**Checks:** Scans prose for citations and fails when one points at nothing: a `.md` path with no such file, or a `file.py:NNN` past that file's end.

**On the real repo:** exit 0, coverage not reported — `[citations] ok`

**Empty tree:** exit 0. **Missing path:** exit 0. **Path argument:** used.

### `plan_claims.py`

**Checks:** `normalise()`, `exists()`, `referenced()`, `sentences()` and `steps()` -- turn a stage heading, a table cell or a numbered step into the module names it asserts something about, and say whether each is on disk.

**Reads:** `__init__.py`

**On the real repo:** exit 0, coverage not reported — ``

**Empty tree:** exit 0. **Missing path:** exit 0. **Path argument:** ignored, scans a fixed root.

### `records/check_burned_corpora.py`

**Checks:** Reads every `REPOS*` literal in `research/phase0/quote/corpus.py`, fails if any repository is named by more than one, and in `--check owner/name` mode prints every file under `research/` that already mentions a candidate

**Emits:** `[burned-corpora]`, `[repositories]`

**On the real repo:** exit 0, coverage not reported — `[burned-corpora] ok — 36 repositories across 6 corpora, none reused`

**Empty tree:** exit 0. **Missing path:** exit 0. **Path argument:** used.

### `records/check_decided_vocabulary.py`

**Checks:** Scans the product documents for terms where a decision has been taken and the losing side is still quotable -- the ranking unit, the pricing axis, and capabilities that do not ship. Reports the file, the line and which d

**Emits:** `[decided-vocabulary]`

**On the real repo:** exit 0, examined 590 — `[decided-vocabulary] 590 paragraph(s) against 3 decision(s) [decided-vocabulary] ok`

**Empty tree:** exit 0. **Missing path:** exit 0. **Path argument:** ignored, scans a fixed root.

> **PASSES AT ZERO.** It reports how much it examined and exits 0 when that is none, so a broken discovery reads as a clean run.

### `records/check_docs_sync.py`

**Checks:** Two checks. 1. Every directory under src/quantamind/ is mentioned in docs/engineering/CODEBASE.md. 2. In CI, a diff that touches src/ must also touch docs/engineering/CODEBASE.md.

**Emits:** `[docs-sync]`

**On the real repo:** exit 0, coverage not reported — `[docs-sync] ok`

**Empty tree:** exit 0. **Missing path:** exit 2. **Path argument:** used.

### `records/check_documented_commands.py`

**Checks:** Finds `python -m <module>` invocations in the documentation and fails when the named module has no command-line entry point.

**Reads:** `__main__.py`

**Emits:** `[documented-commands]`

**On the real repo:** exit 0, coverage not reported — `[documented-commands] 3 documented command(s) NOT BUILT [documented-commands] ok`

**Empty tree:** exit 0. **Missing path:** exit 0. **Path argument:** used.

### `records/check_documented_recipes.py`

**Checks:** Scans the documentation for `just <recipe>` and `quantamind <subcommand>` and checks each one against reality -- the recipe names in the justfile, and the subparsers registered in `serve/cli.py`. A subcommand `cli.py` it

**Reads:** `src/quantamind/serve/cli.py`

**Emits:** `[documented-recipes]`, `[line]`

**On the real repo:** exit 0, examined 82 — `[documented-recipes] 82 documented invocation(s) checked [documented-recipes] 5 documented`

**Empty tree:** exit 0. **Missing path:** exit 0. **Path argument:** ignored, scans a fixed root.

> **PASSES AT ZERO.** It reports how much it examined and exits 0 when that is none, so a broken discovery reads as a clean run.

### `records/check_no_vague_refs.py`

**Checks:** Scans tracked text files for two classes of reference that read as precise and are not: section-number citations (a section symbol with a number) and phase-number citations (`the stage-0 section`, `the stage-4 section`).

**Reads:** `scripts/guard/records/check_no_vague_refs.py`, `tests/unit/test_no_vague_refs.py`

**Emits:** `[no-vague-refs]`, `[phase-ref]`, `[section-ref]`

**On the real repo:** exit 0, examined 3 — `no-vague-refs: clean (3 line(s) suppressed with 'no-vague-refs:allow')`

**Empty tree:** exit 0. **Missing path:** exit 0. **Path argument:** ignored, scans a fixed root.

> **PASSES AT ZERO.** It reports how much it examined and exits 0 when that is none, so a broken discovery reads as a clean run.

### `records/check_plan_state.py`

**Checks:** Counts the modules in each layer of `src/quantamind/`, renders a table between the `plan-state` markers in `docs/plans/implementation.md`, and exits non-zero when the file does not already contain exactly that. `--write`

**Reads:** `__init__.py`, `docs/plans/implementation.md`

**Emits:** `[layer]`, `[plan-state]`

**On the real repo:** exit 0, coverage not reported — `[plan-state] ok — the plan's state block matches the filesystem`

**Empty tree:** exit 1. **Missing path:** exit 1. **Path argument:** used.

### `records/check_schema_shape.py`

**Checks:** Hashes the DDL in `store/schema.py` and compares it to the value recorded here. On a difference it fails, naming what the change requires: a SCHEMA_VERSION bump, a migration, and the byte-level golden that does not exist

**Reads:** `src/quantamind/store/schema.py`

**Emits:** `[schema-shape]`

**On the real repo:** exit 0, coverage not reported — `[schema-shape] DDL digest 4a95ae6d761071bd, SCHEMA_VERSION 5 [schema-shape] ok`

**Empty tree:** exit 1. **Missing path:** exit 0. **Path argument:** ignored, scans a fixed root.

### `records/check_stage_table.py`

**Checks:** Cross-checks three places `docs/plans/implementation.md` records progress -- the summary table, each `# Stage —` heading's status, and the numbered steps -- against `src/quantamind/` and against each other. Four sound ru

**Reads:** `docs/plans/implementation.md`

**Emits:** `[name]`, `[stage-table]`

**On the real repo:** exit 0, examined 7 — `[stage-table] 7 summary row(s), 6 stage section(s) [stage-table] ok`

**Empty tree:** exit 1. **Missing path:** exit 0. **Path argument:** ignored, scans a fixed root.

### `records/check_withdrawn_amendments.py`

**Checks:** Scans the amendment log for rows declaring something ABANDONED or WITHDRAWN, and requires each to name a `guard:`, `ci:` or `hook:` mechanism that exists -- or to tag itself ADVISORY.

**On the real repo:** exit 0, coverage not reported — `[withdrawn-amendments] ok`

**Empty tree:** exit 0. **Missing path:** exit 0. **Path argument:** ignored, scans a fixed root.
