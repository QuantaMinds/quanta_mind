# The co-change signal discriminates but does not localise

**Measured 2026-08-12** against live clones of ten repositories, pulled from GitHub during
this run. This is the fifth negative result in this repository, and the first one that kills
a product claim rather than a risk claim.

---

## What was tested

A session plan on the `feat/history-signal` branch, since removed with the other auto-written session records, proposed a signal no shipping reviewer emits:

> Historically, when this function changed, that other file changed with it. This pull
> request changes the first and not the second. **Here is the companion change you are
> missing.**

The product claim has two halves. The signal must **fire more often on changes that later
broke** — and, when it fires, it must **name the file the fix will actually touch**. The
second half is the product. The first half alone is a risk score, and this repository has
already established twice that a risk score without an action is worth nothing.

---

## Result

**Population.** 41 analysable pull requests across the 10 repositories in the agent corpus
that contain at least one symbol-level breakage: 16 broke under the corrected rule, 25 did
not. Labels from `research/phase0/results/a54_confound.json`.

**Signal.** File-level co-change mined from history reachable from each pull request's
`parent_sha`. Fires when a changed file has a historical partner — co-changed in at least 3
commits, in at least 60% of that file's commits — absent from the diff. Thresholds fixed
before any result was inspected.

### Half one — it discriminates

```
                 fires    silent
BROKE               8         8      50.0%
clean               2        23       8.0%

Fisher exact two-sided p = 0.0066
```

Matched to repositories containing **both** arms, which removes two repositories that could
only contribute to the numerator: **5 of 11 = 45.5%** against **2 of 25 = 8.0%**.

For comparison on a different corpus, an AI reviewer flagged 10 of 65 genuine breakages at a
23.9% rate on clean pull requests. This signal fires **more often on what broke and less
often on what did not**, which is the shape the product needed.

### Half two — it does not localise, and this is fatal

For each of the 8 pull requests where the signal fired on a genuine breakage, the actual
fix commit was retrieved and its file list compared against **every** file the signal
predicted was missing.

```
Pointed at a file the fix actually touched:   0 of 8
```

Not a low rate. **Zero.** Three of the eight had no retrievable file list on the evidence
commit, so five are strictly checkable and all five missed. Concretely:

| Pull request | Signal predicted missing | The fix actually touched |
|---|---|---|
| Gemini-FastAPI 3166124377 | `app/models/models.py`, `app/server/middleware.py` | `app/server/chat.py`, `app/services/lmdb.py`, `pyproject.toml` |
| Skyvern 3085074194 | `skyvern/forge/sdk/routes/agent_protocol.py` | `skyvern/forge/agent.py`, `.../workflow/service.py`, `.../task_v2_service.py` |
| airbyte 2814487611 | `.../config.py`, `.../destination.py`, `.../setup.py` | `.../check_python.py`, `.../indexer.py`, two integration tests |

**The comment the product was going to post would have been wrong every time it appeared.**

---

## What this means

The mechanism detects that a change is *the kind that breaks*. It does not know *what is
missing*. Those are different products, and only the second one was worth building:

- **"This change looks risky"** — a warning. Six static-analysis surveys rank *"misses too
  many issues"* fourteenth of fifteen pain points; as a warning this is noise, and it is the
  same shape as the coverage gate that fired on 45% of pull requests and discriminated on
  none of them.
- **"You forgot `ledger.py`"** — an action, and the reason a developer would tolerate a third
  bot on their pull requests. **This is the half that failed.**

**The discrimination is real and it is not the product.** Anyone reading only the 2×2 would
ship this.

---

## Why it did not localise — the premise was wrong

The obvious diagnosis is that co-change is the wrong ranking function and a better one would
localise. That diagnosis is refuted by the data.

For each genuine breakage, the fix commit's files were split into those the pull request had
**already changed** and those it had not:

| Class | Meaning | Count |
|---|---|---|
| **SELF** | the fix only re-touched files the pull request already changed | **5 of 11** |
| **MIXED** | the fix re-touched changed files **and** added new ones | **6 of 11** |
| **COMPANION** | the fix only touched files the pull request did not | **0 of 11** |

**Every single breakage required re-editing a file the pull request had already changed.
Not one was fixed by adding the missing file alone.**

These are not incomplete changes. **They are wrong changes.** The product was designed
against a failure mode that this corpus does not contain, which is why a better ranking
function cannot rescue it — the thing being ranked is not the thing that broke.

---

## Verification performed, because a green number is not a verified number

- **No-lookahead, asserted not claimed.** For all 41 pull requests,
  `git merge-base --is-ancestor merged_sha parent_sha` was run. **Zero leaks.** History is
  strictly ancestral to the change.
