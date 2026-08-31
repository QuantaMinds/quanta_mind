# D2c — the same logic written twice, found by a parser

**Branch** `feat/d2c-duplicated-logic`. Build-order item 14, the lowest number that is neither
ticked nor parked after D6a landed. Document row 31 of 50.

## The claim, and why a parser and not a model

> The same logic is written in multiple places, and a fix to one leaves the others wrong.

That is a **structural** question. Two function bodies either have the same shape or they do not,
and a parser answers it exactly, reproducibly, and for free — which is the only kind of claim this
product is allowed to assert. `docs/product/QUANTAMIND.md`: *deterministic beats clever; if a
parser can answer it, a model must not.*

It is also the one place where our own measured weakness points. `research/phase0/bench/forensic/
redundancy.py` scored four arms: we emit **194 comments covering 81 goldens**, Qodo **152 covering
98**. Our redundancy rate is **17.3%** against their **1.0%**, and the rate orders the four arms
exactly as their published quality does. That finding is about our *comments* repeating themselves,
not the customer's code — but the shape of the check is the same one, and it is model-free.

## What gets built

| where | what |
|---|---|
| `parse/body_shape.py` | `shapes_in(source)` — one normalised digest per function body. Pure |
| `parse/duplicate_bodies.py` | `twins(clone, changed)` — walks the tree at the working head, groups by digest, and answers which CHANGED functions have a body that also exists elsewhere |
| `render/relations/duplicate_block.py` | the block. `render/` is at its fifteen-file cap, and `relations/` is D2's sub-package the way `context/` is D6's |

## The normalisation, stated precisely

**Rename-insensitive by ALPHA-EQUIVALENCE, not by deleting names.** Every identifier is replaced by
the position of its first occurrence — `v0`, `v1` — so `def a(x): return x + x` and
`def b(y): return y + y` collide while `def c(y): return y + z` does not. Deleting names outright
would make those last two identical, which is a different function and a false positive on somebody's
pull request.

**Literals are KEPT.** `timeout=30` and `timeout=60` are not the same logic, and a check that said
so would be wrong in the direction that costs a reader their trust.

**Comments are free** — they are not in the AST at all. **A leading docstring is stripped**, because
two functions documented differently and written identically are the duplicate this row is about.

## The floor, which will be MEASURED and not guessed

A one-statement body — `return None`, a property getter, `raise NotImplementedError` — collides with
dozens of others in any repository, and reporting those would bury the real finding. So there is a
minimum size, and **the number is chosen from a run over two real repositories rather than picked**,
the way `D2a` measured `~44% of import statements resolve in-tree` before shipping. The count at
each candidate floor goes in the row and in `docs/engineering/CODEBASE.md`.

## Scope: the tree at head, not a stored index

`twins()` parses the repository as it stands at the reviewed commit, every review, and keeps
nothing. **This is deliberate and it is the lesson of D2b.** That row is `ON HOLD, recommend DROP`:
storing a whole-repository graph cost a table, a migration and a watermark, and in-degree then gave
the same top three as alphabetical on 99.2% of changes. Paying that price again before knowing this
signal is worth anything would be repeating the bet, not learning from it.

What that costs is one `ast.parse` per Python file per review. `parse/suite_reach.reach()` already
walks a clone the same way. **The walk is capped and the cap is reported** — a partial answer that
does not say it is partial is the failure this product exists to refuse.

## What could still silently fail

- **A duplicate outside the tree we walked is invisible**, which is every duplicate in another
  repository and every one in a file the cap cut off. The block says how many files were read.
- **Python only.** `verify/rule_check.py` already returns `LANGUAGE_UNSUPPORTED` for everything
  else and `pyproject.toml` declares `dependencies = []`; tree-sitter is not a dependency.
- **Alpha-equivalence is not semantic equivalence.** Two functions that compute the same thing by
  different structure are not found, and two that differ only by a constant are correctly not found
  but may still be the duplication a human means. This finds *copied* code, not *equivalent* code,
  and the block must not claim otherwise.
