# Architectural drift does not separate the outcome — D2E CLOSED

**Run 2026-08-31 against `docs/plans/preregistrations/ranker/drift-preregistration.md`, committed in
`3c38478` before any repository was cloned. 305 library files across four repositories the method
had never seen. Script: `scripts/measure/graph/drift_separates.py`.**

## The registered verdict

| bar | required | observed | |
|---|---|---|---|
| **B1** enough to decide | ≥ 200 files, ≥ 3 repositories | **305 files, 4 repositories** | **MET** |
| **B2** drift separates the outcome | high tertile exceeds low by **≥ 10pp** | **high is 3.5pp LOWER** | **NOT MET** |
| **B3** and not because of churn | must survive within strata | see below | not reached |
| **B4** it must beat what ships | — | not reached | not reached |

**Any bar unmet closes the row.** D2e is closed.

## The numbers

| tertile | files | mean drift | mean fix rate |
|---|---|---|---|
| low | 101 | 0.064 | **0.182** |
| high | 101 | 0.345 | **0.147** |

**The effect is not merely absent, it points the other way.** Files whose imports move most are
returned to by a fix *less* often, not more. The registered bar asked for +10pp and the observation
is −3.5pp.

Within churn strata, which is the control B3 exists for:

| churn | n | low fix rate | high fix rate | gap |
|---|---|---|---|---|
| 10–20 | 110 | 0.134 | 0.138 | **+0.4pp** |
| 20–50 | 122 | 0.189 | 0.140 | **−4.9pp** |
| 50+ | 73 | 0.241 | 0.148 | **−9.3pp** |

**The sign is not stable, so this is not even a usable negative signal.** It runs from +0.4pp to
−9.3pp across three strata of the same population. A signal that changes direction with how much a
file was edited is a description of the editing, not of the architecture.

## The repository that would have made this look real

**`pallets/werkzeug` alone gave −9.1pp, −21.1pp and −19.9pp across the same three strata** — a
strong, consistent, publishable-looking effect in the negative direction. Pooled across four
repositories it collapses to +0.4pp, −4.9pp, −9.3pp.

**One repository is a fact about that repository.** This is the third time that has been recorded
here: the handoff memory already says a single repository usually misses the pre-registered floors
and that pooling is the validated unit, and `publishing-rules.md` requires the pooled figure for
the ranking claim for exactly this reason. Had werkzeug been the whole run, D2e would have shipped
a backwards signal with confident numbers behind it.

## The reverse direction was looked at, and it is the denominator

**"High drift attracts fewer fixes" invites the obvious follow-up: then what attracts MORE?**
Asked and answered on this same data, EXPLORATORY, no bars, nothing registered — and the answer is
that there is nothing there.

Holding the fix count **exactly** constant, so churn is the only thing left to vary:

| fixes = N | files | stable fix rate | drifting fix rate | gap | stable churn | drifting churn |
|---|---|---|---|---|---|---|
| 2 | 47 | 0.135 | 0.114 | +2.1pp | 17.2 | 20.6 |
| 3 | 32 | 0.164 | 0.142 | +2.3pp | 21.1 | 25.4 |
| 4 | 31 | 0.153 | 0.190 | **−3.7pp** | 31.0 | 24.7 |
| 7 | 16 | 0.215 | 0.172 | +4.3pp | 34.8 | 49.5 |

**+2.1, +2.3, −3.7, +4.3 on cells of 16 to 47 files is noise**, and the sign changes.

## AND THE INSTRUMENT HAD A DEFECT I HAVE TO STATE

**`drift = shifts / churn` and `fix_rate = fixes / churn` SHARE A DENOMINATOR.** Two ratios over the
same denominator move together by construction, whatever the numerators do — so part of any
association between them is arithmetic rather than evidence. With the fix count pinned, `fix_rate`
*is* `N / churn`, and the whole comparison collapses to "are drifting files edited more?" Across all
305 files, drift against churn is **r = −0.177**: weak, and enough to matter.

**THE VERDICT IS UNAFFECTED, AND THE REASON IS WORTH WRITING DOWN RATHER THAN ASSUMED.** A shared
`1/churn` induces a POSITIVE association between drift and fix rate. B2 asked for a positive one and
observed a **negative** one — so the artefact could only have flattered the hypothesis, and it still
failed. The bar is if anything more securely unmet than the headline number suggests.

**It would have mattered enormously had the result gone the other way**, and it was not noticed
until the follow-up question forced the arithmetic into view. Same family as
`docs/engineering/CORRECTIONS.md` entry 7: two quantities that look independent and are not. A
future attempt at this must not use a rate whose denominator is also the outcome's.

## What we are NOT concluding

**The direction has a plausible mechanism and it is a HYPOTHESIS, not a finding.** A file whose
imports keep changing is plausibly a file under active development — new dependencies arriving with
new features — while a file touched repeatedly *without* its dependencies moving is plausibly a
file being patched. That story fits the sign. Nothing here tests it, and `AGENTS.md` asks which of
the two we are claiming: **diagnosis, not detector.**

**And this does not condemn cross-file context generally.** D2c is the counter-example: the same
kind of structural, model-free, cross-file claim, measured before it shipped, and the three groups
it found in `pallets/flask` are the ones the maintainers later hoisted into a shared base class.
What has now failed twice is the **import graph as a ranking or risk signal** — D2d on blast radius,
D2e on drift.

## The corpus

`tiangolo/fastapi`, `pallets/werkzeug`, `python-trio/trio`, `sanic-org/sanic` — all four confirmed
FRESH by `scripts/guard/records/check_burned_corpora.py` before cloning, none of them among the
thirty-eight already spent. **No repository was added after seeing a result**, which is the rule the
pre-registration fixed and the one a null tempts you to break.

fastapi contributes only 25 files despite 1,138 Python files in the tree: most are documentation
examples under `docs_src/`, which `suite_reach.is_library` correctly excludes.
