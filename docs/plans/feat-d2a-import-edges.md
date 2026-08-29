# D2a — labelled import edges

**Branch** `feat/d2a-import-edges`. Build order item 5. Spec: `product-build.md` "D2a Labelled
import edges".

## Why a detector and not a reviewer

`pin_mismatch` fires 24 of 24 with precision 100% **by construction** — a parser and an API, no
model, so no model can be wrong about it. Model findings on the same corpus are 66.7–82.1% wrong
and no gate removes any of them. "This module is imported by 14 others" is the same shape as a pin
mismatch: a question a parser answers exactly, not a judgement a model guesses at.

**So the base rate is measured before this ships**, as `pin_check` did (0.24%, 3 in 1,244). A
detector whose firing rate nobody knows is a detector nobody can price.

## What D2a is

`parse/imports.py`: `edges(path, source, in_tree)` → `(Edge, ..., Unresolved, ...)`. One file's
imports, each labelled. No I/O, no git, no network — the caller supplies the source and the set of
paths in the tree, which is what makes it testable without a repository.

**`RESOLVED` requires two independent resolvers agreeing**, per rule 2 and `types/verdict.py`:
the syntax says the import exists **and** the target is a file in the tree. One alone is `INFERRED`.

| what the source says | outcome |
|---|---|
| `from a.b import c`, `a/b.py` in tree | `Edge(RESOLVED)` |
| `from .pkg import name`, `pkg/__init__.py` in tree, `name` could be a submodule or a symbol | `Edge(INFERRED)` — the second resolver cannot tell which |
| `import requests`, not in tree | `Unresolved(EXTERNAL_SYMBOL, IMPORT)` |
| `importlib.import_module(x)` | `Unresolved(DYNAMIC_DISPATCH, IMPORT)` |
| the file will not parse | `Unresolved(UNPARSEABLE_SYNTAX, FILE)` |

**Every outcome is a value. There is no branch that returns nothing** — rule 3, and the defect
class this session found six times.

## What could silently fail

- **An empty edge list read as "nothing imports this".** It means "no static Python import
  found". `importers.py` already states this; the same wording carries here.
- **A file that parses but whose imports all fall outside the tree** looks identical to a file
  with no imports unless the `Unresolved` records are kept. They are returned, not dropped.
- **`__init__.py` re-exports.** `from .thing import X` where `thing` re-exports from elsewhere is
  a real edge to a file this cannot name. That is `INFERRED`, not `RESOLVED`, and not invisible.

## Done when

`just verify` green; a test asserts on real output for each of the five rows above; sabotaging the
two-resolver rule fails a test; `CODEBASE.md` updated. **D2b and D2d do not start until D2a's
distribution over a real repository is measured and written down.**
