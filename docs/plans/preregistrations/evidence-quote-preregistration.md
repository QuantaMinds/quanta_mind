# Design eleven — make the model quote its evidence, not just its target

**The gate reaches 62% of failures and cannot touch the rest.** Pooled across designs nine and ten,
24 wrong findings split three ways:

| class | share | what it needs | gate reaches it |
|---|---|---|---|
| **EXTERNAL** — a registry, a tool's behaviour, today's date | **62%** | a lookup | **yes — 9 of 9 in design ten** |
| **ABSENT** — code that is not in the diff | 17% | more context | no |
| **TRACE** — everything WAS in the diff and it still got it wrong | 21% | nothing; it did not look | no |

**The two it cannot reach have the same shape: the model asserts a chain it never verified.**

- `bokeh#15337` — claimed a loop calling `checkpoint` twice would break `assert_called_once`. The
  implementation was **in the same diff**: `case "s"` calls it, `case "q"` returns without calling.
- `attrs#1608` — claimed `uv run` had no command. The YAML `>` fold joins the lines and supplies
  one. **Decidable from the diff.**

## The change

**One field.** The same move that fixed the anchor — force the model to copy from its input —
applied to the reasoning rather than the location:

| field | purpose |
|---|---|
| `quote` | the defective line (unchanged) |
| **`evidence`** | **a second verbatim quote from the diff that, together with `quote`, makes the claim true.** `"SAME"` if the claim rests only on the quoted line |
| `claim`, `fix` | unchanged |

**Gate `G-evidence`: the evidence must be locatable in the diff, by the same string search that
locates the quote.** No model call.

**Why this should reach both classes.** A TRACE failure has evidence available and the model must
go and find it. An ABSENT failure has no evidence in the diff, so the model cannot produce one and
the gate drops it. **Same mechanism, both classes.**

**And a stated limitation: a claim about an ABSENCE cannot cite evidence.** *"No command is
provided"* has nothing to quote. Such claims will fall back to `"SAME"`, which is exactly the case
this design cannot strengthen.

## Corpus

**Fifty-four repositories are burned.** Six more, verified unused: `encode/starlette`,
`Textualize/rich`, `redis/redis-py`, `tox-dev/tox`, `agronholm/anyio`,
`marshmallow-code/marshmallow`. Ten pull requests each.

**Arms are subsets of one review pass, as in design ten**, so one blind rating scores all of them
and the rater never sees an arm label.

| arm | configuration |
|---|---|
| **A** | design nine — the established control, and a third replication |
| **E** | A + `G-evidence` |
| **EC** | A + `G-evidence` + the model decidability gate |

## Bars

| # | bar |
|---|---|
| **K1** | **EC's wrong-rate < A's, Fisher p < 0.05** |
| **K2** | arm A's wrong-rate < 50% with the Wilson upper bound clearing — **the third replication** |
| **K3** | sabotage catch ≥ 75%, printed first, else VOID |
| **K4** | yield ≥ 0.30 per pull request for any arm claimed as shippable |
| **K5** | ≥ 25 unique findings per arm, else UNDERPOWERED |
| **K6** | **among E's surviving WRONG findings, the TRACE + ABSENT share must FALL below 38%** — this is the bar that tests the mechanism rather than the score |

## Predictions

1. **Arm A replicates 25–45% wrong.** Two runs at 34.9% and 31.0%.
2. **G-evidence removes more findings than expected and yield is the binding constraint.** K4 is
   most at risk.
3. **K6 fails.** I expect the model to satisfy `evidence` by quoting a nearby line that does not
   actually establish the claim — the same way design eight's quote requirement was satisfied by
   abstaining rather than by anchoring better. **A string search cannot check that the evidence
   SUPPORTS the claim, only that it exists.**
4. **EC beats E**, because EXTERNAL is 62% of failures and only the model gate reaches it.

