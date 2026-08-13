# The retrospective sweep — eight repositories, and the outcome rule that undoes it

**Measured 2026-08-13** against live clones. This records what the day-0 retrospective actually
produces when run on real repositories, the firing rule that survived, and the reason the
headline number cannot yet be sold.

Companion to `docs/plans/gravity-reviewer-build-plan.md`. Every number below comes from one
code path with the git exit code asserted; the defect that made an earlier attempt void is
recorded at the end rather than deleted.

---

## What was run

For each repository: take the last 180 days of changes (a squash-merged pull request where the
repository uses `(#N)`, otherwise a commit), rank the changed units by prior-year touch count
using **only history earlier than that change**, apply a firing rule, then look forward 14 days
for a fix-labelled commit returning to one of the change's units.

- **catch** — of the changes that came back, the share where we spoke *and* named the returning unit
- **precision** — of the changes we spoke on, the share where we named a returning unit

---

## The firing rule that works: a percentile, not a threshold

An absolute threshold does not transfer between repositories. Twelve prior touches is rare in
a slow repository and unremarkable in a fast one, so the same rule fired on **11% of
cartography and 53% of Skyvern**. A percentile threshold is self-calibrating.

**Function-level ranking, PCTL≥90 (fire on the top decile of prior touch counts):**

| Repository | Units | Came back | Always-fire precision | Fire | **Precision** | Lift |
|---|---|---|---|---|---|---|
| browser-use | 188 | 43% | 26% | 10% | **79%** | 3.0× |
| Skyvern | 1,021 | 62% | 43% | 10% | **63%** | 1.5× |
| cartography | 258 | 26% | 13% | 11% | **41%** | 3.2× |
| AGI-Alpha | 104 | 63% | 43% | 11% | 36% | 0.8× |
| OpenPipe ART | 65 | 25% | 6% | 12% | 0% | — |
| TabPFN | 83 | 16% | 7% | 12% | 0% | — |
| opendbc | 17 | 29% | 24% | — | — | too small |
| instructor | 14 | 36% | 0% | — | — | too small |

**The fire rate lands at 10–12% on every repository across an 80× velocity range.** That is the
percentile doing its job, and it is the property no absolute threshold had.

**Two repositories return 0% and are not explained away.** OpenPipe ART and TabPFN hold 13–16
breakage events each, so the rule fires on roughly eight units and expected hits are about two;
zero is unlucky rather than damning, and it is **not** evidence the rule works there.
**AGI-Alpha got worse under narrowing** — 43% always-fire down to 36% — the only repository
where the rule hurt, and unexplained.

---

## The largest sample, and the control that saves it

**vllm — 3,052 units, three times the next largest.** File-level ranking, since a
blob-complete clone of that repository was not required for it:

| | |
|---|---|
| Fired on | 310 units (10%) |
| **Precision, ranked pick** | **90%** |
| Precision, alphabetical pick — non-informative control | 33% |
| Precision, random pick — expected | 46% |
| **Ranking lift over random** | **+44 points** |

The ranking earns the number: 90% against 46% for a random pick among the same changed files.

**cartography fails the identical control** — ranked 21%, alphabetical 21%, exactly equal, on
34 fired units. At file granularity on that repository the ranking contributes nothing. Run
the control per repository; a precision figure without it is not a finding.

---

## Why the 90% cannot be sold, and this is the real result

**98% of the units the rule fired on came back.** The PCTL≥90 threshold on vllm is **297 prior
touches** — a file changed about six times a week. Predicting that a fix will touch such a file
within fourteen days is close to predicting sunrise.

So the precision is real **for the outcome as defined**, and the outcome as defined is close to
vacuous on hyperactive units. A reviewer told *"this file will be touched again soon"* learns
nothing.

**The outcome rule is the blocker, not the ranking.** *"A fix-labelled commit touches this unit
again"* is too easy. It must become something a change can actually fail: the fix references
this pull request, or touches lines this change actually modified, or is a revert. Until that
tightens, precision on high-velocity repositories measures activity rather than prediction —
and the same defect wearing a different disguise produced Skyvern's 62% base rate.

**No further repositories should be swept until the outcome rule is fixed.** More numbers about
the wrong question are not progress.

---

## The outcome rule, resolved: files give traffic, symbols give the problem

