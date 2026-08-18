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
