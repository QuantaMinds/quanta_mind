# scripts/verify/ — empty on purpose

The `justfile` references three scripts that live here and do not exist yet:

| Script | Recipe | Proves |
|---|---|---|
| `compare_golden.py` | `just verify-data` | the pack matches a reviewed golden file |
| `assert_no_source_in_pack.py` | `just verify-no-source-leak` | invariant 6 — no source text leaked |
| `assert_deterministic.py` | `just verify-determinism` | invariant 5 — byte-identical re-index |

## Why they are missing

All three operate on the SQLite pack, and there is no pack. `docs/BUILD_PLAN.md` gates
every layer of product code on Phase 0 reporting a verdict, and
`docs/findings/PHASE0_PREREGISTRATION.md §8` is still empty. Writing a verifier for a
format that has not been designed would mean writing product code before the gate, and
would fix the format by accident — the verifier would become the specification.

## Why the recipes still exist

Deleting them would make `just --list` look complete when it is not. The gap is the
point: `just check` is the gate that must be green today, and `just verify` is the gate
that must be green from Phase 1. Anyone running `just verify` now gets a missing-file
error, which is the honest answer. `docs/VALIDATION.md` explains what each will prove.

**`just check` being green says nothing about whether the output data is correct.** That
is `just verify`'s job, and it cannot do it yet. Do not let a green `check` be quoted as
though it were verification — `docs/VALIDATION.md §1` exists to keep those two claims
apart.
