# What started working, what did not, and how we know — issue #87

**Companion to `WHY_THE_ORACLES_NEVER_FIRE_2026-08.md`, which diagnosed it. Fixes in `6f02ad1`.**

---

## The short answer

**The detector half works now and is proven working. The refutation half still cannot fire, by
design. And the re-measurement proves neither of those things** — a point worth making first,
because the obvious way to read the numbers below is wrong.

| | before | after | how we know |
|---|---|---|---|
| pin detector reaches a workflow | never | **yes** | live API test, a real wrong pin found |
| refutation oracles reach a claim | never | **still never** | Finding A, unchanged and intended |
| a hex token drops a finding | yes | **no** | targeted cases, both directions |
| `refuted` and `unresolvable` distinguishable | no | **yes** | conservation over five fates |

---

## How the detector started working

**The cause was one argument.** `serve/pin_check.py` was written specifically because the model
never sees a workflow, and its docstring says the detector "belongs on the RAW changed-file list".
It was given the filtered one: `review_delivery.py` called `changed_files()` with the default
`suffixes=REVIEWABLE_SUFFIXES`, which holds no `.yml`, and passed that result straight on. So
`workflows(changed)` was `[]` and `check()` returned at its guard **before reading git or calling
GitHub, on every pull request on every repository, since the day it was wired.**

**The fix is that `changed_files` can now be asked for everything** — `suffixes=None`, and
deliberately not `()`, because `"a.py".endswith(())` is `False`, so an empty tuple filters
everything out while reading like the opposite. The delivery path fetches once unfiltered, filters
locally for ranking, and hands the unfiltered list to the detector. No extra API call; the ranker's
input is byte-identical to before.

**Proven against the live API, not by unit test.** A repository pinning
`actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd` — a real commit — commented `# v3.0.0`,
where GitHub reports it as `v6.0.2`:

```
filtered list   -> workflows([...]) == []          mismatches=0    <- production, always
unfiltered list -> workflows([...]) == ['.github/workflows/ci.yml']
                   Mismatch(repo='actions/checkout', commented='v3.0.0', actual=('v6.0.2',))
```

**And it stays silent when the comment is right.** The same SHA commented `# v6.0.2` produces
nothing. That is the check that matters: a detector which fires on everything would be worse than
one that fires on nothing, because the silence at least cost no one any attention.

**A fifth defect surfaced while fixing.** `workflows()` tested `"workflow" in path`, so
`docs/not_a_workflow.yaml` qualified. That was harmless only while the detector could never act;
the moment it could, a documentation page showing an example `uses: owner/action@sha # v1.0.0`
would have been reported as a real mismatch in a real workflow — a false finding with an API call
behind it, which is the worst kind this project has. It now requires `.github/workflows/`.

---

## Firing at a real pull request found a sixth defect

The fixes above were verified locally and looked complete. **They were not.** `deliver()` began:

```python
changed = [name for name in every_file if name.endswith(REVIEWABLE_SUFFIXES)]
if not changed:
    return Delivered(Outcome.NO_FILES, (), (), None)
```

and `pin_check` ran forty lines later. **A pull request that changes only a workflow — the most
common shape carrying a pin change — returned before the detector looked.** Handing it the
unfiltered list fixed nothing for exactly the changes it exists to catch.

**No test caught this and none of the earlier ones could have**, because they all asserted on the
detector's input rather than on whether it was reached. It was found by opening a real pull
request against a real repository and watching nothing happen.

The detector now runs before that return, and `NO_FILES` is conditional on there being no pins
either. Two tests assert the ordering, one reading the call site directly — a weak form of test
used deliberately, because the property that broke is an ordering that no behavioural test on the
current code path would notice.

**Proven in production on `QuantaMinds/quanta_mind#88`**, a pull request pinning
`actions/checkout` to a real SHA with four version comments, one deliberately stale:

> **Pinned action versions that disagree with the tag list** — checked against the GitHub API,
> not inferred:
>
> - `actions/checkout` is pinned to `fbc6f399` and commented `# v4.2.0`, but GitHub reports that
>   commit as **v5.1.0, v5**.

One finding, the intended one, silence on the other three. Posted by the App, on a real pull
request, from the fixed code.

---

## Why the re-measurement shows nothing, and why that is correct

The same 30 commits, re-run with every fix in:

| | before | after |
|---|---|---|
| raw findings | 27 | 25 |
| kept | 22 | 19 |
| kept per measured change | 0.733 | 0.633 |
| unanchored | 5 | 6 |
| refuted | 0 | 0 |
| unresolvable | (not counted apart) | 0 |

**Do not read 0.733 → 0.633 as an effect of the fixes.** On **6 of the same 30 commits the model
returned a different number of raw findings** — `44ffe6c6d6` gave 5 then 2, three commits went 0→1,
two went 1→0. Nothing was dropped by an oracle in either run, so every difference is the model
answering differently on an identical diff. **The pipeline is not deterministic run to run**, which
bounds what any small-sample comparison here can claim, including this one and including A6.

**The harness structurally cannot show the detector working.** `bench/rate/measure.py` calls
`review()` and `deep()` — ranking, model, gate. The detector lives in `review_delivery.py`, the
webhook path, which the harness never touches. So `pin_check` was not invoked once during this
run. **A measurement that cannot observe a thing is not evidence about it**, and reporting these
numbers as confirmation would repeat the denominator error retracted earlier in this session.

**The hex fix had nothing to act on here.** Zero findings in either run contained a hex token,
consistent with the 0-of-38 measured during the diagnosis. It is proven by targeted cases —
`"The cache key deadbeef1 is reused"` now publishes, `"The commit 4f2c1ab9de does not exist"`
still drops — not by this corpus.

**The counter split changed no number and that is the point.** `refuted 0, unresolvable 0` is
numerically what `refuted 0` was. It is now two zeros that mean different things: nothing was
contradicted by an authority, and nothing was unanswerable. Before, one number stood for both, and
A6's `refuted 1` was almost certainly an unresolvable wearing a refutation's label.

---

## What is still true after the fixes

**The gate on source-code findings is still exactly one stage: the anchor check.** 24.0% of raw
findings dropped, all of them unanchored. The refutation oracles remain unreachable because the
model is only ever shown ranked source files, and showing it workflows would widen what it reads
and break the cost argument the design rests on. That was a product decision before this
investigation and it survives it.

**So the honest description of the verification layer is: one working stage, plus a detector that
produces its own findings on a file class the reviewer never sees.** Not three stages. The
detector's base rate is **0.24%** — 3 genuine mismatches in 1,244 real commented pins across 22
repositories — so the expected outcome on any given pull request is still silence.

**Published-finding correctness remains unmeasured.** No oracle removes anything from a
source-code finding, so published correctness cannot beat raw correctness by any oracle margin;
the anchor check is the whole difference. The pack in `research/phase0/data/labelling/` is still
the only thing that would settle it, and is still unlabelled.
