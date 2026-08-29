# Why the oracles never fire — investigation, 2026-08-28

**Prompted by:** across 65 changes over two measured runs, the verification gate dropped 5+3
findings for a missing anchor and **exactly one** for anything else. A gate described as three
stages had demonstrated one.

**Answer, in one line:** the two halves of the oracle machinery are unreachable for two different
reasons — one deliberate and documented, one a wiring defect that a docstring already claims was
fixed — and the single non-anchor drop in A6 was almost certainly not an oracle working.

---

## "The oracles" are two different mechanisms, and conflating them hid this

| | what it does | model involved | reached in production |
|---|---|---|---|
| **`verify/external_facts.adjudicate`** + `verify/releases.adjudicate_release` | REFUTES a model's claim about a SHA or a package release | yes — it deletes model output | **no**, by design |
| **`verify/pin_mismatch.detect`** | PRODUCES its own finding: a pin whose `# vX.Y.Z` comment disagrees with GitHub | no — parser plus two API calls | **no**, by defect |

Both are invoked. Neither can act. The counters report them together, so "refuted 0" reads as
"the oracles looked and found nothing" when the truth is "nothing was ever put in front of them".

---

## Finding A — the refutation oracles are structurally unreachable, and that is intended

`publishable.gate()` runs both refutation oracles on every finding. Over **all 38** harvested
findings, every one took the `no-oracle-applies` branch and **zero** were dropped:

```
38  publishes=True  oracle=no-oracle-applies
```

The reason is upstream. Every trigger the oracles need was false on every finding:

| trigger | true in |
|---|---|
| a SHA-shaped token in the claim | 0 of 38 |
| a `owner/repo` token in the claim | 0 of 38 |
| "does not exist" phrasing | 0 of 38 |
| asserts a tag (`is v4.1.1`) | 0 of 38 |
| disputes a package release | 0 of 38 |
| the diff pins anything at all | 0 of 38 |

**Six clean zeros, so the instrument was tested before the result was believed.** Given text
designed to trigger each — `"The commit 4f2c1ab9de is not on main"`, `"Version 1.45.34 of awscli
does not exist"`, a real `uses: actions/checkout@8f4b7f84…` line — **every trigger fired.** The
zeros are a property of the findings, not a dead detector.

**The mechanism is `REVIEWABLE_SUFFIXES`.** It contains `.py .pyi .js .ts .tsx .jsx .go .java .cc
.cpp .hpp .mjs .cjs` — and no `.yml`, `.yaml`, `.toml`, `.txt` or `.lock`. Pins live only in the
files it excludes. All three entry paths filter on it before ranking: `ingest/diff.py:88`
(webhook), `serve/run_commit.py:74` (uncommitted work), `serve/run_commit.py:126` (a named
commit). Demonstrated on `3709c4a9`, a real commit touching `.pre-commit-config.yaml` and two
Python files:

```
files the COMMIT touched : ['src/flask/app.py', 'src/flask/sessions.py']   <- yaml already gone
'.pre-commit-config.yaml' in the diff the model and gate() see? False
```

So the model is never shown a file that could contain a pin, and therefore cannot make a claim
about one, and therefore the oracle that refutes such claims can never speak. **`serve/pin_check.py`
already says this in its own docstring and calls it a product decision, not a mistake:** showing
the reviewer workflow files would widen what it reads, and the cost argument is that it reads only
ranked files. **Finding A is working as designed. It should be reported as scope, not as a gate.**

---

## Finding B — the pin detector is unreachable by defect, and a docstring says otherwise

`serve/pin_check.py` was written *because* of Finding A. Its docstring:

> **THE DETECTOR WAS BUILT, MEASURED 24/24, AND WIRED SOMEWHERE IT COULD NEVER FIRE.** […] it
> belongs on the RAW changed-file list, beside the ranking rather than inside it.

The rewiring was done. **It was given the filtered list anyway.**

- `serve/review_delivery.py:87` — `changed = changed_files(delivery_repo, number)`
- `ingest/diff.py:88` — `changed_files(repo, number, suffixes=REVIEWABLE_SUFFIXES)` — the default
- `serve/review_delivery.py:150` — `pin_check.check(clone, head_sha, changed)` — that same list

