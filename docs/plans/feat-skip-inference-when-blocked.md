# Skip inference when a rule already blocks the merge

**Branch:** `feat/skip-inference-when-blocked`. **Status: PRE-REGISTRATION. Nothing is built, and
the first half of this plan argues for not building it.**

Written because `AGENTS.md` "Working rules" requires a plan before touching the layers that decide
what we publish, and because the saving here is obvious enough to be taken on faith — which is the
condition under which this project has been wrong most often.

## What is proposed

`serve/review/review_delivery.py` now runs `standards_step.applied()` before `examine()`, so the
`Checked` rows exist before any inference. `verify/blocking.decide(rows)` folds them into a `Gate`
with no I/O and no model. **So the pipeline can know the merge is already blocked, for free, before
it spends anything.**

The proposal: when `Gate.standing` is blocking, do not call the model. The change cannot merge; the
developer's next act is fixing the violation.

## Why this is not free, stated before the arithmetic

**One — it trades money for coverage, and coverage is what we sell.** *"The residual is the
product."* Skipping inference makes the residual larger. That is survivable only because the
residual is **named** — but a bigger named residual is still a worse review, and the honest
question is whether a customer would take that trade to save us $0.08.

**Two — it can cost a round trip on a process whose bottleneck is round trips.** The developer
fixes the rule and pushes. On the new head we review and report findings. **They then fix those and
push again.** Had we reviewed the first time, they would have fixed both at once. Our own Problem
slide says the measured bottleneck is **16 hours to first pickup** — so buying $0.08 with an extra
review cycle is a bad trade at any plausible volume, and it is the argument most likely to kill
this.

**Three — the trigger is the customer's setting, not ours.** `HIGH` fails the check and `MEDIUM`
and `LOW` do not, and that is deliberately the customer's call. A team that marks everything `HIGH`
would silently stop getting model reviews; a team with no `HIGH` rules would never trigger the skip
at all. **The feature's behaviour would be a function of a configuration they made for an unrelated
reason.**

## The measurement that must come first

**Neither number below has ever been measured, and the feature is worthless if the first is small
or the second is large.** Bars are fixed here, before either is computed.

| | question | bar to build |
|---|---|---|
| **H1** | What share of reviews carry a blocking violation? | **≥ 15%.** Below that the saving is a rounding error against $1.20–$2.00 per developer per month, and the complexity is not repayable |
| **H2** | On those changes, what does the model produce that survives every gate? | **≤ 0.05 kept findings per change.** If a blocked change still yields real findings, skipping them costs the developer a cycle to save us pennies |

**Both bars must pass. Either one failing closes this.**

**Run it on the retrospective corpus, not on production.** `serve/retrospective.py` already replays
merged history from a clone with the index bounded by each change's parent, and
`verify/rule_check.py` is deterministic — so H1 is computable with **no inference at all** over any
repository with a rules file. H2 needs one inference pass over only the changes H1 identifies,
which is the cheapest possible way to buy the answer.

**A repository used to answer this may not be reused later** — `scripts/guard/records/
check_burned_corpora.py` tracks that, and this is exactly the kind of convenience sample that has
cost this project a result before.

## H1 — RUN 2026-09-11. It fails, and the corpus cannot answer the question anyway.

**Result: 0 of 63 changes blocked (0.00%) against a 15% bar. H1 FAILS.**

Model-free, as specified. Walked 300 commits of this repository, read each commit's rules file at
that commit, ran `verify/rule_check.check_all` over every reviewable changed path, and folded the
rows with `verify/blocking.decide`.

| | |
|---|---|
| commits walked | 300 |
| had no rules file **at that commit** | 203 — the file was added 2026-09-01 |
| measured (rules + reviewable files + rows) | **63** |
| `clear` | 63 |
| `blocked` | **0** |
| paths a parser actually decided | 379 |
| rules that fired | **none** |

**Secondary, because a 10-day window is not a history.** Applying HEAD's four rules retroactively
across the whole walk: **0 of 143 changes blocked, 672 paths decided, zero violations.**

### The zero was verified before it was believed

`AGENTS.md` rule 14 — *a clean zero is a broken comparison until shown otherwise.* Known-answer
test on the same instrument:

| planted | result |
|---|---|
| `import pandas` in `src/quantamind/planted.py` | **VIOLATED** `no-research-imports-in-product` → standing **`blocked`** |
| the same import in `research/phase0/x.py` | no violation → **`not_declared`**, correctly out of scope |

