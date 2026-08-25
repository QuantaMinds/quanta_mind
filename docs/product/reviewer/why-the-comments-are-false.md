# Why two thirds of the comments assert things that are not true

**Run live on 2026-08-24 against the GitHub API, not recalled from a stored pool.**
→ `research/phase0/bench/forensic/confabulation.py`, `bench/results/confabulation.json`

## The failure has a shape, and one mechanism dominates it

Blind raters classified 45 real wrong findings (a further 10 `ABSENT` verdicts were planted
sabotage items and are excluded). Classifying their written reasons mechanically:

| mechanism | n | share |
|---|---|---|
| **claims about which tag a pinned commit SHA carries** | **14** | **31.1%** |
| refuting code was adjacent — often two lines away | 5 | 11.1% |
| date arithmetic ("this is in the future"; it was past) | 5 | 11.1% |
| string-operation semantics (`removesuffix`, `endswith`, `.encode()`) | 4 | 8.9% |
| module-path convention | 3 | 6.7% |
| registry tag existence | 3 | 6.7% |
| flag not present in the code (`O_TRUNC`) | 2 | 4.4% |
| asserted a merged, passing test's assertion is wrong | 2 | 4.4% |
| control flow misread (a `for` loop that does advance) | 2 | 4.4% |
| anchored to the wrong symbol | 2 | 4.4% |
| direction reversed (called an upgrade a downgrade) | 1 | 2.2% |
| not decidable from the diff | 1 | 2.2% |

44 of 45 classified; one unmatched.

## The live test, and why it is built the way it is

The dominant mechanism is testable, so it was tested rather than argued.

Twelve real GitHub Actions. For each, the newest tag and its true commit SHA were fetched **from
the GitHub API during the run**. Two workflow diffs were then built pinning that same real SHA:

- **TRUE_PAIR** — commented with the tag the SHA genuinely carries
- **FALSE_PAIR** — commented with a tag it genuinely does not

The shipped reviewer prompt saw both. **The control arm is the whole experiment**: a reviewer that
objects to every pinned SHA looks identical to one that detects wrong pins, if only wrong pins are
tested — and its objections on those would read as successes.

## Result — n = 24, and there is no signal

| | objected | |
|---|---|---|
| **TRUE pairing** (correct comment) | **6 / 12 = 50%** | every one of these is a false claim |
| **FALSE pairing** (wrong comment) | **5 / 12 = 42%** | verdict correct |
| **discrimination** | **−8.3%** | |

**A one-trial difference in the wrong direction. The honest reading is that the objection carries
no information about whether the pairing is real** — a 50% rate on correct pairings is what a coin
flip produces. The two arms received the same treatment for 7 of 12 actions, which is also chance.

## What it says when it objects, checked against GitHub

**In 7 of 24 trials it stated that the commit SHA does not exist. Every one of those SHAs had been
fetched from GitHub's own API minutes earlier.**

Verbatim, on a **correct** pairing:

> "The new commit SHA for `actions/checkout` does not correspond to a known commit in the official
> repository, creating a supply chain security vulnerability by potentially running untrusted code."

And in an earlier four-action run, on a wrong pairing, it produced a specific invented version:

> "The version comment `# v6.0.0` is incorrect, as the specified commit hash corresponds to version
> `v4.0.2` of `actions/cache`."

`v4.0.2` is not the tag. The SHA carries `v6.1.0`.

**Even the correct catches are correct by accident.** On FALSE_PAIR for `actions/checkout` the
verdict lands — something is wrong with this pin — but the stated reason is that the SHA does not
exist, and it does. A developer who checks the reason finds nothing wrong with the SHA and
concludes the tool is broken, which is the correct conclusion from the evidence they were given.

## Why it happens

**A 40-character hex string carries no information about a version number.** That mapping exists in
one place — the repository's tag list — and nothing in a diff contains it. The model cannot look it
up, and it does not decline. It emits the shape of a finding, and the shape available for an
unverifiable identifier is "this does not exist".

