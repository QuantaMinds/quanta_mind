# The audit trail — every check on every pull request, on the record

**Branch:** `feat/audit-trail`. Schema change, which `AGENTS.md` "Operational notes" calls out as
the risky kind: *migration + `SCHEMA_VERSION` bump, no re-index in prod*, and
`check_schema_shape.py` fires on the DDL's first move — **build the golden THEN**.

## What is missing

`verify/rule_check.py` produces one `Checked` per rule per file, `render/found_block.py` prints the
violations, and **nothing keeps them**. A compliance reader asking "was this rule enforced on every
pull request last quarter, and what did it say" has no table to ask. That artefact is the thing a
compliance team actually buys, and it is the reason D1b was built before D1c.

## The change

One table, `rule_check`, holding the row `types/checked.py` already models:

| column | why |
|---|---|
| `review_id` | the review it belongs to, found by `(repo_id, pr_number, head_sha)` which is already UNIQUE |
| `rule_id`, `path`, `line` | which rule, on what, where |
| `outcome` | passed / violated / uncheckable / deferred — **all four**, or the denominator is a guess |
| `evidence` | what a developer was shown; empty unless violated |
| `reason` | why it could not be decided; NULL unless uncheckable |
| `provenance` | parser or model — **the column that makes the trail worth reading**, because only a parser's verdict can be re-run and shown to agree |

`SCHEMA_VERSION` 4 → 5, a `_to_5` migration that creates the table and **backfills nothing**. A
review recorded before this step has no checks, and that is the honest state: inventing "passed"
rows would manufacture a compliance history that never happened.

## The order, because it is easy to get wrong

1. Add the DDL and bump `SCHEMA_VERSION`
2. Add `_to_5` to `migrations.py`
3. Run `just check` — `check_schema_shape` FAILS on the digest, which is it working
4. Update `RECORDED_DIGEST` **and** regenerate `test_schema_golden.py`'s golden, then review the
   diff by hand
5. `just verify` — which reads VALUES, and will not notice a DDL mistake the golden would

## What must not change

- **A migrated store must equal a fresh one.** `test_schema_golden.py` asserts it byte for byte,
  which is why the table is created from `TABLES` in the migration rather than written twice.
- **Nothing is backfilled.** Absence of a row means we did not check, not that the check passed.

## What could still silently fail

- **A review with no checks writes no rows**, which is correct and indistinguishable from a review
  whose rows failed to write. The count is asserted at the call site rather than assumed.
- **`provenance` is stored as text.** A new `CheckKind` that forgets to map would write something
  a reader cannot interpret; the writer derives it from `Rule.provenance` rather than accepting it.
- The trail records what we CHECKED, never whether the customer's code was good. Nothing here
  measures the model's accuracy, and no column should be read as though it did.
