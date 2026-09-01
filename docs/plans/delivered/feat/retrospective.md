# Plan — the retrospective

**Goal: on a clone and nothing else, report what the ranker would have said about this
repository's own history — and what a later fix actually returned to.**

This is the sales instrument. A prospect runs it before granting any access: no App install, no
webhook, no token, no code leaving the machine. It is also the only bottom-up motion this company
has, and `docs/product/QUANTAMIND.md` names distribution as the weakest point by a distance.

---

## The one decision that shapes everything else

**It replays the VALIDATED event definition, not a new one.**

`research/phase0/external/defect_return.py` defines an admissible event: a commit touching 2–12
`.py` files that a later commit within ninety days, carrying a fix-shaped subject, returns to. The
top-three-by-fix-history miss rate on those events is the number with the p-value — 1.21% against
alphabetical's 3.12%, n = 2,400, six repositories the method never saw.

A retrospective that invented its own definition would produce a number that looks like the
published one and is not it. So the retrospective reports **the same statistic, computed the same
way, on the prospect's repository**. That is the whole pitch: our number on our six repos becomes
their number on their repo.

**It is NOT another out-of-sample replication, and the plan must not say so.** A replication needs
its reading fixed before the data is seen; a prospect's run is unblinded by construction — we see
the number, and so do they. Worse, a collection of them skews: a prospect who runs it and dislikes
the result does not send it back. **If these are ever aggregated, the policy is pre-commit to
reporting every run including the unfavourable ones, or do not treat the collection as evidence at
all.** Written here because the temptation arrives later, with a folder full of good ones.

**It therefore needs no GitHub API.** "Closed pull requests" in the stage description is a proxy
for "changes that landed"; the event definition already reads landed commits, which a clone has.
`gh` stays out of this path entirely.

---

## The duplication this must not add to

The event definition is currently written out **twice**, in `tests/live/test_event_replay_gate.py`
and `tests/live/test_gate_2b_pinned_corpus.py`. Both copies drifted once already: one matched
fix-words case-sensitively under a comment claiming it matched the research, and admitted strictly
fewer events for as long as it stood.

A third copy inside the product would be the same pattern with higher stakes, because this copy is
the one a customer sees. So:

1. Extract the definition to **`rank/events.py`** — one public concern, the admissible event.
2. Both gate tests import it instead of restating it.
3. **Gate 2b passing after the extraction is the proof the extraction is faithful.** It compares
   against a checked-in artefact event-for-event, so a definition that shifted by one event fails.

`rank/` may not import `ingest/`. `events.py` takes `list[Commit]` — a `types/` dataclass — and
returns events. It receives the history; it does not read it.

---

## Layer placement

| module | layer | why there |
|---|---|---|
| `rank/events.py` | `rank` | the unit the ranking policy is *measured on*, beside the policy itself |
| `serve/retrospective.py` | `serve` | orchestrates ingest → store → rank → render; rightmost layer, may import all of them |

`serve/cli.py` loses `retrospective` from `UNBUILT`.

---

## The gate

**No data from after a change may enter its own ranking.**

The bound is `touches.counts(..., as_of=commit.committed_at)` over the half-open window
`[as_of − 365d, as_of)`. The commit's own timestamp is excluded, so a change cannot raise its own
score.

**Known-answer test.** The earliest admissible event in a repository must produce the no-history
case — every path at zero — because nothing precedes it. Not "a low score": zero.

**Sabotage the bound itself.** Remove the `as_of` cutoff (count all touches regardless of time)
and the leakage test must FAIL LOUDLY. If removing the bound merely improves the numbers, the test
was measuring the corpus and not the bound.

**Second sabotage, because the first is not enough.** `as_of` is passed by the caller. A
retrospective that passed `as_of=now` would still be bounded *in the store* and completely leaked
*in fact*. So the test also asserts that the ranking for each event is identical when the index is
rebuilt from **only the commits strictly before it** — the same assertion
`tests/live/test_end_to_end.py` already makes, applied per event.

---

## The distinction that must live in the OUTPUT, not in anyone's head