That is the general form, and it explains the other rows too. `EXTERNAL` failures are questions
whose answer is not in the input: which tag a SHA carries, whether a version is on PyPI, what
today's date is. **The model's confidence is unrelated to whether the answer was reachable.**

## Why filtering does not fix it

Removing every false comment leaves the true ones. There were 12 correct findings in 207
adjudicated: a perfect verifier for both failure classes reaches **C/n = 16.7%** against a field
floor of 49%. **A verifier deletes; it cannot create.**

And the mechanism is not one a parser can adjudicate: **0 of 45** wrong findings were
parser-refutable. Deciding whether `9c091bb2` is tagged `v7.0.0` requires the tag list, which is
exactly the fact the diff does not carry.

## Two instrument errors made during this investigation, disclosed

1. **The first `DISPUTES` pattern missed two objections of six** — "does not belong to the official
   repository" and "the version comment is incorrect" — so the discrimination figure was computed
   over a mis-sized population. Widened, re-run, and every number above uses the wider form.
2. **"The objection tracks the repository rather than the pairing" was drafted and withdrawn.** The
   arms agreed for 7 of 12 actions, which is what a coin flip gives. There is no evidence for the
   stronger claim, and no signal is the finding.

---

# Fix 1, measured: the oracle, and what the base rate says about it

## The prevalence of the defect the detector looks for

1,259 commented SHA pins read from the workflow files of 22 large repositories at HEAD, each
resolved against GitHub's tag list. 15 unresolvable, counted separately and never as clean.

| rule | flagged | of 1,244 resolvable |
|---|---|---|
| exact tag match | 13 | 1.05% |
| **alias-aware** (`# v6` satisfied by `v6.4.0`) | **3** | **0.24%** |

The three genuine ones, all real and all verifiable by hand:

| repository | action | commented | GitHub says |
|---|---|---|---|
| pandas-dev/pandas | codecov/codecov-action | `# v5` | v7.0.0, v7, v6.0.2, v6 |
| grafana/grafana | docker/setup-docker-action | `# v4` | v5.3.0 |
| grafana/grafana | peter-evans/create-or-update-comment | `# v4` | v5.0.0, v5 |

**Not zero, so the detector is worth having. 0.24%, so it is a rare correct finding rather than a
stream of them** — and the rate at which a *pull request introduces* one is lower still, because
the stock bounds the flow.

## "100% precision by construction" was claimed here and it was false — twice

Both defects were found by running the cheap prevalence scan **before** building anything on the
detector, which is the only reason they were found at all.

1. **`tags_at` scanned the tag list line by line, and GitHub returns it as ONE line of compact
   JSON.** It paired the first `"name"` with the first `"sha"` and returned a single tag where the
   commit carried two. Every moving major alias was invisible.
2. **The rule required exact tag equality.** `# v6` on a commit tagged `v6.4.0` is the universal
   convention — the `v6` alias has moved on to a newer release and is not at that commit.

Together they flagged 13 pins of which **10 were correct: a 77% false positive rate, worse than the
model this was built to replace.** Both are fixed, both are covered by tests, and the claim is now
that the rule is *deterministic* — not that it was right the first time.

**A deterministic checker is not automatically a correct one.** It removes the model's confabulation
and replaces it with the author's assumptions, and those need measuring too.

## Where fix 1 leaves the arithmetic

The class is 14 of 45 wrong findings (31%). The verifier removes them: on the 24 live trials it
refuted 7 of 15 pin-related findings and left 4 unresolvable, which are also dropped. **That is
deletion, and the 16.7% ceiling still applies to it.**

The detector adds findings — at 0.24% of pins. **It is a real entry in the numerator and a small
one.** Nothing here reopens Half B, and the honest summary is that the largest single failure
mechanism is now handled deterministically instead of guessed at.
