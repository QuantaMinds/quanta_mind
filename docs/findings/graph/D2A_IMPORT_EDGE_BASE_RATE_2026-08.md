# D2a import edges — the base rate, measured before it ships

**Run 2026-08-29 over two repositories with `parse/imports.edges`. No model, no network.**

`verify/pin_check.py` shipped with its base rate stated — 0.24%, 3 genuine mismatches in 1,244
real pins — because **a detector whose firing rate nobody knows is a detector nobody can price.**
Same discipline here, before D2b stores anything or D2d puts it in a comment.

## The distribution

| | quantamind | pallets/flask |
|---|---|---|
| files | 106 | 24 |
| import statements placed | 571 | 402 |
| **edge, `RESOLVED`** | 246 (**43.1%**) | 184 (**45.8%**) |
| unresolved, `EXTERNAL_SYMBOL` | 325 (56.9%) | 218 (54.2%) |
| edge, `INFERRED` | 0 | 0 |
| unresolved, `DYNAMIC_DISPATCH` | 0 | 0 |
| unresolved, `UNPARSEABLE_SYNTAX` | 0 | 0 |

**Roughly 44% of import statements resolve to a file in the same tree.** That is the material a
blast-radius signal has to work with; the rest are stdlib and third-party names, correctly
reported as unresolved rather than dropped.

## The three zeros, checked rather than believed

A clean zero is a broken comparison until shown otherwise, and there are three here.

- **`DYNAMIC_DISPATCH` 0** — neither repository calls `importlib` anywhere.
- **`INFERRED` 0** — flask declares 108 relative imports and every one resolves to a file in the
  tree, which is the correct outcome, not a missing branch.
- **`UNPARSEABLE_SYNTAX` 0** — every file parses.

**Each branch was then fired on purpose.** A file combining `importlib.import_module`, a
third-party import and a relative import to a missing module produces `INFERRED`,
`EXTERNAL_SYMBOL` and `DYNAMIC_DISPATCH` together. The zeros are properties of these two
repositories, not a dead detector.

## What this does not say

**Nothing about usefulness.** 44% resolution says the graph is buildable, not that "imported by
14 others" predicts anything. D2d is testable against the same fix-return outcome the touch index
uses, and that test has not been run. **This is the cost of the signal, not evidence for it.**

**Two repositories, both Python, one of them ours.** A repository built around dynamic imports,
plugin registries or namespace packages would show a very different mix, and `DYNAMIC_DISPATCH`
existing at 0 here is exactly the number that would move.

**An empty edge list means "no static Python import resolved to a file in this tree".** It does
not mean nothing depends on the file. Any renderer that says otherwise is stating something this
module did not check.
