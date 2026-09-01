# D1f — a blocking status check, and it may only block on what a parser decided

**Branch** `feat/111-blocking-status-check`. Touches `verify/`, so this plan is written first as
the working rules require. The row it closes is `docs/plans/roadmap/product-build.md`, "D1f
Blocking, not just commenting."

## The claim being made to a customer

That code meets a declared standard **before a human reviewer sees the pull request**. A comment
does not make that claim — it can be scrolled past. A required status check that fails does.

## The predicate, and why it is one line

`Checked.outcome is Outcome.VIOLATED` — nothing else blocks.

This is not a filter bolted on top; it is already structural. `verify/rule_check.check` returns
`Outcome.DEFERRED` for `CheckKind.MODEL_JUDGED` **before any path that can reach `_violation`**, and
`Rule.provenance` is derived from the check kind, never set by a caller. So a model verdict cannot
produce a `VIOLATED` row however the rule was declared. The pin is a test asserting exactly that,
plus a sabotage: let `check()` fall through for `MODEL_JUDGED` and the test must fail by name.

At our measured raw error rate — 66.7 to 82.1% wrong — a model verdict holding somebody's merge is
the single worst thing this product could ship. The gate must be reproducible or absent.

## What the other outcomes do

| outcome | blocks? | why |
|---|---|---|
| `VIOLATED` | **yes** | a parser found it and any auditor can re-run it |
| `PASSED` | no | nothing to say |
| `DEFERRED` | no | a model judged it; reported in the comment, never in the gate |
| `UNCHECKABLE` | no | we failed to decide, and a failure to decide is not a violation |

**`UNCHECKABLE` must be visible in the status description, not swallowed.** Silence and "we could
not check" must never be the same value on the wire (non-negotiable 3). A gate that says "success"
while ten files were unparseable is the proxy failure rule 14 names.

## The OPEN DECISION the row flags — which languages

The row says the tree-sitter constraint "must not be spent by accident". It does not need to be
spent at all: `check()` already returns `UNCHECKABLE`/`LANGUAGE_UNSUPPORTED` for every non-Python
path. So the gate is **Python-only by construction**, a JS file can never block, and the status
description says how many files went unchecked. `pyproject.toml` keeps `dependencies = []`.

## A repository that declared no rules gets NO status, not a green one

`enforce()` returns `()` when nothing is declared. Posting success there would assert compliance
with a standard nobody wrote — the same lie as a green test that asserts nothing. Post nothing.

## Where the code goes — settled

Four modules, one per layer, because no single layer may hold all of it:

| module | layer | what it does |
|---|---|---|
| `verify/blocking.py` | verify | `decide(rows) -> Gate`. Pure. No network, no model. |
| `render/status_check.py` | render | `Gate` -> the state and the one sentence GitHub shows |
| `ingest/publish/commit_status.py` | ingest | writes `(repo, head_sha, state, description)` |
| `serve/blocking_status.py` | serve | the join, the only place all three may meet |

**THE WRITER MUST NOT KNOW WHAT BLOCKS.** The first draft had `commit_status.py` take a `Gate` and
import `Standing` inside the function to read it. `verify` is to the RIGHT of `ingest`, so that was
the sideways reach rule 7 exists to stop — hidden behind a `TYPE_CHECKING` guard that made only the
type import look handled. It takes a state and a sentence now.

Both `ingest/` and `serve/` were at the 15-file cap, and `serve/review_delivery.py` was at exactly
200 lines, so two grouping commits (`ingest/publish/`, `serve/commands/`) had to land first.

**`POSTING_ENABLED` is checked by the caller**, at `serve/review_delivery.py:120` and `:191`.
Nothing under `ingest/publish/` consults it, so the status call needs its OWN check at its own call
site — an inherited one is a gate nobody wrote.

## What could still silently fail

- **The status posts against the wrong SHA.** A status on a stale head blocks nothing.
- **`POSTING_ENABLED=0` must rehearse, not post.** The webhook already honours it; the status path
  is a second caller and needs its own assertion, not an inherited one.
- **A `VIOLATED` row that never reaches the publisher** — `enforce` persists and returns; a caller
  dropping rows would show green. Count rows in, count rows posted, assert equal.
