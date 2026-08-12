# The coverage merge gate does not separate defective from clean AI pull requests

**Measured 2026-08-12** on the agent-arm corpus. This is the fourth negative result in this
repository and the one that closes the product line described in `PRODUCT_PLAN_2026-08.md`.

---

## The claim being tested

`PRODUCT_PLAN_2026-08.md` proposed auto-merging low-risk pull requests, gated on a condition
no competitor can express:

> Auto-merge only if **every call site in the diff resolved**. If we could not check
> something, a human does.

Everything else in that gate — ticket type, diff size, file paths, author, and even another
app's check-run conclusion — is already expressible by **Mergify's `auto_merge_conditions`**,
shipped 2026-05-06, whose condition attributes include `label`, `files`, `added-files`,
`added-lines`, `modified-lines`, `author`, and `check-success`. The coverage condition was
therefore the entire differentiator.

**It fails.**

---

## Result

| | Gate **holds** | Gate **passes** |
|---|---|---|
| Broke | **21** | **28** |
| Did not break | 74 | 88 |
| **Breakage rate** | **22.11%** | **24.14%** |

```
RR (held vs passed) = 0.916    naive Katz 95% CI [0.557, 1.505]
Fisher exact two-sided p       = 0.7462
n = 211 pull requests across 96 repositories
```

**The gate holds pull requests at a marginally LOWER breakage rate than the ones it lets
through.** It does not discriminate. The interval spans 1 comfortably in both directions.

### Firing rate — the number that looks like success and is not

| Measure | Value |
|---|---|
| PRs where ≥1 call site has no static callee name | **95 of 211 — 45.0%** |
| PRs where ≥1 changed symbol is named by no call site | **112 of 211 — 53.1%** |
| Individual call sites with no static callee name | **884 of 367,874 — 0.24%** |
| Hold rate, PRs touching ≤3 files | **45.3%** |
| Hold rate, PRs touching >3 files | **44.3%** |

The gate fires constantly — **nine times** the ≥5% floor the plan set. It is not decorative.
It is **active and wrong**, which is worse: enabling it holds nearly half of a customer's
otherwise-mergeable pull requests and prevents nothing measurable.

**The plan's own gate criterion was the wrong test.** It asked whether coverage is the
*deciding* condition often enough to matter. It should have asked whether coverage is the
*correct* condition. Firing rate measures use; only discrimination measures value.

---

## The one genuinely interesting property, which does not save it

**The hold rate is flat across pull-request size** — 45.3% at ≤3 files against 44.3% above.
Coverage is **orthogonal** to every attribute a competitor can already gate on. Filtering to
small pull requests does not reduce it, so Mergify cannot approximate it by proxy.

That would have been a strong moat if the signal were worth anything. It is orthogonal *and*
uninformative — a genuinely independent measurement of nothing that predicts defects.

---

## Consistency with the correlation test

This is the same finding from an independent framing.

| Framing | Population | Result |
|---|---|---|
| Correlation test — exposure vs breakage | 310 PRs, symbol level | **RR 1.040**, cluster-robust CI [0.598, 1.890] |
| **Merge gate — held vs passed** | **211 PRs, PR level** | **RR 0.916**, CI [0.557, 1.505] |

Two framings, two nulls, overlapping intervals centred on 1.

**Label noise does not rescue it.** The BROKE labels come from the file-level outcome rule,
which `PHASE0_PREREGISTRATION.md` measures as **65–71% false-positive** — verdicts sharing no
symbol with the pull request. Noise attenuates toward RR 1.0, so a corrected measure could in
principle move. The correlation test already ran that correction: restricting BROKE to
symbol-overlapping evidence gave **RR 1.251, p = 0.797** — *"the null survives the correction
that would have helped it."*

---

## Method, so this is reproducible

**Population.** All exposure records with `graph_status == "ok"` across
`results/exposure_shard1..5.jsonl` and `results/exposure_agent_linux.jsonl`. Records the
instrument could not analyse are excluded rather than coded as passing — a timeout is not a
clean bill of health.

**Gate definition.** A pull request is *held* when `no_static_callee_sites > 0`: at least one
call site in scope whose callee could not be named statically. This is the operational form
of *"coverage: full"* in the product plan.

**Outcome.** BROKE membership from `results/a54_confound.json`, the 53 verdicts re-derived
under A54, joined on `pr_id`. Everything else in the analysed set is coded as not broken.

**Statistics.** Naive Katz interval and Fisher exact. **Not cluster-robust** — 211 PRs across
96 repositories, and A8 requires clustering at repository level for the primary inference. A
clustered interval would be **wider**, not narrower, so it cannot rescue the result.

---

## Limits, stated rather than implied

- **n = 211**, 49 broken. The interval is wide and would be wider under clustering.
- **`no_static_callee_sites` is one definition of unresolvable.** It captures a missing static
  callee *name* — `HANDLERS[kind]`, `getattr(mod, cfg["name"])`. It does **not** capture a
  site that has a name resolving to the *wrong* target, which is the failure mode CodeGraph
  issue #765 documents. **A name-ambiguity gate is untested and is a different measurement.**
- **Python only, agent-authored, one corpus.**
- The gate was evaluated **marginally**, not jointly with ticket type, priority, CI status or
  test coverage, none of which the corpus carries.

---

## What this triggers

`PRODUCT_PLAN_2026-08.md` lists among its falsification criteria:

> Coverage is the deciding condition on **under 5%** of held PRs — the gate is decoration

That criterion **passes** at 45%, and it was the wrong criterion. The result here is worse
than decoration: the gate is load-bearing and uninformative. **The plan is falsified on a
condition it should have written and did not.**

What remains of the differentiator after Mergify's `auto_merge_conditions` and this result is
a single parser-based condition — detecting a changed public signature. That is a feature.

---

## Why this is worth publishing

Someone else will build this. The reasoning is attractive, the firing rate is high enough to
look like validation, and the failure only appears when you check discrimination rather than
frequency.

**A 45% firing rate reads as a working product.** It took a contingency table to see that the
held pile and the passed pile break at the same rate. That is the finding, and it belongs
beside the correlation-test null, the 65–71% symbol-mismatch in a standard outcome rule, and
the verdict-collapse table across seven shipping tools.

**Elapsed time from proposing the measurement to this result: about twenty minutes**, against
a product build measured in months. That ratio is the argument for the method, not for the
conclusion.
