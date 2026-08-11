# External citations, verified against the live web — August 2026

Every figure this study compares itself to was re-checked against its source rather than
against memory. Two of the checks changed something. One found a unit error in our own
runbook that had survived since the anchor was written.

**Method:** each claim was located in our own files first, then the source was fetched and
the figure read out of it. Where the abstract and the body disagree on units, the body is
quoted. Nothing below is reconciled by inference — a figure either appeared in the source
or it is recorded here as not found.

---

## 1. The comparison anchor — CONFIRMED, and the abstract is a trap

`docs/findings/PHASE0_PREREGISTRATION.md` compares against **11.3%** (agent) and
**21.18%** (human). A casual cross-reference against the paper's abstract would flag both
as wrong, because the abstract reports **3.45%** and **7.40%**.

**Both pairs are real, and they are different units.**

| figure | unit | source text |
|---|---|---|
| 3.45% / 7.40% | **per patch** | abstract; body: "805 of 23,333 patches (3.45%)", "2,733 of 36,991 patches (7.40%)" |
| 11.3% / 21.18% | **per pull request** | §5.1: "affecting 11.3% of agent-generated pull requests"; "impacting 21.18% of human-authored pull requests" |

Our outcome variable is per-PR, so **11.3% and 21.18% are the correct anchors** and the
preregistration uses them correctly. The paper does not state the PR-level denominators;
our `136/642 = 21.18%` from the replication notebook reproduces the paper's own PR-level
figure to the stated precision, which is independent corroboration of the derivation.

## 2. A UNIT ERROR IN OUR RUNBOOK — found by this check

`docs/findings/PHASE0_RUNBOOK.md` "Base-rate sanity check" reads:

> The published breaking-change rates for agent PRs on Python repos are **3.45% for code
> generation, 6.72% refactoring, 9.35% chore**. Our outcome is behavioural (revert/fix
> ≤7d), which should catch **more** than AST detection.

Those three figures are **per-patch**. The sanity check compares them to our **per-PR**
rate. A PR contains many patches, so the two are not comparable in the direction the
check assumes, and the check will read "we catch more" no matter what our rule does —
rule 14's question, in an anchor rather than in a check. The PR-level comparator the
paper supplies is 11.3%.

**Not corrected in place.** The band was pre-registered and A38's correction notes
already forbid moving it quietly; this row records that it rests on the wrong unit and
must be re-derived, exactly as A38 said of the arm.

## 3. What the corrected anchors say about our own rates — A DIVERGENCE

Using the paper's PR-level figures against our third-walk numbers:

| arm | ours | published (PR-level) | ratio |
|---|---|---|---|
| agent | 37.07% | 11.3% | **3.28×** |
| human | 35.05% | 21.18% | **1.65×** |

Same rule, both arms; same detector, both published figures. **A rule uniformly more
permissive than AST detection would inflate both arms by a similar factor. Ours inflates
them by factors a full 2× apart.**

And the direction is opposite: the published data has humans breaking **1.87×** as often
as agents, while A38/A41 measured our arms as indistinguishable across three walks
(Fisher p = 0.795, 0.807, 0.807).

This is recorded, not explained. It admits at least three readings — our rule
over-detects on the agent arm, AST detection under-detects on it, or the arms genuinely
differ on behavioural repair while not differing on API breakage — and nothing here
separates them. **It is written down before the gate rather than after, so whichever way
it resolves, the observation was not made to fit.**

## 4. AIDev dataset scale — CONFIRMED

Our claims: 932,791 PRs / 116,211 repositories; curated subset 33,596 / 2,807 repos at
>100 stars; cutoff 1 Aug 2025. **All confirmed at source.** The paper also reports 72,189
developers and five agents (Codex, Devin, Copilot, Cursor, Claude Code).

**One secondary-source discrepancy, not a correction to us:** a third-party summary gives
"over 933,000 agentic PRs across 61,000 repositories". 61,000 contradicts the paper's
116,211. The paper is the authority; the summary is wrong.

**No August 2026 refresh of AIDev was found.** The dataset remains a 1 Aug 2025 snapshot,
which is what makes `repo_gone` a live and growing category — a full year of drift now.

## 5. Per-agent rates — CONFIRMED, all five

Our table reproduces the source exactly: Codex 2.62, Copilot 3.04, Devin 4.09, Cursor
4.20, Claude Code 5.10. Source: "Claude Code exhibits 74 breaking changes across 1,450
patches (ratio 5.10), while Copilot, Cursor, Devin, and OpenAI Codex have ratios of 3.04,
4.20, 4.09, and 2.62". `74/1450 = 5.10%` confirms these are **per-patch** percentages.

**The table is used only for a relative ordering across the five agents**, so a consistent
unit is all it requires and the ordering holds. It is not compared to our PR-level rate.
The unit is nonetheless now stated in the table, because the runbook error above is what
an unlabelled unit costs.

## 6. Commit-provenance citation — CONFIRMED verbatim

A42 cites arXiv **2607.02774**, *"Was It Never Collected, or Rewritten Away? A
Commit-Provenance Dataset Separating Ingestion Gaps from Upstream History Edits across
the World of Code"*. **Title and identifier match exactly.** The method is confirmed as
described: GHArchive (append-only push events) against World of Code (never deletes a
collected object), classifying every absence.

This one was checked because an arXiv identifier in this project was once guessed and
returned an unrelated paper. It is correct.

---

## Still unverified

- **`arXiv 2601.16809` (*Will It Survive?*), `2603.26130` (SWE-PRBench), `2603.11078`
  (CR-Bench)** — cited in `docs/PROJECT_CONTEXT.md`, not re-checked here. They inform
  positioning, not any number the study computes.
- **Whether AIDev's `repo_gone` rate is measurable against a current GitHub state.** The
  1.6% observed so far is against a one-year-old snapshot and should grow; nothing has
  measured how fast.
