VOID — do not analyse.

Produced 2026-08-05. Every record is arm=human, every one was REJECTED at
clone_failed in the journal, and none is an admitted unit. parent_sha is empty
on all of them while parent_resolution_method reads "squash".

## CORRECTED 2026-08-11 — this file named the wrong cause, and the real one was
## still live six days later

The sentence removed from here read: *"The pass selected the inverse of the
intended population."* That conflated TWO defects and attributed the visible
symptom to the wrong one.

**The population defect was real.** 17 rows, all rejected at `clone_failed`,
none an admitted unit. That part stands.

**`arm=human` was NOT caused by it.** `assemble.build_record` declared
`arm: str = "human"` as a DEFAULT, and `pilot/run.py` never passed the argument.
So every record it persisted said `human` **regardless of which population was
selected**. A run over exactly the right agent PRs would have produced
`arm=human` on all of them too.

Verified 2026-08-11 on `agent_walk2_records.jsonl`: a walk invoked with
`--arm agent`, whose population `arm.verify` checked against AIDev's own `agent`
column, and whose journal correctly recorded Codex 327, Copilot 79, Devin 85,
Cursor 61 and Claude Code 17 — persisted **310 of 310 records as `arm=human`**.
Six days after this file blamed population selection.

**And the third symptom this file lists is not a defect either.** It reads
"`parent_sha` is empty on all of them while `parent_resolution_method` reads
'squash'". Inspected 2026-08-11: all 17 rows carry `stage_failed = scope`, i.e.
`measure` found no analysable Python at the parent. `run_pipeline.failed()`
builds a failure audit and **never populated `parent_sha`**, while it did copy the
resolved shape. So an empty sha beside a resolved method is what a FAILURE RECORD
looked like, not a resolution that never happened. Three symptoms, one real
population defect, one default-parameter defect, and one artefact of the failure
path — recorded separately because reading them as one is what hid the second.

**Why the correction matters more than the fix.** A wrong diagnosis in a VOID
record is worse than no record: a reader looking for a selection bug would not
find one, and would not look for a default parameter. The defect survived
because a plausible explanation for the same symptom was already written down.

**Fixed 2026-08-11.** `arm` is now REQUIRED on `build_record` — no default, so
omitting it is a type error rather than a human-arm record — and all three
callers pass `candidate.arm`, the same source the journal uses, so the two
artefacts cannot disagree. The 310 records were backfilled from the journal's
per-PR arm column; the pre-fix file is kept as
`agent_walk2_records.WRONG_ARM.jsonl`.

**Why nothing caught it.** `arm.verify` (A32) works, and checks the POPULATION
before the first clone. The exposure pass consumes `PRRecord`, one layer down.
The check was correct about the thing it examined and guarded a quantity that
was not the one at risk — the third appearance of that shape, after A52's star
band and A53's empty-symbol tripwire. The general form, now written into
`AGENTS.md` rule 14: **assert on the artefact the consumer reads, not on the
input that produced it.**

**The mechanism, which is the fourth of its family.** `arm: str = "human"` makes
absence indistinguishable from a value — as `stars=-1` did for size, as
`derived_files=0` did for "never measured", as `or []` did for an unreadable
window. `task_type=""` and `licence=""` keep their defaults deliberately: `""`
denotes UNRECORDED. **A default is safe when it denotes nothing and dangerous
when it denotes something.**