**Gate 2b is met** — `rank/` reproduces `defect_return_external.json` event for event on the six
pinned repositories, 2,400 events, and `just gate-2b` re-proves it. That is a *reproduction on the
corpus that carries the p-value*.

**A retrospective run is not that.** It is the same ranking code on a repository nobody has ever
measured, n unknown, unreplicated, and chosen by the person it will be shown to. The two numbers
have the same units and the same shape, which is exactly why they will be quoted side by side the
first time someone pastes the output into a deck.

So the output states its own provenance, every run, above the numbers:

- which corpus this is (`this repository, first measurement`) and that it is **not** the validated
  result
- the published claim named separately, with its n, its repository count and its p-value, and
  marked as measured **elsewhere**
- no arithmetic combining the two, ever — no "compared with", no ratio, no "in line with"

**A run on one repository cannot confirm or refute the published figure**, and a reader with both
numbers in one paragraph will assume it does. `docs/product/publishing-rules.md` governs the
printed form; this is the same rule applied to a number the customer generates themselves.

## What the numbers actually are, measured before building anything

Three claims in the first draft of this plan were checked against the corpus and the research, and
**two of them were wrong.**

**WRONG — "the fresh six produced roughly 400 events each, so a prospect will miss the 500 floor."**
400 is `MAX_EVENTS`, the cap, not the supply. Uncapped, measured with `rank/events.py` on the
pinned corpus:

| repo | commits | events |
|---|---|---|
| scrapy | 6,536 | **1,447** |
| celery | 8,022 | 2,366 |
| ansible | 34,361 | 5,661 |
| scikit-learn | 23,715 | 7,905 |
| django | 23,181 | 10,957 |
| pandas | 29,155 | **16,538** |

**44,874 pooled, not 2,400.** Every one clears the 500 floor by 3× to 33×.

**But that conclusion was ALSO wrong, and the built instrument proved it.** Run against three
repositories nobody had measured, every single one came back INCONCLUSIVE:

| repo | events | discordant | ranker vs chance (informative) | verdict |
|---|---|---|---|---|
| psf/requests | 551 | **12** | +16.35 | INCONCLUSIVE — under the 20-pair floor |
| tiangolo/fastapi | 257 | 20 | +17.24 | INCONCLUSIVE — 243 events short |
| pallets/click | 414 | 6 | +10.92 | INCONCLUSIVE — 86 short, **and p = 0.69** |

The pinned six are unusually large. `requests`, `fastapi` and `click` are popular, mature projects
and none of them reaches the floor, so **INCONCLUSIVE is the default output for a typical
prospect after all** — the original concern was right and the correction to it was overconfident.
Multi-repo pooling is therefore a rescue, not a convenience, and it is the one piece of this plan
still unbuilt.

**`click` is a real null and the instrument said so**: 4 discordant pairs for the ranker against 2
for the control, p = 0.69. It also shows alphabetical at **+1.89 against chance** — the
layout-encodes-importance effect the research found in home-assistant, appearing unprompted in a
repository chosen at random.

**RIGHT, and understated — the degenerate stratum.** 68.6% of events touch ≤3 files, where a
budget of three IS every file. Measured on the discriminating set: ≤3 files scores **0.00% miss
for every arm**, and the pooled figure is diluted about threefold.

| stratum | n | history | alphabetical | chance | history − chance |
|---|---|---|---|---|---|
| all | 2,278 | 1.05% | 2.77% | 2.76% | **+1.70** |
| ≤3 files | 1,514 | 0.00% | 0.00% | 0.00% | +0.00 |
| **≥4 files** | 764 | **3.14%** | **8.25%** | **8.21%** | **+5.07** |

**WRONG — reporting against alphabetical.** `defect-return-external-preregistration.md` already
settled this: alphabetical's strength varies by repository layout, so it is not a stable reference.
In home-assistant it sat +1.75 above chance because `components/<name>/__init__.py` sorts first and
is also the churn-heavy file — the control accidentally encoded importance. **The invariant
comparison is exact hypergeometric chance, computed per event, and it is the one to quote.**