The blocker above is now measured rather than argued. Three outcome rules, run on **one
population per repository** so they cannot be confounded, on blob-complete clones with the git
exit code asserted. "Lift" is precision at a 10% firing rate minus the precision a random pick
of the same changed units would achieve.

| Repository | Units | file lift | **symbol lift** | line lift |
|---|---|---|---|---|
| Skyvern | 1,022 | +50 | **+46** | +7 |
| browser-use | 186 | +20 | **+36** | −4 |
| cartography | 251 | +1 | **+28** | −5 |
| opendbc | 17 | −1 | **+17** | +0 |

**Symbol overlap is positive on all four. File overlap is erratic. Line overlap is dead.**

The base rates say the same thing more plainly. Under the file rule they are **90%, 83%, 44%,
33%** — implausible as defect rates. Under the symbol rule: **62%, 42%, 27%, 29%**.

**Why each rule behaves as it does:**

- **File overlap measures traffic.** Three quarters of the follow-ups it counts touch the same
  file at different lines — continued development, not repair. Measured directly: of 1,316
  Skyvern follow-ups, 989 touched only the same file elsewhere, 327 touched the modified lines,
  and 105 were explicit reverts.
- **Line overlap measures geometry that drifts.** Every later commit renumbers the file, and
  with a median 26-hour gap in a repository committing many times a day, intervening edits are
  near-certain. It therefore **under-counts real repairs** by an unmeasured amount.
- **Symbol overlap survives both problems.** A function keeps its identity when line numbers
  move, and it is far tighter than the whole file.

**This supersedes the void'd symbol measurements.** All four repositories carry full objects and
the harness asserts the exit code, so this is the sound version of the comparison withdrawn
earlier.

**Two limits.** On cartography the ranker **ties its alphabetical control** — 43% against 43% —
so it beats a random pick there but not a fixed non-informative one. And opendbc is 17 units;
ignore it. Two of four repositories show the ranker beating both controls.

**What symbol overlap still cannot decide** is whether touching the same function again was a
*repair* or the *next iteration of the same feature*. That is a fact about intent, not about
diff geometry, and no granularity of overlap will recover it.

---

## Labelling the outcome by intent: the ranker points the right way, underpowered

Sixty symbol-overlap pairs from Skyvern were labelled **blind** — the ranker's verdict was
withheld and the ordering shuffled by content hash — as REPAIR, CONTINUED_WORK, UNRELATED, or
UNCLEAR, reading both subjects, both diffs, and whatever pull-request discussion existed.

| | |
|---|---|
| Ranker named the shared symbol on **repairs** | **7 of 10 — 70%** |
| Ranker named it on **non-repairs** | 21 of 44 — 48% |
| Difference | **+22 points** |
| Fisher exact two-sided | **p = 0.298** |

**Two results, and the second is larger than the first.**

**The direction is right and the power is not there.** A 22-point gap is the first evidence
that the ranker tracks risk rather than traffic, and ten repairs cannot establish it. Reaching
significance at this effect size needs roughly five times the labels.

**Even symbol overlap is 83% noise.** Of sixty pairs where a fix-labelled commit touched the
same function within fourteen days, **ten were genuine repairs**; twenty-five were plainly
unrelated and nineteen were the same feature progressing.

**That recalibrates every precision figure in this document.** Those numbers are precision at
hitting a symbol-overlap *event*. Multiplied by a 17% repair base rate, Skyvern's 66% becomes
roughly 11%. **No precision figure here should be quoted without that multiplier** until the
outcome rule is labelled at scale.

**The weakness of this evidence, stated plainly.** The labels were produced by the same author
as the hypothesis. Withholding the ranker's verdict prevents seeing which side a pair falls on;
it does not prevent knowing what result would be convenient. These labels want a second rater,
or a model with no stake in the outcome. Six pairs were marked UNCLEAR and excluded — mostly
refactor-then-fix sequences only the author could adjudicate.

---

## The ranker tracks repairs, not traffic — replicated by an independent rater

The open question all along was whether the ranker points at changes that *came back* or merely
at code that is *busy*. Three hundred symbol-overlap pairs from Skyvern were labelled by
**Gemini on Vertex** — a different model family, no stake in this hypothesis — reading both
subjects, both diffs, and any pull-request discussion. Zero failures.

| | Hand labels, 60 pairs | **Gemini, 300 pairs** |
|---|---|---|
| Ranker named the symbol on **repairs** | 70% (7 of 10) | **69% (27 of 39)** |
| Ranker named it on **non-repairs** | 48% (21 of 44) | **47% (117 of 247)** |
| Difference | +22 points | **+22 points** |
| Fisher exact two-sided | p = 0.298 | **p = 0.0151** |

