# Handoff — `fix/darwin-memory-cap`, 2026-08-05

Companion to the auto-generated `session-fix-darwin-memory-cap.md`. That one lists what
changed; this one says what it means and what to do next.

**Machine:** darwin arm64 — a new platform for this project; prior work ran on win32.

The single most important line: **the exposure pass has not run successfully, and the
corpus is final.**

---

## Start here

**The open question is the `arm` field.** `results/exposure.VOID.jsonl` holds 8 records,
every one `arm: "human"`, every one REJECTED at `clone_failed` in the journal, zero
admitted units. The pass processed the inverse of the intended population.

`pilot/run.py` draws its population from `eligible_prs(PACKAGE)` where
`PACKAGE = data/AIDev_BC_Analyser.zip` — the figshare **human-PR** replication package.
Whether the 139-admitted journal is therefore also human-arm is the first thing to
establish, because if it is, the consequence runs back further than the exposure pass.

Three faults stacked in that output:

1. Records rebuilt from rows marked `clone_failed`, not from admitted rows.
2. All tagged `arm: human` against what should be an agent corpus.
3. `parent_resolution_method: "squash"` with `parent_sha: ""` on 8 of 8 — a shape
   returned without a commit, and nothing objected.

This is **not** size-selection. The arm split ruled that out, so it is not another door
onto the confounder — it is a population-selection defect, which is fixable.

---

## The lesson this session keeps re-teaching

Three defects today, one shape: **a stage produced an empty result and a downstream stage
read it as a finding.**

- `RLIMIT_AS` — PyCG never launched, recorded as `CRASHED`, a claim about the repository.
- blobless clones — a diff over blobs that never arrived is empty, recorded as
  `no_python`, again a claim about the repository.
- the void exposure pass — no parent resolved, recorded as `"no analysable Python at the
  parent"`. It should read `"parent unresolved — scope not attempted"`.

**When the harness fails, the label must say so.** Every fix today has that form.

A fourth, and a new class, found in my own code: **a predicate copied between call sites
carries its semantics with it.** `len(api_files) < API_FILE_PAGE` means *"distrust this
list"* in `verify_files`, and I reused it to mean *"skip the check"*. Both uses are
individually correct; the defect exists only in the relationship, which no test of either
function can see.

Both belong in `AGENTS.md` beside the "ask what a check outputs when the thing it checks
is broken" rule. **Not yet added** — that file sits at exactly 200 of its 200-line budget,
so a line must be freed first.

---

## The bug that mattered most

`RLIMIT_AS` cannot be lowered on darwin under an unlimited hard limit — soft-only
included. The `ValueError` fired inside `preexec_fn`, so PyCG never started and `run()`
recorded `GraphStatus.CRASHED`. **100% of invocations.** A corpus run would have finished,
produced a table, and reported total attrition as a result about the corpus when it was a
fact about the operating system.

What actually established it, in order:

1. Failing test: `assert 0 == 2` in the controls corpus test.
2. Isolation: `SubprocessError: Exception occurred in preexec_fn`.
3. Mechanism, independently: `setrlimit(RLIMIT_AS, (16GB, 16GB))` →
   `ValueError: current limit exceeds maximum limit`; soft-only also fails;
   same-as-current succeeds.
4. **Prediction before writing the fix** — monkeypatched the limiter to `None`, the gate
   returned `super_chain (2,2)`. The diagnosis predicted the result before code changed.
5. After: 260 green; controls gate `RR 8.0`, 80/80 units, `super_chain` 40/40.

---

## Blobless cloning: adopted, then abandoned

Adopted to close a size-selection door — nine repos exceeded the clone timeout and they
were the largest. It opened a worse one on the same eight repositories.

First live use: 12 rejections at `derived=0` — three labelled `no_python` where GitHub
lists 104, 65 and 40 `.py` files — and **17 of 17 scored PRs CLEAN**, p = 0.0049.
Decisively, `bruin-data/ingestr#2532214135`, which the probe had scored **BROKE**, derived
zero symbols.

A stop rule was committed **before** the re-run: if that known-answer PR does not come
back BROKE, abandon rather than patch. It came back `no_symbols`, `derived=0`.
**Abandoned.**

The contents assertion never fired, because `api_files` truncates at
`API_FILE_PAGE = 100` and the guard skipped exactly the largest PRs — the predicate defect
described above.