**Prediction 3 is the honest one: this design's gate is checkable for presence and not for
relevance, and that gap is where I expect it to fail.**

---

## The reading for each near-miss bucket, fixed before the data lands

**Four buckets, and they license different conclusions. Deciding after seeing which one dominates
would be a post-hoc adjustment, so the readings are written here first.**

| bucket | what it means | what it licenses |
|---|---|---|
| **absent from the diff entirely** | the model cited text that is nowhere | **the gate is working.** 62% is a fact about the model's grounding |
| **near miss in an added line** | whitespace, paraphrase, a span across a hunk boundary | **the gate is too strict on matching.** 62% is a fact about `locate()`, and the fix is a looser match, not a different rule |
| **present in the diff but NOT an added line** | **the model quoted CONTEXT — an unchanged line it can see** | **the RULE is wrong, not the model** |
| SAME / empty | the claim rests on the quoted line, or the model declined | neither |

### The third bucket is the one that changes the design, and the argument is a priori

**`G-quote` requires an added line and that is correct** — a finding about code the pull request
did not introduce is a finding about the existing codebase, which is not what a diff-scoped
reviewer was asked for.

**`G-evidence` requiring an added line does not follow from that.** A defect introduced by an added
line is frequently only demonstrable against surrounding unchanged code. *"This new early return
skips the ledger write below"* needs the write, and the write is context. **The evidence for a
defect in new code is very often old code.**

**So the loosening is licensed by the argument rather than by the number**, and it is stated now:
**`G-evidence` should accept evidence from ANY line of the diff — added, removed or context —
while `G-quote` continues to require an added line.** The measured bucket size tells us what the
strict rule cost, not whether to change it.

**The counterfactual is computable from the saved raw findings** — every rejection carries its
cited text, and re-locating against all diff lines needs no model call and no re-run. **Its
wrong-rate still needs adjudication**, because a looser gate publishes a superset of arm E and the
extra findings have never been graded.

**Design twelve is the loosened rule on a fresh corpus.** This run measures the strict one as
built.

---

## The reading for each near-miss bucket, fixed before the data lands

| bucket | means | licenses |
|---|---|---|
| **absent from the diff entirely** | the model cited text that is nowhere | **the gate is working.** The rejection rate is a fact about the model's grounding |
| **near miss in an added line** | whitespace, a paraphrase, a span across a hunk boundary | **the matching is too strict.** The fix is a looser `locate()`, not a different rule |
| **present in the diff but NOT an added line** | the model quoted CONTEXT — an unchanged line it can see | **see the calibrated threshold below** |
| SAME / empty | the claim rests on the quoted line, or the model declined | neither |

### The context bucket has a MEASURED threshold, not an argued one

**I was going to license loosening `G-evidence` to accept context lines on the argument that a
defect in new code is usually only demonstrable against surrounding old code. That argument is not
supported by our own data.**

Across designs nine and ten, 26 CORRECT findings; of the 17 that name any identifier:

| | share |
|---|---|
| every named identifier is in an **added** line | **88%** |
| some named identifier is found **only in context** | **12%** |

**So genuinely correct findings almost never need context to establish themselves.** 12% is the
rate to beat, not "very often".

**The pre-registered reading:**

- **context bucket at or below ~12%** — the model is reaching for context at the same rate correct
  findings actually need it. **The rule is defensible; loosening buys little.**
- **context bucket far above ~12%** — the model is citing context it does not need. **That is a
  grounding failure, not a rule problem, and loosening would admit exactly the findings that reach
  for support they cannot use.**

**Either way the loosening is NOT pre-licensed.** If it is ever made, it is design twelve on a
fresh corpus with the bar fixed again.

**The proxy is weak and that is stated:** backticked identifiers cover only 17 of 26 correct
findings, the other 9 naming nothing at all. **It measures where a claim's named symbols live, not
where its evidence lives**, and a stronger test would need findings labelled by hand for what
established them.