The formula is `research/phase0/claims/stats.py:39` and is reimplemented rather than imported —
rule 11 keeps research out of the product. On the pinned six, alphabetical lands at **−0.01
against chance**, so here it happens to be honest; the third sample is where it was not. History
beats chance in **6 of 6**, from +0.54 (pandas) to +6.06 (scrapy).

**So the retrospective's headline is history versus CHANCE on the ≥4-file stratum**, with the
degenerate share printed beside it, and alphabetical kept only as the figure the published claim
used.

## Prior art, named rather than discovered

Ranking files by prior fix history is **BugCache** — Kim, Zimmermann, Whitehead and Zeller, ICSE
2007, ACM SIGSOFT Distinguished Paper — which caches fault-prone locations from known fixes and
reported 73–95% hit rates across seven projects. `QUANTAMIND.md` already says the ranker is not
the moat; this is the citation for why. Their unit is a cache of N locations over a project's
lifetime, ours is the top three files of one change, so **the numbers are not comparable and must
never be printed together.**

The change-size distribution is corroborated externally too: published pull-request studies put
the **median at 2 files changed**, 80th percentile 7. Our corpus is 49% at exactly two files. The
degenerate stratum is not an artefact of these six repositories.

## What it prints

Per repository, one block:

- events found, and how many were rejected by each clause of the definition — **counted, never
  silent**, so a definition that started rejecting everything cannot read as a clean run
- top-three miss rate, against the alphabetical control on the same events
- the same for the no-history case, which is where the ranker declines to speak

**STRATIFIED BY FILE COUNT, because the pooled rate oversells by construction.** The definition
admits 2 to 12 files, and roughly two thirds of real changes touch three or fewer. On those, the
top three IS every file: the ranker cannot miss, the control cannot miss, and both score a perfect
hit no matter what the ordering says. Pooling them with the informative events dilutes exactly the
way an earlier figure in this project did.

So the block reports **≥4 files separately** — the stratum where a ranking decides anything — and
that is the number the headline should quote. The ≤3 stratum is printed beside it, labelled as
decided-by-construction rather than hidden.

**`tie_at_boundary` is printed too**: events where the third and fourth files score equally, so
which one the budget reads is arbitrary and the hit is luck. It sits alongside `no_history` and
`flat_nonzero` as a case the reader is told about rather than one the average absorbs.

**The control ships beside the number, always.** A miss rate with no control is a number about the
repository, not about the ranker, and `AGENTS.md` says a gate the null also passes is measuring
the corpus.

**It must refuse to report rather than report thinly.** Below the pre-registered floors from
`defect_return.py` — 500 events, 20 discordant pairs — it prints INCONCLUSIVE.

**The floors will fire on almost every single repository, and that is a product problem, not a
statistics one.** The fresh six produced roughly 400 events EACH against a 500 floor, so a typical
prospect lands under it and the sales instrument's default output becomes "we cannot tell you
anything". Three ways out were considered and the choice is recorded here because it must be made
before the module exists:

| option | verdict |
|---|---|
| point estimate with an interval, marked below floor | **NO.** This is the number that gets pasted into a deck with the caveat stripped |
| INCONCLUSIVE with the event count and the shortfall named | **YES** — the prospect learns how much history the question needs |
| pool across the customer's repositories | **YES, as an explicit multi-repo mode** |

**Pooling is not a new unit — it is the VALIDATED one.** The published figure is itself pooled:
n = 2,400 across six repositories, reported with a per-repository positivity count (6 of 6). So
multi-repo mode reproduces the shape of the original experiment rather than inventing one, and it
carries the same guard: **a pooled win carried by one repository is an artifact**, so positivity
is printed beside the pooled rate and never omitted.

---

## Definition of done

1. `just verify` green
2. A live test runs it against a real repository and asserts on real output
3. `docs/engineering/CODEBASE.md` updated
4. Both gate tests import `rank/events.py`, and gate 2b still reproduces the artefact exactly
5. **The reverse assertion**: a test asserts neither live test file contains a fix-word list or a
   file-count bound of its own. Extraction proves today's behaviour; this stops a local copy being
   reintroduced tomorrow that agrees now and drifts later — which is what happened the first time
6. Both sabotages tested: bound removed, and index rebuilt per event
7. The PR states what could still silently fail