**Consequence, as pre-registered:** the eight stay excluded, the clone-timeout bound is
retained, the 21-plus commit band stays unresolved. A worse corpus and a defensible one.

---

## Facts established, so they are not re-derived

- Corpus facts reproduce **exactly** from a fresh HuggingFace download: Codex 21,799
  (64.89%), Copilot 4,970, Devin 4,827, Cursor 1,541, Claude_Code 459 (1.37%); stars
  min 101 / median 564 / max 203,424, n=2,807.
- The published PR-level breaking-change figure of **11.3%** is real — `293 out of 2592`
  from the replication package's own notebook. Human arm is `136 out of 642` = 21.18%.
  File-level agent rate is 3.45% (805/23,333); Codex 2.62% reproduces exactly.
- The 26.87% outcome-rate residual is **benign**: zero verdict flips across overlapping
  PRs, identical rate (18.52%) on the 27 scored in both journals. Composition, not churn.
  The 27.3% figure came from a 48-record pilot and is not comparable.
- **The 300-file diff limit cannot be hit.** The only `Accept` header sent is
  `application/vnd.github+json`; nothing requests the diff media type. Thread closed.
- Truncation at 100 files does **not** bite the current corpus: 0 admitted PRs have
  `derived >= 100`. The three with `corpus_py` of 137/234/213 have real diffs of 8/11/3 —
  that gap is the documented over-attribution. **It would bite a future corpus with
  genuinely large diffs**, and belongs in the over-attribution amendment as a stated
  limit. **Not yet written.**

---

## Environment, already done

`uv` 0.12.1 and `just` 1.58.0 via brew, at the exact pins. Both venvs synced — product on
3.12, harness on its own 3.10.20. Pre-commit installed. `colima` and `docker` installed;
colima started but **never used** — the work stayed on macOS.

- AIDev tables live at `research/phase0/data/aidev/`, where `pilot/run.py` expects them —
  not at `data/`.
- Replication package at `research/phase0/data/AIDev_BC_Analyser.zip`, md5
  `7fc01c70cb4ed0210fab098d820de743`, 78,419,081 bytes — verified.
- **`GITHUB_TOKEN` lives in `research/phase0/.env` and NOTHING LOADS IT.** `require_token`
  reads `os.environ` directly; there is no dotenv dependency. Every run must be prefixed
  with `set -a && . ./.env && set +a`. The token is a fine-grained PAT and authenticates.

---

## Files that matter

| Path | State |
|---|---|
| `results/rate_journal_v2.md` | **CANONICAL — untouched.** 90 repo-done, 139 admitted |
| `results/rate_journal_v2.pre_A29.bak` | backup taken before the first re-scan |
| `results/rate_journal_v2.rescan_suspect.md` | first re-scan, contaminated |
| `results/rate_journal_v2.rerun.md` | second re-scan, also failed |
| `results/rescan_eight_rows.quarantined.md` | the 31 suspect rows |
| `results/exposure.VOID.jsonl` and its README | **VOID — do not analyse** |
| `results/controls.json` | valid, passing on darwin |

Both re-scans went to copies. **The canonical journal was never contaminated.**

---

## Outstanding, in priority order

1. **The `arm` question** — start here.
2. **The empty-parent invariant** — a resolver returning a method with no SHA must raise.
3. **Error strings that blame the repository** for harness failures — fix the class.
4. **OOM enforcement test** — the memory cap is proven *accepted*, never proven to *fire*.
   Drive a child past a small cap, assert it dies and the harness records OOM. Before the
   full run.
5. **`AGENTS.md`** — the two rules above; needs a line freed.
6. **The over-attribution amendment** — add the >100-file verification-fallback limit.
7. **`docs/CODEBASE.md` was not updated** this session; the session-end hook flags it.
8. Then: exposure pass, the draw, 20 hand labels (human, ~2h, cannot be redone), full run.

**Two paths the signed amendment explicitly does not cover:** Linux equivalence is
inferred from reading code and never observed — run the controls gate on any new platform
before the corpus runs there, and it must reproduce `RR 8.0 / 80-of-80 /
super_chain 40-of-40`. And the memory cap is proven accepted, not proven to fire.

---

## Standing instruction

Nothing here is finished because it is green. Thirteen defects were found this session and
every one produced a **plausible, complete-looking, wrong** result rather than an error.
Ask what each check outputs when the thing it checks is broken. If the answer is "the same
thing", it is not a check.
