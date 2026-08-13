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
