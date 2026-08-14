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

| 4 | "All four base branches merged into main later than the PR merged into them, so walking default measures a different week." Stated as a measurement, and a taxonomy was designed on it — the fourth arm was said to be one that *will* fire. | **All four arrived inside the window.** Measured: 1 minute, 3 minutes, 10 minutes, and 3 days 12 hours, against a 7-day window. Walking default would have been valid for every one. | By finally running the query — `git rev-list --ancestry-path <merge_sha>..<default>`, last entry, its committer date. Minutes of work, never done until after the claim had been built on. | **NO.** Nothing catches an unmeasured claim in prose. See the mitigation below. |

---

## The mitigation for entry 4

No guard reads prose for whether a claim was measured. What would have worked here is a
habit, not a mechanism:

> **A claim about the data is either accompanied by the query that produced it, or marked
> as a hypothesis.**

Entry 4 also has a shape worth naming, because it is the reason it went unexamined by
either party. **The unverified claim was conservative** — it predicted more exclusions,
more caution, a wider limitation. That made it comfortable to accept and extend.

An unverified claim that argues for caution attracts less scrutiny than one that argues
for a result, and that asymmetry is how a study accumulates unearned conservatism. The
measured answer was the opposite of the comfortable one in every case.

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

## 5 — A pre-registered check with no possible input

**Claimed:** A56 registers, before the exposure pass, *"`TIMEOUT` rate for EXPOSED against
UNEXPOSED PRs"* as a test of whether graph attrition correlates with the treatment.

**What actually held:** the check cannot be computed and never could have been. A PR that
times out has **no exposure classification**, because timing out is what prevents one —
all 46 timeouts and both OOMs classify as `unanalyzed_resource`. The check compares
timeout rates between two groups that a timeout removes you from.

**How it was caught:** by running it. The join returned zero exposed and zero unexposed
timeouts, which is not a null result — it is the only result the check can produce.

**Mechanism now:** none, and that is the point of this entry. This is a NEW class, distinct
from the ones already logged. Rule 14 asks *what does this check output when the thing it
checks is broken?* — and answers "the same thing", which catches a check that cannot
discriminate. **This check cannot even be evaluated**: its input set is empty by
construction, so it has no output at all, working or broken. The question that would have
caught it is one step earlier: **can this check receive data?**

The second half of A56's timeout check — TIMEOUT rate by scope-file quartile — stands and
is computable. Size selectivity is measurable; correlation with exposure, through this
route, is not.

**ADVISORY.** No guard proposed. A mechanism that decided whether a pre-registered check
has a reachable input set would have to understand the check, and inventing one on a
single instance is how a guard ends up asserting more than it can test.
