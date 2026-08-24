# The external-fact oracle — and the one way it can add a correct finding rather than only remove a false one

**Written before the code. Bars fixed here.**

## What is being fixed, and what is not

Measured live on 2026-08-24 (`bench/forensic/confabulation.py`): shown twelve real GitHub Actions
pinned to SHAs fetched from the API during the run, the reviewer objected to **6 of 12 correct
pairings and 5 of 12 wrong ones — discrimination −8.3%**. In 7 of 24 trials it said the SHA does
not exist; every one had just been fetched from GitHub. **It is not checking. It cannot check.**

| class | n of 45 | oracle exists? |
|---|---|---|
| SHA → tag | 14 (31%) | **yes** — one GitHub API call |
| registry version exists | 3 (7%) | **yes** — PyPI / npm index |
| date arithmetic | 5 (11%) | **yes** — inject today |
| adjacent refuting code | 5 (11%) | partly; hunk expansion already moved TRACE+ABSENT 73.3% → 18.8% |
| semantic misreading | 17 (38%) | **no** — the fact is a conclusion, not a lookup |
| string-op / convention tail | rest | **no** |

**~53% of wrong findings are addressable. 38% are not**, and an August 2026 result has LLMs failing
to re-localise a defect they had localised correctly in **78%** of cases under semantic-preserving
rewording. That is a research problem, not an engineering gap.

## The part I under-stated, and it is the only reason this is worth building

**"A verifier deletes; it cannot create" is true of a verifier. An oracle is not only a verifier.**

Used one way it kills a model claim that contradicts ground truth — deletion, and the 16.7% ceiling
applies. Used the other way **the oracle reads the diff itself**: it finds every SHA-pinned action,
resolves each against GitHub, and emits a finding when the pin and its comment genuinely disagree.

That finding is produced by a parser and an API. **No model was asked, so no model can be wrong
about it, and its precision is 100% by construction.** It is a new entry in the numerator, not a
survivor of the old one.

**Whether that numerator moves at all is an empirical question and this plan does not assume it.**
Real mismatched pins may be vanishingly rare. Measuring their base rate is the cheapest step here
and it comes first, because if the answer is zero the rest is deletion again and the ceiling holds.

## Build order — cheapest falsification first

1. **Measure the base rate.** Scan N real merged pull requests for SHA-pinned actions whose comment
   disagrees with the tag GitHub reports. **No model, no build beyond a scanner.**
2. **The oracle** — `verify/external_facts.py`. Resolvers for SHA→tag, registry version existence,
   and today's date. Three outcomes per claim, never two: `REFUTED`, `CONFIRMED`, `UNRESOLVABLE`.
3. **The gate** — a finding whose external claim is `REFUTED` is dropped. **So is `UNRESOLVABLE`**:
   a claim we cannot stand behind is not one we publish, and collapsing it into `CONFIRMED` is how
   the current failure happens.
4. **The detector** — the oracle emits its own findings from step 1's scan.
5. **Re-measure** the wrong-rate on the stored pool with the gate applied.

## Bars, fixed now

- **Step 1 (base rate):** report it whatever it is. **A rate of 0 means step 4 is not built** and is
  recorded as a closed road, not retried.
- **Step 3 (the gate):** must remove **≥ 80%** of the 17 SHA/registry-class wrong findings in the
  stored pool, and must remove **0** of the 12 correct findings. A single correct finding lost
  fails the step — this class is not one where a trade is acceptable, because the oracle is
  deterministic and a deterministic check that kills a true finding is a bug, not a threshold.
- **Step 4 (the detector):** every finding it emits must be reproducible from the API by hand. Any
  finding that cannot be is a defect in the oracle, not a false positive to be tuned away.

## What this does NOT do, stated before it is built

**It does not reopen Half B.** Applying every fixable item optimistically reaches **29.3% wrong,
12.1% correct** against a 49% field floor, and the yield — one useful comment per 27 to 77 pull
requests — is what closed the half. Removing false comments does not produce true ones, and step 4
is the only part that could, at a base rate this plan expects to be small.

**What it is worth regardless:** the SHA class is 31% of our wrong findings, it is the single
largest mechanism, and it is the one that most directly costs trust — a developer who checks
"this commit does not exist" against a commit that does never checks the next one.

## What could still silently fail

An oracle that cannot reach GitHub returns `UNRESOLVABLE` for everything, which drops every finding
in the class and looks exactly like a gate working perfectly. **The rate of `UNRESOLVABLE` is
therefore reported on every run**, and a run where it exceeds a threshold is a failed run rather
than a clean one — the same defect as a filter admitting nothing across a whole pass.
