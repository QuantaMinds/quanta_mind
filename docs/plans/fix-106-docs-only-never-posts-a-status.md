# A gate that sometimes declines to speak cannot be a required check

**Branch:** `fix/106-docs-only-never-posts-a-status`. **Status: PLAN.** Written first because it
changes `verify/blocking.py`, which `AGENTS.md` "Working rules" requires, and because the thing it
changes is a decision this repository made deliberately and documented well.

## The observed failure

PR #104 is documentation only. `main` requires `quantamind/declared-rules`. Every CI job is green
and the pull request is `MERGEABLE / BLOCKED`, because **the status never posted**.

It is not `failure`. It is **absent**, which GitHub renders as `pending` — indistinguishable from
"still running". Nobody reading that pull request can tell whether the gate declined, crashed, or
has not finished.

## Two causes, one destination

**One — the docs-only early return.** `serve/review/review_delivery.deliver()` filters to
`REVIEWABLE_SUFFIXES` and returns before `standards_step.applied()` runs, so `announce()` is never
called at all.

**Two — `Standing.NOT_DECLARED` posts nothing on purpose.** `serve/blocking_status.py` says why:

> *"A CHANGE NOTHING GOVERNED GETS NO STATUS. Posting `success` where no rule applied puts a green
> tick against a standard nobody wrote."*

**Both are reachable independently**, so fixing one leaves the other. A repository with a rules file
that governs only `src/` still hits cause two on a change to `scripts/`.

## Why the existing decision was right, and why it is now wrong

**The reasoning protected the meaning of a green tick, and that was the correct thing to protect
while the status was advisory.** A missing signal cost a reader nothing; a misleading one cost them
their trust in the whole column.

**Making the check REQUIRED swapped the cost of the two mistakes.** Silence stopped being a missing
signal and became a deadlocked merge — and a permanently `pending` check is not even legible as a
refusal. **This is the same shape as the defect the product sells against**: "nothing to check here"
and "no answer yet" arriving as the same blank space, on the one surface that holds a merge.

## The change

**`Standing.NOT_DECLARED` posts `success`, and the description carries the distinction.**

```
success — no declared rule governed any file in this change
```

**That is not a claim of compliance.** It is the same move `UNCHECKABLE` makes in the compliance
table: name the state rather than fold it into a pass. A reader who sees that description learns
more than a reader who sees nothing, and strictly more than one who sees `pending` forever.

**And the docs-only path routes through the same call.** `announce(repo, sha, checks=())` yields
`decide(()) -> NOT_DECLARED`, so both causes get one answer and there is no second code path to
forget. `deliver()` stops returning before the gate.

## What must NOT change

- **`BLOCKED` still fails.** Nothing here touches what a violation does.
- **Only a parser's verdict may reach `failure`.** `verify/rule_check.check` returns `DEFERRED` for
  a model-judged rule before any path that can build a violation; that stays.
- **`POSTING_ENABLED=0` still rehearses**, and the gate is still computed and printed so a rehearsal
  shows what it *would* have said.

## What could still silently fail

- **A repository with no rules file now gets a green tick on every pull request.** True, and it is
  the point — but if the description is ever shortened to fit, the tick becomes the lie the old
  decision was protecting against. **The description is load-bearing and a test must pin its text.**
- **`only_pins` still posts its comment.** The pin path is unchanged; this adds a status beside it,
  and a change carrying both should show both.
- **A status failure is still swallowed into a log line.** `commit_status.StatusFailed` is caught and
  the review posts anyway. That is deliberate and unchanged, but it means a network fault here
  produces the same permanently-pending check by a different route — **untouched by this fix, and
  worth its own issue.**

## Sabotage, before any of it is believed

1. **Delete the `NOT_DECLARED` branch entirely** so every change posts a generic success → the test
   pinning the description must fail. A green suite would mean the description is not checked.
2. **Restore the early return in `deliver()`** → a docs-only delivery must be shown to post no
   status, by a named test, or cause one is unguarded again.
3. **Make a violation reach `NOT_DECLARED`** → must still be `failure`. A fix that turned a blocked
   change green would be far worse than the bug it replaced.
