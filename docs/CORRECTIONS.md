# Corrections

> **ADVISORY — no mechanism, and the reason is stated rather than the tag being a shrug.**
> This file records claims that turned out to have nothing behind them. No guard can check
> that an entry is honest or that the log is complete, and a guard that appeared to would
> be worse than none — the argument `AGENTS.md` already makes for its own advisory rules.
>
> Its job is not enforcement. It is to make one class **recognisable**, so a human catches
> the next instance: **stated authority with nothing behind it.**
>
> Every entry carries four things. The last column is the one that stops this becoming
> decorative — if most entries read "caught by reading", that is a finding about where
> coverage is thin, and the format is what makes it visible.

| # | The claim | What actually held | How it was caught | Mechanism now |
|---|---|---|---|---|
| 1 | A protocol file was cited by path **and section number** as established policy governing how the 20-PR gate must be run. | The file had never been committed. Neither had the section. The real instruction was one line in `PHASE0_RUNBOOK.md` — "Read them yourself" — which predated the citation and said something the fabricated section did not. | By reading. The cited path was checked against the tree, twice, and did not exist either time. | **YES** — `guard:check_citations_resolve`, sabotage-verified against this exact citation. |
| 2 | A31 recorded `--filter=blob:none` as ABANDONED. | The flag stayed in `pipeline/worktree.py` for a day, and **both arms were walked under the strategy the amendment said was abandoned.** | By reading the code after the walks had already run. | **YES** — `guard:check_no_partial_clone` rejects any `--filter`, and `guard:check_withdrawn_amendments` requires a withdrawal to name its enforcer. |
| 3 | The 20-PR gate validated the outcome classifier. | `draw._as_record` **rebuilt** the classifier's input instead of consuming the `PRRecord` the pipeline had written, and got `base_ref`, `arm` and `merged_sha` wrong. The gate certified a classifier the study does not run, on roughly one PR in six. | By reading, after it had already invalidated a gate — chased down from a single disagreement where machine and human gave three different answers for the same PR. | **NO.** No guard catches "this tool rebuilds its input instead of consuming it". `record_for` now returns the stored object and is asserted on **identity**, but that is a test of one call site, not of the class. |

---

## What the last column says

Two of three are now mechanised. The third is the one that matters, and it is the one no
guard reaches.

Entries 1 and 2 are **reference** failures: a citation that resolves to nothing, a
withdrawal that names no enforcer. Both are decidable by pattern, which is why both now
have guards.

Entry 3 is a **provenance** failure — two code paths that each look correct in isolation,
where one silently stands in for the other. Nothing distinguishes a legitimate constructor
from a drifting reconstruction without knowing which artefact is authoritative, and that is
a judgement about intent. It went three fields wrong in a path with **zero test coverage**,
inside the tool whose entire purpose was to validate something else.

The generalisable form, and the thing to watch for:

> **A validation tool must consume the artefact under test, never reconstruct it.**
> Reconstruction is where drift enters, and it enters silently because both paths look
> correct on their own.

---

## Adding an entry

Add one when a claim in this repository — a comment, an amendment, a docstring, a
citation, a test name — turns out not to have been backed by what it asserted. Not for
ordinary bugs. The distinguishing mark is that **something stated a property and nothing
held it**, so the reader had no way to tell from the artefact alone.

Fill the mechanism column honestly, including "NO". An entry claiming coverage it does not
have would be an instance of the class it is filed under.
