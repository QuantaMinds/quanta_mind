# Design 13 — what the two Qodo mechanisms did, measured

Pre-registered in `docs/plans/preregistrations/reviewer/expansion-conventions-preregistration.md`
before any model call. Six repositories verified unused, 90 merged pull requests, 80 reviewable,
three arms, blind adjudication, **10 of 10 sabotaged controls caught**.

## The headline: expansion removed the failure class it was built for

**Wrong findings caused by the model not following code that was shown to it fell from 73.3% to
18.8% — a 54.6 point move on the class the mechanism targets.** That is H1, the primary
hypothesis, against a 15-point bar.

**And the mechanism is visible in individual findings, not just in aggregate.** Two claims that
falcon's URI decoder contained an infinite loop died once the model could see ten lines further
back, where `for pos in range(...)` sits. A `for`/`range` loop advances every iteration; the
`continue` the model objected to cannot spin. The refutation was always there, just outside the
window we were showing it.

| pre-registered bar | | result | |
|---|---|---|---|
| **H1** share of wrong findings that failed to follow shown code | ≥ 15 point fall | 73.3% → **18.8%** | **PASS** |
| **H2** wrong-rate with expansion | ≤ 30% | **59.3%** [40.7, 75.5] | **FAIL** |
| **H3** conventions file makes convention-policing worse | ≤ +10 points | **−12.6 points** | **PASS** |
| **H4** yield | ≥ 0.30/PR | 0.41 / 0.40 / 0.46 | **PASS** |

## Why the overall wrong-rate did not move, which is a different fact

H2 failed: 51.7% → 59.3%, intervals overlapping almost entirely. **This is not expansion failing.
It is a second failure class dominating the pool that expansion does not touch.** Reading the two
lines together as "expansion did not work" is the misreading this section exists to prevent.

Cross-tabulating cause against file kind separates them completely.

| file kind | n | wrong | rate | causes |
|---|---|---|---|---|
| **CI config** (`.github/`, `*.yml`) | 36 | 24 | **66.7%** [50.3, 79.8] | **EXTERNAL 23**, TRACE 1 |
| tests | 20 | 10 | 50.0% | TRACE 8, EXTERNAL 2 |
| source code | 29 | 11 | 37.9% | TRACE 8, EXTERNAL 3 |

Every one of those EXTERNAL claims has the same shape: *this commit hash does not exist*, *this tag
was never released*, *this date is in the future*. **Every single one checked against GitHub was
false.** `actions/setup-python@5fda3b95` is tagged exactly `v7.0.0`; `actions/checkout` `v7.0.1`,
`astral-sh/setup-uv` `v9.0.0`, `pre-commit/mirrors-mypy` `v2.3.0`,
`astral-sh/ruff-pre-commit` `v0.15.21` and `PyCQA/isort` `9.0.0b2` all exist;
`hynek/build-and-inspect-python-package` was never renamed and still ships `v3.0.1`.

### The date error is not a training-cutoff artefact, and no filter ends it

The comments the model called "in the future" read **Aug 14–17 2026**. The run was **Aug 18 2026**.
**Three days in the past.** That is not a model whose knowledge stops short of the present; it is a
model with **no reliable notion of the present at all**, which will produce the same error wherever
dates appear. CI configuration is simply where dates cluster.

**This partly retires the registry-lookup arm before it is built.** An arm resolving tags and
hashes against the GitHub API answers roughly 20 of the 23 EXTERNAL claims and does not answer
*what is today*. Excluding the file kind is free and covers more. Design 14 predicts the date error
survives the exclusion, and treats its absence as evidence the diagnosis was wrong.

### This is the third application of the rule, not a new discovery

Lockfiles, dependency manifests and documentation were already excluded on exactly this reasoning.
`.github/` was kept **deliberately and on evidence** — it was producing CORRECT findings at roughly
one in four when the filter was written. It is now 66.7% wrong at n = 36. **The principle did not
change; the evidence did.** Recording it as a rediscovery would understate the process and overstate
the insight.

## H3 inverted, and the reason is not the good news it looks like

The pre-registered fear was that a rules file — mostly style — would buy convention-policing from a
reviewer already a third wrong. **It came back 12.6 points better.** That is the second prediction
this campaign to invert informatively, after the execution gate's anti-correlation.

**But the improvement is bucket composition, not accuracy.**

