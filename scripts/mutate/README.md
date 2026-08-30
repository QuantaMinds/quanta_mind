# `scripts/mutate/` — does the suite notice when a number changes?

```bash
uv run python scripts/mutate/sweep.py                 # constants in files this branch changed
uv run python scripts/mutate/sweep.py --all           # every constant in src/quantamind
uv run python scripts/mutate/sweep.py --all --root scripts/guard
```

Exit codes: `0` nothing survived, `1` survivors or a file it failed to restore, `2` refused.

**This is not `scripts/measure/`.** Everything there imports `quantamind` and measures the
product. `sweep.py` deliberately imports nothing from it — it must keep working when a mutation
makes the product unimportable — and what it measures is the SUITE, not the product.

## The number that matters is not "caught"

`sweep.py` runs the mutations; `verdict.py` says what they mean, and the split exists because
counting catches together hid a whole sweep's real result.

The first run on `src/quantamind` caught 29 of 130 mutations and that was reported as coverage.
**Twenty of those 29 were the `-> 0` case**, and zero rarely fails an assertion — it breaks the
code. `BLOB_TIMEOUT_S = 0` failed 23 tests with 69 `TimeoutExpired` and 7 assertions: the suite
saw a crash, not a wrong number. Read as values actually pinned, that run covered **8 constants
of 62**, not 29 of 130.

So every constant is mutated twice, to `0` and to `2n+1`, and lands in one of three states:

| state | means |
|---|---|
| **pinned** | both directions caught — a test actually checks the value |
| **WEAK** | caught only at 0 — the suite noticed a crash, not the number |
| **unseen** | neither caught — nothing distinguishes this value from another |

A WEAK constant is not covered. The suite executes the code, so it notices the number being
catastrophic and would not notice it being wrong.

## What it refuses to do

**A red baseline stops the run.** If the suite already fails, every mutation reads as caught and
the report claims total coverage — the exact failure this tool exists to find. An empty
population refuses for the same reason. A literal that moved since discovery refuses rather than
writing at a stale column, and every file is restored and then re-read.

**Literals are read from the source, not from `repr(value)`.** `30_000` reprs to `"30000"`, five
characters against the six on the line, and slicing by the wrong length skipped three constants
in silence before it was caught.
