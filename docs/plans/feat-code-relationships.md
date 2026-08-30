# Rules a repository declares, and the checks that enforce them

**Branch:** `feat/code-relationships`. Required by AGENTS.md "Working rules" because this changes
`verify/` — the layer that decides what we publish.

**PART OF THIS IS RETROSPECTIVE, AND SAYING SO IS THE POINT.** D1a and D1b were built before this
file existed; the plan lived in `docs/plans/product/product-build.md` instead. The rule asks for a
plan here so a reviewer sees intent separately from the diff, and writing it afterwards is weaker
than writing it first. Recorded rather than backdated. **This file was then lost once** — see the
incident note at the end — and rewritten from the same intent.

## What changes

| | |
|---|---|
| `types/rule.py` | a declared standard; provenance DERIVED from the check kind |
| `ingest/standards/rules_file.py` | `.quantamind/rules.toml` → rules and typed refusals |
| `parse/python_names.py` | calls, imports and definitions from a syntax tree |
| `types/checked.py` | one audit row: PASSED / VIOLATED / UNCHECKABLE / DEFERRED |
| `verify/rule_check.py` | apply rules to a file, and to a whole change |
| `ingest/blob.py` | a file's text AS THE CHANGE LEAVES IT, not as the clone happens to sit |
| `render/rule_block.py` | what the rules said, with the denominator printed |

## The invariant everything here exists to protect

**A check that did not run must never look like a check that passed.** Only Python is parsed —
tree-sitter is not a dependency — so a TypeScript file yields `UNCHECKABLE`, and
`counts_toward_compliance` keeps it out of the denominator. Without that, a compliance rate reports
OUR parser coverage as the CUSTOMER'S code quality, and it does so most flatteringly on the
repositories we can read least.

This is the fourth appearance of the clean-zero class here. The first three shipped.

## What must not change

- **`render/comment.py` still claims nothing about correctness.** Rule violations are asserted
  because they are reproducible; model findings are not published, and that separation is the
  whole reason an audit trail is worth reading.
- **No new dependency.** `tomllib` and `ast` are stdlib.

## What could still silently fail

- **Nothing persists yet.** Rows are computed and rendered; the audit trail (D4b) needs a schema
  bump, a migration and a regenerated golden, in that order.
- **A rule declared for a language we cannot parse is honest but useless.** The customer sees
  "not decided" forever, and no correctness in this layer fixes that.
- **`check_change` costs one `git show` per changed file**, bounded by the changed-file count and
  never by a model call, but unmeasured on a very large change.

## Incident, 2026-08-27 — a green gate that depended on downloaded data

Mid-branch, ~1,600 files vanished from the working tree: all of `research/`, all of `scripts/`,
and 25 files under `docs/`. Every one was tracked and was restored with `git checkout`. **I do not
know what deleted them**, and no recipe or guard in this repository explains it; `just clean`
targets named paths and was never run. Recorded rather than guessed at.

Two things did not come back, because git never had them:

- `research/phase0/external/revert_pairs.py` — untracked, and genuinely lost.
- The gitignored corpora under `research/phase0/data/`, which are regenerable.

**And restoring exposed a guard that had been passing for the wrong reason.**
`scripts/guard/citations/resolve.py` matches citations by BASENAME. AGENTS.md's own example,
`` `file.py:42` ``, had been resolving against some file of that name inside a downloaded corpus —  <!-- citation:allow — quoting the example, which is the same non-citation -->
so the rule that forbids vague references was itself green because of gitignored data. It now
carries `citation:allow`, which is what an example should have had from the start.

**The cost of my own recovery is recorded too:** `git checkout -- docs/` restored tracked files and
discarded uncommitted edits to `product-build.md` and deleted nothing but cost real work. A
narrower restore, path by path, would not have.
