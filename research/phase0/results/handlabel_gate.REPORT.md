# The 20-PR hand-labelling gate: four attempts, no valid result

**Status as of 2026-08-10: the gate has NOT been passed.** One attempt produced a score
(16/20) and was invalidated. Two were withdrawn before scoring. The fourth could not be
drawn. A fifth is blocked on a corpus walk now in progress.

Nothing here is a result. This document exists so the numbers that were produced stay
traceable to the reasons they do not count.

---

## 1. What the gate is for

`PHASE0_RUNBOOK.md` “The 20-PR hand-labelling gate” requires twenty merged agent PRs to be
read by a human, labelled BROKE or CLEAN, and compared against the outcome classifier.
**≥16 of 20 agreement.** Below that, the outcome variable is unreliable and so is every
number downstream of it.

The sample is drawn blind and stratified: ten of each classifier verdict, shuffled, with a
sealed key. Balance is deliberate — at the corpus base rate a random twenty hands the
labeller about two BROKE, so marking everything CLEAN would score ~18/20 and prove nothing.
At 10/10, always-CLEAN scores 10/20 and fails.

**This costs representativeness on purpose.** Agreement estimates the average of
sensitivity and specificity, NOT accuracy over the corpus, and must never be reported as
"right 80% of the time".

---

## 2. Attempt 1 — seed 20260809. Scored 16/20. INVALID

Drawn from the live agent population. Twenty PRs labelled, committed at
`2026-08-09T10:19:00-07:00` **before** the key was opened, then scored:

```
agreement 16/20 (80%)   gate >=16 -> PASS
kappa 0.682   unsure 1   median 9 min

                 human BROKE   human CLEAN
machine BROKE             7              2
machine CLEAN             1              9
```

Labels: CLEAN 11, BROKE 8, UNSURE 1. Preserved as
`handlabel_gate.INVALID.human_labels.csv`; the score as
`handlabel_gate.INVALID.score.json`.

### 2.1 Defect A — the evidence gatherer swallowed a 404

Four labels — **3, 7, 17, 20** — were recorded CLEAN on the stated reason "zero commits in
the 7-day window". There were no commits because **the window could not be read**. All four
PRs merged into branches since deleted:

| label | PR | base ref | resolves |
| --- | --- | --- | --- |
| 3 | policyengine-us#6069 | `BenOgorek/qbid-suite` | 404 |
| 7 | policyengine-us#6052 | `BenOgorek/qbid-suite` | 404 |
| 17 | policyengine-us#6071 | `just-qbid-logic` | 404 |
| 20 | PteraSoftware#32 | `release-3.1.0` | 404 |

The gatherer ended its window query with `or []`. A 404 became an empty list, an empty list
read as "nothing landed after this PR", and that became a verdict that nothing broke.

**Label 20 is provably wrong on its stated reason.** `PteraSoftware#32` merged at
`00:49:29Z`; commit `4098184ef7f1` landed at `02:10:53Z`, eighty minutes later and inside
the window.

### 2.2 Defect B — the gate certified a classifier the study does not run

`handlabel/draw.py`'s `_as_record` **rebuilt** the classifier's input from a `Candidate`
instead of consuming the `PRRecord` the pipeline had written, and got three fields wrong —
each reproducing a defect the pipeline had already fixed and documented:

| field | rebuilt as | consequence |
| --- | --- | --- |
| `base_ref` | never set → `""` | `base_ref_of("")` returns `"HEAD"`, so the scan walked the clone's **default** branch |
| `arm` | hardcoded `"human"` | on a draw invoked `--arm agent` |
| `merged_sha` | `commit_shas[-1]` | the PR's last branch commit, not the merge commit |

15.5% of the corpus merges into `dev`, `develop` or a feature branch, so **the gate was
wrong on roughly one PR in six.**

### 2.3 The two defects masked each other

On `PteraSoftware#32` three components gave three different answers:

- **pipeline** — base `release-3.1.0` is gone → `UNSCANNABLE`
- **gate** — walked `main` instead → found `4098184ef7f1` → `BROKE`
- **human** — gatherer swallowed the 404 → saw nothing → `CLEAN`

