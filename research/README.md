# research/

Measurement code. Not the product, and not on the product's dependency graph.

Each subdirectory is a **standalone uv project** with its own `pyproject.toml`,
`uv.lock`, `.python-version` and virtual environment. They are deliberately not uv
workspace members: uv's documentation states it "can't ensure that packages don't
import dependencies declared by another workspace member", and a shared environment
would put pandas, scipy and PyCG within import reach of `src/qmctx/`.

`scripts/guard/check_no_research_imports.py` enforces the same boundary a second
way, so it survives someone converting these back into workspace members later.

| Directory | Question it answers | Status |
|---|---|---|
| `phase0/` | Does an unresolved call site predict breakage in AI-authored changes? | harness scaffolded, **not run** |

## phase0

Read in this order:

1. `docs/findings/PHASE0_PREREGISTRATION.md` — what is measured, and the thresholds.
   Fixed before data is seen; changing a threshold afterwards requires an amendment
   entry saying what changed, why, and who approved it.
2. `docs/findings/PHASE0_RUNBOOK.md` — how, day by day, with the controls and the
   failure-diagnosis tree.
3. `phase0/ENVIRONMENT.lock` — the pinned environment, and the three non-obvious
   findings about the instrument that were established by running it rather than
   assumed.

```bash
cd research/phase0
uv sync
uv run pytest          # 33 contract tests; every stage still raises NotImplementedError
```

The modules are stubs. Their tests assert the contract and pin the pre-registered
thresholds as data, so Day 1 implements against a written spec rather than fitting
one to whatever the code happens to produce.

**Nothing here has been run against real data.** `docs/findings/` contains no
results file, and `PHASE0_PREREGISTRATION.md` section 8 is still empty. Until it is
not, the founding correlation is unmeasured and no product code is authorised.
