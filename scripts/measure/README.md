# `scripts/measure/` — harnesses that measure the product

Everything here **imports `quantamind`** and answers a question about how the pipeline behaves.
That is why it is not in `research/`: research is a separate uv project on a different
interpreter, and **its interpreter cannot import the product** — every module in this directory
was previously unrunnable from the project it lived in, and had to be invoked with the root
interpreter by hand.

It is equally not in `src/quantamind/`. That is the package a customer installs, declared with
`dependencies = []`; a harness that clones repositories and calls Gemini has no business
shipping inside it, and the layer rule (`types → … → serve`) would bind code that crosses layers
by design.

`scripts/` is the seam that fits: the root interpreter, covered by rule 11's guard and by
`just check`, and not shipped.

## What is here

| module | question it answers |
|---|---|
| `measure.py` + `record.py` | how many findings a review publishes per change, **with its denominator named** |
| `predicts.py` + `run_six.py` | whether import in-degree predicts which file a later fix returns to |
| `attention.py`, `firing_by_size.py` | where human review attention actually goes |
| `borrowed_clones.py` | one clone at a time, so the disk survives a corpus sweep |
| `conversing.py` | conversational review shape |
| `pin_prevalence.py` | how often a commented action pin disagrees with the tag list |
| `rename_blindness.py` | what a rename does to the touch index |

## Running them

Each is a plain script under the root interpreter:

```
uv run python scripts/measure/measure.py --clone .verify-clone --repo owner/name --limit 30 --out out.json
```

`rename_blindness.py` needs the pinned fixture repositories — `just fixtures`, about 1.3 GB.
It fails with `HistoryReadFailed` naming the missing clone rather than silently doing nothing.

## What is tested, and what is not

`record.py` is pure arithmetic and is covered by `tests/unit/measure/test_rate_report.py`, which
pins **all three denominators against hand-computed answers** — the same six findings read as
1.500, 1.000 or 0.600 depending which you pick, and a rate quoted without its denominator is how
this project once reported an instability that did not exist.

The rest drive real clones and real inference. They are not unit-tested and should not pretend to
be: what they produce is checked by the findings they feed, each of which states its own method.

## What stayed in `research/`

`bench/forensic/shape/pulls.py` imports `quantamind` too, but its sibling `shape/tally.py` does
not — it is research analysis. Moving it here would drag a research package product-side, so it
stayed, and it still needs the root interpreter to run. That is a known rough edge, recorded
rather than papered over.

## Duplicated across the boundary

Three modules exist twice, and the copies must be edited together:

| product-side | research-side |
|---|---|
| `scripts/measure/borrowed_clones.py` | `research/phase0/bench/forensic/borrowed_clones.py` |
| `scripts/measure/conversing.py` | `research/phase0/bench/forensic/conversing.py` |
| `scripts/measure/pulls.py` + `tally.py` | `research/phase0/bench/forensic/shape/pulls.py` + `shape/tally.py` |

**This is duplication chosen over a broken import, and the reason is a hard one.** The two
projects run different interpreters: PyCG caps `research/` at Python 3.10, the product needs
`>=3.12` for `sys.monitoring`, and `research/phase0/pyproject.toml` records that a shared
environment cannot satisfy both. **An import across that boundary cannot be made to work** —
declaring `quantamind` as a research dependency fails on exactly that version conflict.

Research still needs these three: `shape_context.py` imports `borrowed_clones` and `pulls`,
`conversational_arm.py` imports `conversing`. Moving them without leaving copies broke those two
files, and nothing caught it — research is not import-checked by `just check`.

**Both of those research files already required the root interpreter before any of this**, since
they transitively import `quantamind`. The move changed which import fails first, not whether
they run. That is why the copies are copies rather than an attempt to make research self-sufficient.

Every duplicated file names its twin in its own docstring, so an edit to one is a visible
prompt to edit the other.