**Two raters, one of them the author of the hypothesis and one with no stake, produced the same
effect size to within a point.** The larger sample makes it significant.

**Inter-rater agreement on the binary decision — repair or not — is 92%, Cohen's kappa 0.66.**
Four-way agreement is 55%, but the disagreements are almost entirely CONTINUED_WORK against
UNRELATED, which are the same thing for this measurement. Five binary disagreements in sixty,
and the **hand rater was the more liberal one** (17% repairs against 12%): the bias ran toward
finding the effect, and the effect held under the stricter rater.

**Gemini's verdicts:** 197 UNRELATED, 50 CONTINUED_WORK, 39 REPAIR, 14 UNCLEAR — a **14% repair
base rate**, corroborating the 17% found by hand. **Symbol overlap remains roughly 86% noise**,
so every precision figure in this document still carries that multiplier.

### What this establishes, and what it does not

**Established.** The ranked symbol lands on genuine repairs materially more often than on
continued work or unrelated edits. The attention signal is about risk, not activity. That was
the question the coverage null, the co-change null and the hotspot null all failed to answer,
and it is now answered in the affirmative on an independent rater's labels.

**Not established.** That a reviewer shown the routing line *before* the defect exists catches
anything they would otherwise miss. Every number here is retrospective. The commercial question
is still a field measurement, and no amount of history answers it.

---

## Reverts are excellent ground truth and a vacuous test of this ranker

A revert is a repair by definition, recorded by git, and needs no rater — which makes it the
obvious way to escape the self-labelling bias above. It does not work here, and the reason is
worth keeping.

```
ranker hit on REVERTED changes      : 12/12 = 100%
alphabetical (non-informative) pick : 12/12 = 100%      <- identical
reverts that undid the WHOLE change : 9/12  = 75%
mean share of the change's symbols the revert touched  : 94%
```

**A revert is the inverse of the change, so it touches the same functions the change touched.**
The set the ranker is asked to hit is therefore nearly the whole set of candidates, and any
pick scores. The pooled figures before the control looked decisive — **+49 points,
p = 0.0005** — and they measure nothing: a completely broken ranker scores 100% on this test.

**Withdrawn:** the revert arm and every figure derived from it.

**The general rule this is an instance of.** Any test of *"did the ranker name the right unit"*
requires the outcome to touch **some** of a change's units and not others. An outcome that
touches all of them cannot discriminate, however clean its provenance. Ground-truth quality and
test power are separate properties, and reverts have the first without the second.

**A narrower detector was not the fix either.** Matching only git's generated
`This reverts commit <sha>` body found **3 reverts in the entire corpus**, because a
squash-merged revert pull request keeps its title and loses that body. Subject-linked matching
found 12. Neither count rescues a test that is satisfied by construction.

---

## The measurement defect that voided the first attempt

`git log -p` **fails outright on a blob-filtered clone**:

```
fatal: You are attempting to fetch 27f89abbd669d6351d66f9c49b6842ab49e71eb9,
which is in the commit graph file but not in the object database.
```

It emits a partial patch stream and exits non-zero. The harness did not check the return code,
so every patch-reading run silently analysed a truncated prefix — **710 and 918 commits on two
runs of the identical command**, against the 3,313 the repository holds.

**Voided by this:** the symbol-versus-file comparison, the nested-versus-global comparison, and
the first retrospective figures. **Unaffected:** everything produced with `--name-only` or
`--numstat`, which read no file contents — the 4,293-event file-level ranking result, the
six-language generalisation, the co-change localisation null, and the known-answer test.

**The harness now asserts the git exit code and refuses to report from a partial read.** It
fired once afterwards, correctly, when a wrapper timeout killed a run mid-stream.

---

## What a reader should take from this

1. **Percentile thresholds, not absolute ones.** Self-calibrating across velocity; the single
   most useful design finding here.
2. **Always run the non-informative control.** Two repositories produced precision figures the
   ranking had not earned.
3. **The outcome rule is now the limiting instrument**, exactly as the file-overlap attribution
   rule was before it. Fix it before gathering more.
4. **Assert the exit code of every command whose partial output is indistinguishable from its
   complete output.** Third occurrence of that class in this repository.