- **Sabotage.** Rebuilding history from `merged_sha` instead of `parent_sha` moved the catch
  rate from 50.0% to 37.5%, so the boundary is load-bearing rather than decorative. This is a
  weak sabotage — it does not prove the harness would catch a signal built from the fix
  commits themselves — and a stronger one is still owed.
- **A first run was discarded.** It analysed 34 pull requests against the sabotage run's 39,
  because three repositories finished cloning between the two. Both were re-run on the
  identical set of 41. **The discarded run's numbers were not used.**
- **Truncation caught and corrected.** The first localisation check compared only the top 3
  predictions per pull request. Re-run against **all** predictions: still 0 of 8.

---

## The known-answer test, which is what makes the zero meaningful

A zero can mean the signal found nothing or that the instrument is dead. Only a known-answer
test separates them, so the **same signal and the same code path** were run on **ordinary**
commits: hold out one file from a real multi-file commit, mine history strictly before it,
and ask whether co-change names the held-out file.

| Population | Signal fired | Named the right file |
|---|---|---|
| Ordinary commits, 148 across 6 repositories | 52 | **22 of 52 — 42.3%** |
| Defect-fix commits, this study | 8 | **0 of 8 — 0.0%** |

```
Fisher exact two-sided p = 0.0218
```

**The instrument works.** 42% precision when it fires is consistent with the published range
for co-change recommendation. The zero on defect fixes is therefore a property of
defect-inducing changes, not a broken harness.

---

## A third signal, also null

If localisation is impossible, the fallback is a hotspot warning: fire when a changed file
has recent fix-commit history. Preregistered threshold: at least 2 fix-labelled commits
touching a changed file in the 180 days before the pull request.

| Threshold | Catch | Fires on clean | RR | p |
|---|---|---|---|---|
| ≥1 | 12 of 16 — 75.0% | 12 of 25 — 48.0% | 1.56 | 0.113 |
| **≥2 (preregistered)** | 9 of 16 — 56.2% | 9 of 25 — 36.0% | **1.56** | **0.334** |
| ≥3 | 8 of 16 — 50.0% | 8 of 25 — 32.0% | 1.56 | 0.330 |

Null, and it fires on a third of clean pull requests — the coverage gate's failure mode
exactly.

**The first run of this check returned zero at every threshold**, which is the signature
`AGENTS.md` describes: a check that outputs the same thing whether or not the thing it checks
exists. The cause was a window expressed relative to today rather than to the pull request,
so no commit could satisfy both it and the ancestry bound. A sanity counter now reports
in-window commits found — **0 before the fix, 1,298 after** — and it is printed every run.

---

## Where this leaves a model-free pre-merge product

Three signals have now been tested against breakage in this repository, and the pattern is
consistent with what the corpus is made of:

| Signal | Discriminates? | Actionable? |
|---|---|---|
| Call-site coverage | **No** — RR 0.916 | — |
| Co-change companion | **Yes** — p = 0.0066 | **No** — 0 of 8 localised |
| Fix-history hotspot | **No** — RR 1.56, p = 0.33 | — |

Published work on model-generated code reports that **semantic errors account for over 60% of
faults** and that AI-assisted generation produces roughly **1.7× more logic and correctness
bugs**. That is the same conclusion the 11-of-11 self-fix result reaches from this corpus:
**the defects are wrong logic, not missing structure.**

Deciding whether logic is correct requires reading the logic. A parser cannot do it, and a
model-free pre-merge product therefore has no signal to stand on. **This is a constraint made
explicit, not a failure to find the right heuristic.**

---

## Limits, which do not rescue it

- **n = 16 breakages.** Small. Two repositories supply 6 of the 8 catches.
- **Mild size confound.** Firing pull requests changed a median of 3 files against 2 for
  silent ones, and larger changes break more often.
- **9 of the 25 clean pull requests are file-rule BROKE** but symbol-clean, so the clean arm
  contains near-misses.
- **This is file granularity, not symbol.** The plan claimed symbol-level as the
  differentiator and this run did not test it. It is the one remaining path, and it is a
  weaker hope than it looks: the signal did not miss by a little, it pointed at unrelated
  parts of the codebase.

---

## What is withdrawn and what stands

**Withdrawn.** *"We'll flag the incomplete changes neither of them can see."* The measurement
that was supposed to support that sentence refutes it. It must not appear in a pitch, a page,
or a conversation until a localisation number exists and is positive.

**Stands.** The corrected attribution rule, reproduced three times — 32.1% survival on the
original corpus, 36.1% and 35.7% on two later ones. That is independent of this result,
because it concerns how breakage is attributed, not how it is predicted.

The audit half of the position — *"you are spending this much and cannot measure what it
catches"* — rests entirely on the attribution rule and is untouched by this run.

Elapsed from writing the plan to falsifying it: **under two hours.**
