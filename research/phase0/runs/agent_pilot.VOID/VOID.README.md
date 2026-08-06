VOID — do not analyse. Superseded, not merely incomplete.

Produced 2026-08-05: two runs, 30 repositories then an extension that reached 38 of 72
before halting. Files: `agent_pilot.VOID.journal.md`, `agent_pilot.VOID.json`,
`agent_records.VOID.jsonl`, `agent_pilot.VOID.log`, and the trace in
`../runs/agent_pilot.VOID/`.

**Every repository here was cloned with `--filter=blob:none`, which A31 had already
ABANDONED.** The amendment was recorded; the flag was never removed from
`pipeline/worktree.py`. A partial clone defers file CONTENTS, so a diff over blobs that
never arrived is EMPTY rather than wrong, and the harness writes `no_python` — a claim
about the repository — when the truth is that a lazy fetch returned nothing.

A31's own evidence for abandoning it: twelve rejections at `derived=0`, three labelled
`no_python` where GitHub lists 104, 65 and 40 `.py` files, 17 of 17 scored PRs CLEAN at
p = 0.0049, and a known-BROKE PR deriving zero symbols.

The numbers this run produced carry that signature and were read as findings:

- `no_python` **18.1%**, against the human arm's 4.0%, reported as an agent-arm property
- **16.7%** of admitted PRs UNSCANNABLE
- breakage **26.67%** (12 of 45), admission **57.45%**

None of them is usable. The `no_python` figure in particular is the bug's fingerprint,
not a fact about how agents write code.

**The human arm is NOT affected.** `git merge-base --is-ancestor` confirms
`rate_journal_v2.md` predates the blobless commit; it was walked with full clones. That
is why this is void rather than the pair being comparable — one arm full, one arm
partial, so every cross-arm difference confounded arm with clone strategy.

Kept rather than deleted because it is the evidence for
`scripts/guard/check_no_partial_clone.py`, which now rejects any `--filter` on a git
clone, and for `check_withdrawn_amendments.py`, which requires a withdrawal to name the
check that enforces it. Both are sabotage-verified.

The run that halted did so correctly: the contents assertion in `pipeline/assemble.py`
fired on a three-file PR that derived two, and raised `HarnessError` rather than
recording an exclusion. It is blind to PRs above `API_FILE_PAGE = 100` files, which is
why A31 chose abandonment over patching — but on the case it can see it stopped a run
instead of producing numbers.

Superseded by the re-walk under full clones.