| arm | n | CORRECT | WRONG | UNFALSIFIABLE | TRIVIAL |
|---|---|---|---|---|---|
| A | 29 | 2 | 15 | 4 | 8 |
| B | 27 | 2 | 16 | 4 | 5 |
| C | 30 | **3** | **14** | **8** | 5 |

From B to C, WRONG fell by 2 while **UNFALSIFIABLE rose by 4 and CORRECT rose by 1**. The
CORRECT-rate barely moves — **6.9% → 7.4% → 10.0%**, intervals [1.9, 22.0], [2.1, 23.4],
[3.5, 25.6], overlapping almost entirely. **The conventions file made the model more cautious, not
more accurate.** A wrong-rate that falls because claims migrate into "cannot be decided" is worth
having, but it is a different purchase from a reviewer that is right more often, and the
CORRECT-rate must be quoted beside it every time.

## The off-CI subgroup, and why it is not the headline

| arm | off-CI wrong-rate | 95% Wilson |
|---|---|---|
| A | 12/23 = 52.2% | [33.0, 70.8] |
| B | 5/13 = 38.5% | [17.7, 64.5] |
| C | 4/14 = **28.6%** | [11.7, 54.6] |

**Post-hoc, not pre-registered, and the intervals overlap almost completely.** A clean monotone
ordering across three arms is exactly what noise looks like at n = 13 and n = 14. The pattern is
consistent with both mechanisms working and equally consistent with chance. **A rule read off the
data it is scored on has no error rate**, which is why design 14 pre-registers a bar of 40% rather
than the 28.6% that inspired it.

## Half A, and an unplanned replication

Of 43 pull requests with resolvable history, **35 touch three or fewer Python files** — where top
three is every file and the ranking decides nothing. **This reproduces the effort-test result on a
different corpus without setting out to**: the ranker is large-PR triage, and this corpus is not
that.

## The reusable defect: git was handing us the answer

Git writes the enclosing declaration into every hunk header and we discarded it. **That is the same
defect as two others already in this record** — `git log --name-only` output that was being parsed
without checking the exit code, and the funcname heuristic. Each time, the tool was supplying
information for free and it was thrown away before anyone looked at it. **The class is worth naming
because it recurs: ask what the tool already tells you before adding a mechanism to compute it.**

The invariant tested was the right one. **Expansion must never move an added line**, because every
published anchor derives from where an added line sits. It held across **664 real hunks at every
look-back from 5 to 60**, five sabotages each broke the whole mechanism rather than its entry
point, and `run13.py` aborts on a single shift.

## The binding number is the CORRECT-rate, and it is worse than the wrong-rate

| arm | CORRECT, all files | per PR | CORRECT off-CI | per PR |
|---|---|---|---|---|
| A | 2 | 0.025 | 1 | **0.013** |
| B | 2 | 0.025 | 1 | **0.013** |
| C | 3 | 0.037 | 1 | **0.013** |

**Off CI config, every arm produced exactly one correct finding across 80 pull requests — one
useful comment per 77.** The wrong-rate has been the headline all along; this is the more damning
number, and it is immune to the denominator games a path filter can play.

**And CI config has a HIGHER correct-rate (11.1%) than everything else (6.0%).** Excluding it
removes 53% of the wrong findings and **57% of the correct ones** — a worse trade than removing
findings at random. The intervals overlap so the reversal is not significant, but there is no
evidence the exclusion raises the correct-rate and the point estimate goes the wrong way. Design
14 is amended accordingly: correct-findings-per-pull-request becomes a **bar**, not a note.

## The pattern: these mechanisms buy caution, not accuracy

Three times now. The ±10-line window converted WRONG into UNFALSIFIABLE. The conventions file did
the same — WRONG −2, UNFALSIFIABLE +4, CORRECT +1. The decidability gate does it by construction.
**Several mechanisms move findings toward "cannot be decided" rather than toward "correct."** That
is honest output and worth having. It is not a reviewer.

## What this does not license

- **The rater designed the experiment.** Arm labels were blind and all ten planted controls were
  caught, but designer bias is unguarded. **None of this counts toward replication.** Four designs
  now owe an independent grader.
- **The corpus was too small and it was said so first.** ~30 findings per arm, interval half-width
  ~17 points. H2's failure is not evidence expansion hurts.
- **Design 11's arm R — the clean design-nine replication — cleared its yield bar** at 0.40/PR
  (0.33 unique), but its wrong-rate is unadjudicated. **The replication count stays at two.** Arm E,
  the evidence field, failed yield at **0.22/PR before adjudication ran**, so it is underpowered by
  its own pre-registration.
- `infer/` stays closed.