Machine and human disagreed because they were reading different branches, **neither of
them the right one.**

### 2.4 Why 16/20 could not be salvaged

Labels 3, 7 and 17 *agreed* with the machine, so dropping only label 20 keeps 16/20. That
rescues nothing: three labels agreeing while resting on no evidence is two instruments
sharing a blind spot, not agreement. And the key was open, so any re-label by that labeller
is anchored.

### 2.5 What survived as signal

The two genuine disagreements point in **opposite** directions, which is information about
the rule and worth keeping:

- **`langgraph#4947` — rule too LOOSE.** A docstring-only change marked BROKE because a
  later commit touched the same file.
- **`prometheus-metrics-bundle#118` — rule too TIGHT.** Missed a same-day fix to scripts
  the PR itself created.

### 2.6 Who labelled it

`PHASE0_RUNBOOK.md` says **"Read them yourself."** An agent did the reading. That line
predates the session and should have been raised before the labelling rather than after.

---

## 3. Attempt 2 — seed 20260810. Withdrawn before labelling

Drawn from `agent_rewalk_records.jsonl` with the pipeline fixed: the draw now consumes real
`PRRecord`s (`record_for` returns the stored object, asserted on **identity**).

- 10 BROKE / 10 CLEAN, blind sheet carried no verdict
- **Zero overlap** with attempt 1
- Dossiers gathered, **20/20 complete**: 416 window commits with full file lists, 149 issues
- `human_labels.csv` stayed blank — **no labels were ever recorded**

An **agent reference set** was produced and stored separately (BROKE 3, CLEAN 15, UNSURE 2),
explicitly marked `REFERENCE SET ONLY -- NOT THE GATE`.

**Withdrawn because the sealed key's confidentiality could no longer be demonstrated.** The
commit timestamp exists so blindness is *provable* rather than asserted; an assurance that
nobody looked is exactly the kind of claim this project has learned not to accept. Discarded
on the possibility, not on a confirmed exposure.

---

## 4. Attempt 3 — seed 20260811. Withdrawn: a new seed is not a new sample

Filled 10/10 from `agent_rewalk3_records.jsonl`. Then the overlap check:

```
overlap with seed 20260810 (withdrawn): 8 of 20
overlap with seed 20260809 (invalid):   1 of 20
```

**Nine of twenty PRs repeated.** A fresh seed reshuffles a small pool; it does not refresh
it. Across three draws, **51 distinct PRs** had been drawn from 118 admitted records.

---

## 5. Attempt 4 — seed 20260812. Could not be drawn

Drawn from a filtered records file with all 51 previously-drawn PRs removed, leaving 86.

```
ValueError: only 9 BROKE PRs found in 39 examined across 389 repositories, need 10.
```

### 5.1 Cause one — a cap mismatch nobody noticed

Two limits, set independently, for different reasons, constraining the same resource:

- the walk admits up to **`--per-repo 7`**
- the draw considers at most **`MAX_PER_REPO = 3`**

| | |
| --- | --- |
| unseen records | 86 |
| repositories holding them | 31 |
| reachable at cap 3 | **67** |
| **structurally undrawable** | **19** |

Those 19 exist, are admitted, count toward every corpus figure, and **no draw can ever
select them.** The admitted-record count overstates the drawable pool by **22%**.

### 5.2 Cause two — a depletion ratchet

A stratified 10/10 draw removes BROKE *faster than the pool contains it*, so each attempt
leaves a CLEAN-richer residue:

| set | scanned | broke | rate |
| --- | --- | --- | --- |
| previously drawn | 32 | 15 | **46.88%** |
| unseen remainder | 84 | 28 | **33.33%** |
| whole corpus | 116 | 43 | 37.07% |

Fisher p = 0.201 at n=32 — not significant, and **mechanically expected rather than
accidental**. `P(≤9 BROKE in 39 | 0.3707) = 0.0468` rules out sampling noise as the sole
cause.

**Draw feasibility degrades monotonically with attempts, independently of pool size.** The
two causes compound: the reachable subset is also the depleted one.

### 5.3 The raise message was itself an instance of the class

It read:

> *"a base rate this far from expectation is a finding about the outcome rule, not a
> sampling inconvenience"*

