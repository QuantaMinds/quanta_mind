# Design 13 — what the two Qodo mechanisms did, measured

Pre-registered in `docs/plans/preregistrations/reviewer/expansion-conventions-preregistration.md` before any
model call. Six repositories verified unused, 90 merged pull requests, 80 reviewable, three arms.

## The bars, as they came out

| | bar | result | |
|---|---|---|---|
| **H4** yield | ≥ 0.30 findings/PR | A 0.41, B 0.40, C 0.46 | **PASS** |
| **H1** TRACE+ABSENT share of wrong falls A→B | ≥ 15 points | 73.3% → 18.8%, **−54.6 points** | **PASS** |
| **H2** arm B wrong-rate | ≤ 30%, interval rule | **59.3%** [40.7, 75.5] | **FAIL** |
| **H3** arm C not worse than B | ≤ +10 points | **−12.6 points** | **PASS** |

Sabotaged controls: **10 of 10 caught.** Arm labels were held in a key the rater did not open.

## Expansion did exactly the one thing it was built to do, and it was not enough

Arm A's wrong findings were 73.3% TRACE or ABSENT — the model failing to follow code that was
shown to it. **Arm B's are 18.8%.** Feeding the model the enclosing function removed the class of
error it was supposed to remove, and the mechanism is visible in individual findings: two claims of
an infinite loop in `falcon/cyutil/uri.pyx` died because the `for pos in range(...)` header that
refutes them sits ten lines above the hunk.

**And the headline did not move** — 51.7% → 59.3%, intervals almost entirely overlapping. A
different failure class had already taken over.

## The mechanism: 23 of 24 wrong CI-config findings are unanswerable by construction

Cross-tabulating cause against the kind of file the finding is about separates it completely.

| file kind | n | wrong | rate | correct | causes |
|---|---|---|---|---|---|
| **CI config** (`.github/`, `*.yml`) | 36 | 24 | **66.7%** [50.3, 79.8] | 4 | **EXTERNAL 23**, TRACE 1 |
| tests | 20 | 10 | 50.0% | 1 | TRACE 8, EXTERNAL 2 |
| source code | 29 | 11 | 37.9% | 2 | TRACE 8, EXTERNAL 3 |

Every one of those EXTERNAL claims is the same shape: *this commit hash does not exist*, *this tag
was never released*, *this date is in the future*. **Every single one checked against GitHub was
false.** `actions/setup-python@5fda3b95` exists and is tagged exactly `v7.0.0`; `actions/checkout`
`v7.0.1`, `astral-sh/setup-uv` `v9.0.0`, `pre-commit/mirrors-mypy` `v2.3.0`,
`astral-sh/ruff-pre-commit` `v0.15.21` and `PyCQA/isort` `9.0.0b2` all exist;
`hynek/build-and-inspect-python-package` was never renamed and still ships `v3.0.1`; and the "future"
dates read Aug 14–17 2026 against a run on Aug 18 2026.

**A diff cannot settle any of them, and the reviewer is diff-scoped.** That is not a tuning
problem. It is the decidability principle the project already holds, applied to a file kind the
path filter still admits.

## Off CI config, both mechanisms help, monotonically

| arm | off-CI wrong-rate | 95% Wilson |
|---|---|---|
| A — design nine | 12/23 = 52.2% | [33.0, 70.8] |
| B — plus expansion | 5/13 = 38.5% | [17.7, 64.5] |
| C — plus conventions | 4/14 = **28.6%** | [11.7, 54.6] |

**This is a post-hoc subgroup and is not a passed bar.** It was not pre-registered, the intervals
are enormous, and a rule read off the data it is scored on has no error rate. It is a hypothesis for
the next pre-registration, nothing more.

## The conventions file did not do the harm it was expected to do

H3 existed because a rules file is mostly style and the reviewer is already a third wrong. It went
the other way: arm C is **12.6 points better** than B, with more UNFALSIFIABLE and fewer WRONG.
Selecting the file needed two fixes made before any model call — three of the first six repositories
shipped a 62–98 character POINTER rather than rules, and `tornadoweb/tornado` was in the corpus by
eye and turned out already burned in the aged corpus.

## Half A had almost nothing to rank

Of 43 pull requests with resolvable history, **35 touch three or fewer Python files** — where top
three is every file and the ranking decides nothing. Eight reached the informative stratum. This
reproduces the effort-test result: the ranker is **large-PR triage**, and this corpus is not that.

## What this does not license

- **The rater designed the experiment.** Arm labels were blind and all ten planted controls were
  caught, but designer bias is unguarded. **None of this counts toward the replication standard**,
  which needs a rater who did not design the run.
- **The corpus was too small and it was said so first.** At ~30 findings per arm the interval
  half-width is ~17 points. H2's failure is not evidence expansion hurts.
- `infer/` stays closed. Nothing here is near the bar that would open it.