**So the instrument detects a violation and respects a path scope. The zero is real.**

### And it still does not answer the question

**The rules file says so itself, in its own header:** *"Every entry was run against this repository's
own history before being added."* **The rules were selected not to fire on existing code**, so a
zero here is manufactured by how they were chosen, not measured.

Three more limits, each on its own sufficient:

- **Four rules**, three `forbid_import` and one `forbid_call` — a narrow surface, and
  `what-to-say.md` already warns that the enforceable surface is narrower than "your standards"
  sounds.
- **In-sample**: our rules, our code, a codebase built to be checkable.
- **No other repository available declares rules at all** — not `.verify-clone`, not the clones
  directory. There is no out-of-sample corpus to move to.

### The disposition

**Do not build it, and the reason is not the 0%.** The reason is that **H1 cannot be earned until a
customer writes a rules file**, and then it must be answered on theirs. The number above is a
property of how we wrote our own rules.

**This is the same blocker as everything else in this plan's neighbourhood**, and it is worth
saying plainly: the optimisation, the demand question and the free-tier cost basis are all waiting
on the same event. **Closed pending a customer corpus. H2 was not run — H1 gates it, and running an
inference pass to answer a question the denominator cannot support would be spending to learn
nothing.**

---

## The design, if both bars pass

**`Reading` REFUSES THE NAIVE VERSION, AND THAT IS THE TYPE DOING ITS JOB.** `allocate/depth.py`
raises on construction:

> `reading nothing while leaving N file(s) unread is not an …`

So "read nothing, leave everything unread" **cannot be expressed**. That is deliberate — it is the
shape of a silent skip, and the constructor exists to refuse it. Two options, and only the second
is acceptable:

1. ~~Carve an exception into `Reading.__post_init__`~~ — **no.** It would reopen the exact hole the
   validation was written to close, for every future caller as well as this one.
2. **A fourth `Depth` value — `Depth.BLOCKED` — with its own `why`, and the skip decided at the
   `examine()` call site rather than inside `plan()`.** `allocate/` must not import `verify/`, so
   `plan()` cannot see the gate; `deliver()` holds both and is where the two meet.

**The comment must say it, in the coverage line, in the customer's words.** Not "3 of 40 files
read" with no reason — *"A rule you wrote is already blocking this change, so we did not spend a
model read on it. Fix that and push; we will read it then."* **A skip that is invisible is the
defect this product exists to refuse**, and `render/blocks/coverage_line.py` is where it lands.

**`Standing.NOT_DECLARED` must not trigger it.** A repository with no rules has declared none; it
is not blocked, and reading it as such would silently stop reviewing every customer who has not
written a rules file yet — which today is all of them.

## What could silently fail

- **The skip fires and nothing says so**, leaving a comment that looks like a completed review of a
  change nobody read. This is the failure that matters; the coverage line is the check, and a live
  test must assert the sentence appears.
- **`Gate.standing` is blocking for a reason that is not a violation.** `blocking.decide` also
  carries `unchecked`; a future change to `Standing` could make a non-violation block and silently
  switch inference off estate-wide. **Key on the violations, not on the standing.**
- **The saving is claimed rather than measured.** Cost per review is recorded in `store/costs.py`
  and readable with `quantamind cost --repo`. **The before-and-after belongs in the PR description,
  from that command, not from arithmetic.**

## Sabotage, before this is believed

`AGENTS.md` rule 14: *ask what a check outputs when the thing it checks is broken.* Three, and each
must fail a **named** test:

1. Force `Gate` to blocking on a change with no violations — **inference must still run.**
2. Make the skip fire and delete the coverage sentence — **a test must fail.** If the suite is
   green with the developer told nothing, the feature is a silent skip with a plan attached.
3. Point it at a repository with no rules file — **`NOT_DECLARED` must not skip.**

## The honest expectation

**H2 is the one that will probably fail**, and the reasoning is already on the record: findings are
**25.0% correct**, but the argument for skipping needs them to be worth *nothing* on blocked
changes specifically, and nothing measured says a change that breaks a declared rule is a change
the model has less to say about. **If it comes back with real findings on blocked changes, the
right answer is to publish them and pay the $0.08** — the cycle is worth more than the cost.

**This document should be read as a proposal to measure, not a proposal to build.**