Known-answer test on the real function:

```
workflows(RAW)      -> ['.github/workflows/tests.yaml', '.github/workflows/lock.yaml']
workflows(FILTERED) -> []          <- the detector's actual input at line 150
```

`check()` returns `([], 0)` at its `if not paths` guard before reading git or calling GitHub. **For
every pull request on every repository**, the detector exits before doing anything. `flask`'s
workflows are SHA-pinned with version comments — `actions/checkout@de0fac2e… # v6.0.2` — so there
is real material here and the detector would read it if handed the path.

**Two further consumers named and absent.** `pin_check.py` says `CONSUMED BY: serve/review_delivery.py,
serve/run_commit.py`. `run_commit.py` does not import or call it, so the CLI path has no pin
detection at all — a docstring naming a consumer that does not exist.

### Why every test passes anyway

`tests/live/test_oracles_name_their_artefact.py` names the artefact each oracle must find, as
rule 14 requires — `test_detect_names_the_tag_it_disagrees_with` passes a synthetic diff string
straight to `detect()`. **Every oracle test calls the unit directly.** None goes through
`changed_files` → `check`, so no test exercises the wiring, and the wiring is the broken part.
This is the defect class AGENTS.md already names: *an unreachable check reads exactly like a
passing one.*

---

## Finding C — A6's single "refuted 1" was probably not an oracle working

If the oracles cannot reach an external claim, how did A6 record one non-anchor drop? There is a
path, and it is not the intended one. `adjudicate()` extracts any 7–40 character hex token; if it
finds one and no `owner/repo`, it returns `UNRESOLVABLE`, and `gate()` **drops the finding**:

```
"The cache key deadbeef1 is reused across runs"     -> publishes=False, sha-oracle, unresolvable
"The default ffffff00 is applied before the theme"  -> publishes=False, sha-oracle, unresolvable
"The `size` parameter is ignored when the list is"  -> publishes=True,  no-oracle-applies
```

A cache key, a colour constant or a hash literal is enough. **The only drop the gate can perform
in practice is losing a finding for containing hex-shaped text**, which is a false drop rather
than a refutation. A6's findings were not retained, so this cannot be confirmed for that specific
case — stated as the mechanism, not as the verdict.

---

## What this changes about the numbers already published

**"Gate rejection 14.3%" and "18.5%" are the anchor check alone.** That is what A6 said —
*"almost entirely the parser confirming a quote exists in the diff"* — and this investigation
raises it from *almost* to *entirely*, with the mechanism named.

**No published claim needs retracting.** The rates are correct; what changes is what may be
inferred from them. Specifically: *published* correctness cannot currently be better than *raw*
correctness by any oracle-driven margin, because no oracle removes anything. The anchor check is
the whole difference. That makes the unlabelled pack in `research/phase0/data/labelling/` more
load-bearing, not less.

---

## What to do, and what each costs

**1. Give the detector the list it was supposed to get.** One argument: pass the unfiltered
changed-file list to `pin_check.check()`, and let `workflows()` do the selecting it already does.
`changed_files` needs an unfiltered call, not a changed default — the filter is correct for
ranking. Small, mechanical, and it makes a measured-24/24 detector reachable. **Its base rate is
0.24%** — 3 genuine mismatches in 1,244 real pins — so expect it to fire rarely and be right.

**2. Add a wiring test, not another unit test.** Every existing oracle test would still pass with
the wiring broken. The test that matters starts from a changed-file list containing a workflow and
asserts a mismatch reaches the rendered comment.

**3. Stop the hex-token false drop.** Requiring a repository *before* extracting SHAs would make
`UNRESOLVABLE` unreachable from a semantic claim. Today the gate's only live behaviour is
discarding findings that mention a hex string.

**4. Report the two mechanisms separately.** `refuted` currently sums a stage that cannot act and
a stage that is not wired. Counting them apart would have surfaced this in A6 rather than 65
changes later.

**Not recommended: showing the reviewer workflow files.** That reopens Finding A, widens what the
model reads, and contradicts the cost argument. `pin_check.py` already reasoned this through and
its conclusion holds.
