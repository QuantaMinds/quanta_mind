# tests/unit/layers/ — one file per product layer

`tests/unit/` crossed the fifteen-file cap as the product grew, and the split that fell out of the
contents was **the layers themselves**: ingest, parse, store, rank, render, serve. Everything left
in `tests/unit/` is about the project rather than a layer — the CLI, packaging, the guards' own
discovery walk, typed silence, and `test_failures_are_loud.py`, which spans every layer by design
and belongs to none.
