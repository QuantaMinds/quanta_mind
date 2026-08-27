# Pre-registration — can a parser tie a breakage to the change that caused it?

**Written before any repository is cloned. Bars fixed here. A near-miss is a fail.**

## Why this exists, and what it gates

The proposed product loop is: production breaks → the incident is attributed to a change we
reviewed → the reviewer explains why. **Every link after the first depends on attribution
working**, and attribution has never been measured here as an instrument. What has been measured
is that the industry's rule is wrong: **36 of 53 verdicts — 67.9% — blamed a change sharing no
symbol with the fix**, survival under symbol-level correction 32.1%, reproduced at 36.1% and
35.7% (`docs/product/QUANTAMIND.md` "The corrected attribution rule underneath all of it").

That measurement was scored against **rater-derived** ground truth on 53 verdicts. This one is
scored against **mechanical** ground truth, which the earlier one did not have.

**If attribution does not work on the cleanest possible signal, it cannot work on a Datadog
alert**, where the signal is a stack trace and a timestamp rather than a named commit. So this is
the gate, and it is cheap: no model, no vendor API, no customer.

## The ground truth, and why it is not a proxy

`git revert` writes **"This reverts commit `<sha>`."** into the message. The revert **names its own
culprit**. A human decided a merged change was bad enough to undo and recorded which one.

This is the one outcome label in this project that is neither a fix-word proxy nor a rater's
opinion. `research/phase0/src/phase0/outcome/signals.py:REVERTS_COMMIT` already parses it and
`reverts()` already matches on the SHA rather than the subject, so an unrelated commit whose
subject begins "revert" is not attributed.

**The label's known limits, stated before it is used.** A revert is a *decision to undo*, not proof
of a production incident: some reverts undo a merge-order mistake, a failing CI job, or a change
the author reconsidered. So this measures **attribution mechanics**, not incident frequency. It is
an upper bound on how well attribution can work — the culprit is known to be in the history and
known to be a single commit. **Both simplifications favour the rule under test, and any number
here should be read as a ceiling.**

## THE DIRECTION OF THE QUESTION, because the standing rule points the other way

`research/phase0/corpus_age.py` refuses a corpus drawn from the present, and it is right for every
question this project has asked so far: *given a change, what happened next.*

**This question runs backwards: given a revert, what caused it.** The cause is already in the past
at the moment the revert lands, so a sample drawn from recent history is valid and `assert_corpus_age`
does not apply. **The forward version — given a change, will it later be reverted — is a different
study and would need the 90-day window.** Recorded here so a future reader does not "fix" this into
the wrong instrument, or cite this as licence to draw a forward corpus from the present.

## Population

Commits reachable from the default branch whose message matches `REVERTS_COMMIT` and whose named
SHA **resolves in the clone and is an ancestor of the revert**. Excluded and counted separately:

| exclusion | why |
|---|---|
| named SHA does not resolve | the culprit left this history; not an attribution failure |
| culprit is itself a revert | that is a re-land, not a breakage |
| culprit is a merge commit | its changed-file set is a branch, not a change |
| revert touches no file the clone can read | nothing to attribute on |

**Every exclusion count is printed. A filter that admits nothing raises** — `AGENTS.md`
non-negotiable 14, and the third instance of that defect class in this project.

## Q1 — the window. Descriptive, no bar.

Age = committer date of the revert minus committer date of the culprit. Report median and the share
within **1, 7, 30 and 90 days**.

**What it decides:** how far back an incident-triggered attribution must look. If the median age
exceeds 90 days, *"the pull request we reviewed"* is the wrong frame for the product and the
feature is about the archive, not the sprint.

## Q2 — the attribution, run blind. This carries the bars.

The named SHA is **withheld from the rules** and used only to score them. Candidate set = commits on
the branch strictly before the revert and within the window that stratum tests. Three rules, run on
the **same pairs**:

| rule | admits a candidate when |
|---|---|
| **file** | it shares ≥1 changed path with the revert — the industry rule |
| **file+focus** | file overlap **and** `signals.is_focused` (`MIN_COMMIT_FOCUS = 0.25`) |
| **symbol** | it shares ≥1 changed Python symbol with the revert — the corrected rule |

Reported per rule: **culprit retained** (recall), **candidates admitted** (median and 90th
percentile), and **culprit ranked first** when candidates are ordered by overlap size.

### The bars

- **B1 — population floor.** ≥30 usable pairs per repository. Below that the repository is
  **INCONCLUSIVE** and only pooled figures are quoted, with the per-repository positivity count
  printed beside them. Single repositories have missed pre-registered floors three times here.
- **B2 — the kill bar for the incident loop.** Pooled, the symbol rule must retain the culprit in
  **≥70%** of pairs **while admitting a median of ≤5 candidates**. **Both halves are required.**
  Recall alone is meetable by admitting everything, and a rule that admits every candidate scores
  1.00 while telling an operator nothing — the check would read identically when broken.
- **B3 — the comparison.** Symbol against file, paired **McNemar** on culprit-retained over the
  same pairs, plus the median set size for each. **"Our rule is better" stands only if symbol
  admits fewer candidates at no worse recall.** A rule that wins recall by admitting more has not
  won anything.

**If B2 fails, the incident→change loop does not ship on this mechanism** and the product claim
reverts to what is already measured: the ranker, model-free, on fix history.

## The two-populations trap, named before it can be committed

Symbol extraction is **Python-only** (`phase0.pipeline.changed.symbols_touched`, tree-sitter).
A revert touching no Python file is undecidable for the symbol rule and decidable for the file rule.

**Scoring symbol on one population and file on another is the defect this project has already
shipped once** — `candidate in ours_caught` was false for all 194 because both sides were `str`
from different populations. So **both figures are reported**: the all-pairs figure where a
symbol-undecidable pair counts as a symbol MISS, and the Python-only stratum. Labelled, never
folded, and the stratum sizes printed.

**And both sides of every SHA comparison are named.** The message carries an **abbreviated** SHA;
the candidate carries a **full 40-char** `hexsha`. They are compared through `repo.commit()`
resolution and prefix matching, never `==`, and the resolved culprit is asserted to be an ancestor
of the revert before the pair is admitted.

## Known-answer test, and the sabotage

- **The oracle must NAME the artefact it finds.** One revert pair is read by hand from the chosen
  repository and both SHAs are hardcoded into a test. "Does it return something" passes while the
  instrument is silent.
- **Sabotage the whole mechanism, not its entry point.** The extractor is run against a synthetic
  history whose reverts name SHAs absent from it; usable pairs must fall to **zero and raise**, not
  return an empty result. A previous sabotage broke only the entry point and proved nothing.

## Corpus

Chosen from repositories the method has never seen, verified with
`uv run python scripts/guard/records/check_burned_corpora.py . --check owner/name` before the clone,
not by eye. Thirty-eight repositories are spent and eyeballing already let a burned one through.

**Full clones only.** `--filter` is banned by `scripts/guard/check_no_partial_clone.py`: a diff over
blobs that never arrived is empty rather than wrong.