**TRUE on a first draw. FALSE on a fourth**, where the cause is depletion by design. One
message, two opposite meanings, pointing a future reader at the classifier when nothing is
wrong with it — the failure pattern this project spent the week removing, sitting inside the
warning written to prevent it.

`draw.py` now states both causes, how to tell them apart, and names the remedy.

---

## 6. Where the four attempts went

| attempt | seed | outcome | cause |
| --- | --- | --- | --- |
| 1 | 20260809 | scored 16/20, **invalid** | gatherer swallowed 404s; gate rebuilt the classifier's input |
| 2 | 20260810 | **withdrawn** | key confidentiality not demonstrable |
| 3 | 20260811 | **withdrawn** | 9 of 20 PRs repeated |
| 4 | 20260812 | **could not draw** | pool depleted + 22% undrawable |

**Only one valid draw was ever needed.** Three were spent on defects — each caught a real
problem, and none was waste — but nobody knew draws were a limited resource until they ran
out.

---

## 7. The related finding: an inert constant

Grepping for other mismatched caps found a second instance, one step worse.

`POSITIVE_CONTROL_N = 30` is declared in `controls/analysis.py`, exported through
`controls/__init__.py`, and **read by nothing but a test asserting it equals 30**. The
controls gate runs at `DEFAULT_PER_MECHANISM = 40`, so **A30's RR 8.0 was measured at 40,
not at the pre-registered 30.**

In the cap mismatch both limits did something and one starved the other. Here **one is live
and the other is decorative — and the test makes it look enforced.**
`assert POSITIVE_CONTROL_N == 30` returns the same value whether the gate builds 30, 40 or
400 units.

**40 is not wrong** — more units is a stronger control, and the gate passed at 40/40
detection with RR 8.0. But the preregistration says 30, the code says 40, and nothing
reconciled them. Recorded as A44 rather than silently amended: what the gate actually ran is
the number belonging in Results.

Ruled out with reasons: the retry pair (`MAX_RETRIES × RETRY_AFTER_CAP_S` = 75 min worst
case) has no enclosing budget to starve; `GIT_TIMEOUT_S` at 30/60/120/30 across four modules
is an inconsistency smell, not a starving pair.

---

## 8. Current state

**In progress:** a 200-repository agent walk (`agent_walk2.*`), re-walking the original 72
plus 128 new. New repositories arrive at the corpus rate (~37% BROKE), undepleted.

**Quarantined out of the repository** (scratchpad, not `data/labelling/`): seed 20260810's
key, sample, dossiers and agent reference set; seed 20260811's key, sample and template.

**Preserved in `results/`:** attempt 1's labels and score under the
`handlabel_gate.INVALID.` prefix, with a README pinning each artifact to its draw.

**Amendments:** A43 (drawable pool, cap mismatch, depletion ratchet), A44 (inert constant).

---

## 9. What a valid attempt requires

1. **A larger pool.** Walking more repositories — not re-seeding, which reshuffles the same
   pool, and not raising `MAX_PER_REPO`, which defeats the cap that stops one repository
   supplying the sample.
2. **A fresh seed, resealed**, with overlap verified against **all** prior draws.
3. **Dossiers regathered.** The gatherer works: 20/20 complete, every fetch recorded as
   success or explicit failure, `window_commit_count: 0` distinguished from `null`.
4. **A human labeller**, per the runbook and `HAND_LABELLING_PROTOCOL.md`. A machine dry run
   of this gate scored 11/20, kappa 0.10.
5. **Labels committed before the key is opened.** The timestamp is the proof.

---

## 10. What this cost, and what it bought

Four attempts, no gate. But the attempts surfaced defects that would otherwise have run
through 4,300 PRs unnoticed:

- the outcome walk's commit-count cap silencing 31.4% of one arm
- `derived_files` recording 0 for "never measured"
- `verify_files` substituting the corpus for GitHub as authority
- the gate certifying a rebuilt classifier
- `parent_commit` attrition that was entirely rewritten history
- a drawable pool 22% smaller than the record count

**The instrument is in better shape than when the gate was first attempted.** What remains
is a corpus large enough to draw from, and two hours of human reading.
