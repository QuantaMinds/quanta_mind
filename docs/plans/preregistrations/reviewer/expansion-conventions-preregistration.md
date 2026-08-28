# Design 13 — enclosing-function expansion and the repository's own rules

Written before any model call on the corpus below. Bars are fixed here. A near-miss is a fail.

## What is being tested

Two mechanisms taken from Qodo, the top tool of 49 on Martian's offline layer at 67.9% precision,
both of which this project currently discards:

- **Expansion** (`research/phase0/quote/expand.py`) — git writes the enclosing declaration into
  every hunk header and we throw it away. The reviewer sees `+ if order.refunded:` with three lines
  of context and does not know what function it is in. Expansion walks back to the declaration.
- **Conventions** (`research/phase0/quote/conventions.py`) — the repository's own `AGENTS.md` or
  `CONTRIBUTING.md`, so a finding can cite the house rule it breaks instead of a generic notion of
  good code.

## Corpus

Six repositories, each verified absent from every file under `research/` before selection, each
carrying a conventions file. Fifteen merged pull requests apiece, ninety total.

| repository | conventions file | chars |
|---|---|---|
| `pyca/cryptography` | `AGENTS.md` | 1,095 |
| `falconry/falcon` | `AGENTS.md` | 6,101 |
| `pytest-dev/pluggy` | `CLAUDE.md` | 2,043 |
| `jazzband/pip-tools` | `CONTRIBUTING.md` | 4,807 |
| `scikit-build/scikit-build-core` | `AGENTS.md` | 10,868 |
| `aws/aws-cli` | `CONTRIBUTING.md` | 7,920 |

**Every repository here has a conventions file, and that is a selection, not a sample.** Sampling
repositories at random found a usable rules file in roughly one of three. Arm C's result therefore
describes the repositories where the mechanism can act at all, and must never be quoted as an
effect over repositories generally.

### Two corrections made before any model call, against no outcome

**Three of the first six repositories shipped a POINTER, not rules.** `pluggy`'s `AGENTS.md` is
"See @CLAUDE.md", `sanic`'s and `trio`'s `CONTRIBUTING.md` are a bare URL — 62, 72 and 98
characters against 1,095–6,101 for real ones. The first selector accepted all three, so arm C
would have been a silent no-op on half the corpus and reported as though the rules had been sent.
`conventions.MIN_CHARS = 400` now rejects them and the selector skips a stub to the next candidate.
`sanic` and `trio` have no usable rules file at all and were replaced.

**`tornadoweb/tornado` was in the corpus and is burned** — it appears in the aged corpus and in
`rater7` and `rater8`'s chunks. It was added by eye without running the freshness check that every
other repository passed. Replaced. The check is mechanical for exactly this reason.

Priority order beats length when choosing among usable files: `falcon` ships a 6.1k `AGENTS.md` of
coding rules beside a 14.8k `CONTRIBUTING.md` that is mostly how to sign a CLA.

## Arms

Three arms over the same ninety pull requests, paired by pull request.

- **A** — design nine's configuration, unchanged. `evidence=False`, no expansion, no rules.
- **B** — A plus expansion.
- **C** — B plus the conventions block.

Arms B and C change the prompt, so they produce different findings than A. This is **not** the
subset pairing of design ten, where one adjudication scored three arms. Every finding from every
arm is adjudicated, arm label hidden.

## What is already settled and is not being retested

`MAX_BACK = 20` was chosen by a coverage sweep over 211 hunks of six **already-burned**
repositories: 40.3 / 55.5 / 62.1 / 73.9% expanded at 5 / 10 / 20 / 60. The sweep measured coverage,
never a wrong-rate, and never on the six repositories above. It is fixed and is not an outcome.

The anchor invariant — expansion must not move an added line — held on all 211 hunks at every cap
from 5 to 60, and is asserted per pull request during the run. **A single shift aborts the run.**

## Hypotheses and bars

**H1 (primary, mechanism).** Expansion targets one failure class: claims wrong because the model
could not see the enclosing function. Among adjudicated-wrong findings, the share classed
`TRACE`/`ABSENT` falls from A to B by **≥ 15 points**.

**H2 (secondary, headline).** Arm B's wrong-rate on unique findings is **≤ 30%**, against design
nine's 34.9% and design ten arm A's 31.0%, with the Wilson upper bound reported. Failing H2 while
passing H1 means the mechanism worked and moved nothing overall — report both.

**H3 (harm, conventions).** A rules file is mostly style, and a reviewer already 30–35% wrong may
buy convention-policing dressed as defect-finding. **Arm C's wrong-rate must not exceed arm B's by
more than 10 points.** If it does, the conventions block is not shipped, whatever it does to yield.

**H4 (yield).** Arm B publishes ≥ 0.30 findings per pull request, design ten's bar. Expansion that
buys accuracy by falling silent has not bought accuracy.

## Power, stated in advance so a null is not over-read

At an expected 30–50 unique findings per arm and a base rate near 0.33, the 95% interval half-width
is roughly 13 points. **This run can detect a large effect and nothing smaller.** A null on H2 is
not evidence that expansion does not help; it is evidence this corpus was too small to say. That
sentence is written here, before the number exists, so it cannot be reached for afterwards.

## Adjudication

Blind, per `docs/plans/preregistrations/reviewer/adjudication-preregistration.md`: arm labels stripped, findings shuffled,
raters out-of-family, sabotaged controls (a real quote paired with a claim from a different pull
request) mixed in at a known rate. **A rater pool that does not catch the controls is discarded
before its ratings are read.**

## What could still silently fail

- Expansion could add context that shifts the model's attention off the added lines and onto
  surrounding code, producing findings about code the pull request did not touch. `gate.py` already
  requires the quote to be an ADDED line, so those die at `G-quote` — but they would show as a
  falling yield, not as an error, and H4 is what catches it.
- `corpus.blob` reads the **base** sha. Reading the head would misalign every expansion by whatever
  the pull request changed. The unit check pins base, not head.
- A conventions file can be stale, aspirational, or contradicted by the code. The model would cite
  a real rule that the maintainers stopped enforcing. Nothing here detects that; it lands in H3.
