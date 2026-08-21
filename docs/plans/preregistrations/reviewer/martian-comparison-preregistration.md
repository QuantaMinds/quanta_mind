# The head-to-head — pre-registered before the run

**We have refused every competitor comparison on the grounds that theirs is behavioural and ours
is truth.** That refusal is correct about the published leaderboard and wrong as a permanent
position: Martian's benchmark has an **offline layer** — 50 pull requests, five repositories,
human-verified issue lists, an open judge — and running our reviewer through it produces a number
on **their** axis, against **their** ground truth, scored by **the same judge as everyone else**.

**If we lose, we lose on a benchmark we chose to enter.** That is the point of writing the bars
first.

→ `https://github.com/withmartian/code-review-benchmark`

---

## The thing nobody outside has noticed

**The precision figures the industry quotes — Greptile 76.2%, CodeRabbit 49.2% — are from the
ONLINE layer**, which asks whether a developer changed the code after a comment on live pull
requests. The offline layer, on human-verified issues, returns very different numbers for the same
tools:

| tool | offline precision (Opus judge) | offline precision (GPT-5.2 judge) |
|---|---|---|
| qodo-extended-v2 (best F1) | 67.9% | 58.9% |
| greptile-v4-1 | 53.3% | 44.7% |
| **coderabbit** | **34.7%** | **30.7%** |
| greptile | 41.5% | 37.4% |
| copilot | 28.3% | 24.7% |

Computed from `offline/results/*/evaluations.json`, 48 tools, 50 pull requests, two judges.

**Our 65.2%-wrong figure has been compared against the wrong baseline all along.** The relevant
number for CodeRabbit is not 49.2% correct, it is **30.7–34.7%**.

---

## What is run

1. **Fetch** the 50 pull requests' diffs from their original repositories.
2. **Review** each with our model and our prompt, adapted to whole-diff review.
3. **Judge** the resulting candidates against the checked-in golden comments.
4. **Judge CodeRabbit's and Greptile's checked-in candidates with the identical judge**, so the
   comparison is between reviewers and not between judges.

### This is a NEW arm, not the one measured at 5.80%

**Our measured configuration reviews Python functions one at a time.** These repositories are Java,
Go, TypeScript and Ruby, and every other tool on this benchmark reviews a whole diff. So this runs
our model and our prompt in a configuration nothing has scored before. **It may not be reported as
a re-measurement of the 5.80%**, and a difference from it is not evidence about either.

### The judge

Their judges are Claude and GPT-5.2; we have Vertex credentials and no keys for either. **So the
judge is Gemini, applied identically to all arms**, and its verdicts are not interchangeable with
the published ones.

---

## The bars

| # | bar | why |
|---|---|---|
| **P0** | **Judge calibration.** Our Gemini judge, run over CodeRabbit's checked-in candidates, must land within **±10 points** of the published Opus-judge precision of 34.7% | Outside that, the run measures our judge and not our reviewer, and **the whole comparison is reported as VOID rather than as a result** |
| **P1** | our precision ≥ CodeRabbit's, same judge, same 50 PRs | the parity claim |
| **P2** | our F1 ≥ CodeRabbit's | so precision cannot be bought by emitting almost nothing |
| **P3** | recall reported without a bar | we emit few findings by design; the number is context, not a target |
| **P4** | ≥ 40 of 50 pull requests produce a review | a tool that silently skips is not a tool that passed |

**P0 is checked and reported before P1–P4 are computed**, so a miscalibrated judge cannot be
discovered after the headline is known.

---

## The prediction, written before the run

**Recorded so it can be wrong on the record.** Ten of thirteen predictions in this project's last
campaign were wrong, nine of them mine.

1. **We lose badly on recall.** Our reviewer is tuned to speak rarely; CodeRabbit's recall is
   ~59.5%. I expect ours **under 25%**.
2. **We are competitive on precision** — I expect **30–50%**, i.e. at or slightly above CodeRabbit
   — because their false-positive count is enormous (194 FP against 103 TP under the Opus judge).
3. **We lose on F1**, because recall dominates it at these levels.
4. **The 87.3% anchor decoupling does not appear here**, because this benchmark judges the text of
   a comment semantically and never checks whether the cited line contains the code described.
   **If that is right, this benchmark cannot see our worst defect**, and a good score on it would
   not mean the reviewer is fixed.

**Prediction 4 is the one to watch.** If we score respectably here while remaining 65% wrong under
our own adjudication, the finding is about **what the industry's benchmark fails to measure**, and
that is more valuable than a rank.

---

## What may and may not be claimed

**May:** our precision, recall and F1 on the offline layer beside the other tools', under one
judge, on 50 pull requests.

**May not:** anything about the **online** leaderboard. We are not on it, we did not run it, and it
measures a different quantity on a different population.

**May not:** that our reviewer is fixed. This benchmark does not check anchors, and anchors are
where 87.3% of our claims fail.

**May not:** a rank. 48 tools were scored by judges we did not use; inserting ourselves into their
ordering would be exactly the drift this project's publishing rules forbid.

---

## A limitation found DURING the run, recorded before the result

**Noted while the calibration arm was still executing, so it cannot be a post-hoc excuse.**

At 10 of 50 pull requests our Gemini judge scored CodeRabbit at **P = 38.8%, R = 80.5%** against
their Claude judge's **P = 34.7%, R = 59.5%** on the full set.

**Precision tracks within a few points. Recall does not — it is roughly 21 points higher.** Our
judge matches a candidate to a golden comment more readily than theirs does.

**P0 as written checks precision only.** That was not a considered decision; precision is the
primary metric and I wrote the bar around it without asking whether the same tolerance held for
recall. It does not.

**What this permits and forbids.** The same judge scores every arm, so **the within-run comparison
between us and CodeRabbit remains valid** — that is what P1 and P2 test. But **no absolute number
from this run may be quoted beside the published leaderboard**, because a more lenient judge
inflates every arm's true positives. Our recall figure in particular is not comparable to the
59.5% published for CodeRabbit.

**This does not void the run.** It narrows what it can say: a ranking against CodeRabbit on this
corpus under one judge, not a position on Martian's board.

### And the limitation above was wrong — it was a 10-pull-request artefact

**The full calibration arm finished at P = 37.8%, R = 62.4%, against their Claude judge's
P = 34.7%, R = 59.5%. Both within 3.1 points.**

The recall gap I recorded — 80.5% at 10 pull requests, "roughly 21 points higher" — **converged
away as the sample filled in**: 80.5% → 72.0% → 67.3% → 65.7% → 62.4%.

**I drew a conclusion from 10 of 50 observations, which is the error this project keeps
cataloguing, committed while warning about post-hoc excuses.** The paragraphs above are kept
rather than deleted because the correction is the point.

**What this restores:** the judge is calibrated on BOTH axes, not just precision, so the run's
absolute figures are defensible beside the offline layer's published numbers — still never beside
the online leaderboard, which measures a different quantity entirely.

---

# The result — at level with CodeRabbit, significantly behind Greptile

Run: `research/phase0/bench/run.py`. 50 pull requests, 173 golden comments, one Gemini judge
across every arm. Artefact: `research/phase0/bench/results/martian_comparison.json`.

**P0 passed first**: our judge scored CodeRabbit at **P = 37.8%, R = 62.4%** against their Claude
judge's **34.7% / 59.5%** — 3.1 and 2.9 points. Calibrated on both axes.

| arm | PRs | TP | FP | FN | precision | 95% CI | recall | F1 |
|---|---|---|---|---|---|---|---|---|
| greptile-v4-1 | 50 | 91 | 70 | 82 | **56.5%** | 48.8–63.9% | 52.6% | **54.5%** |
| coderabbit | 49 | 105 | 183 | 68 | 36.5% | 31.1–42.2% | **60.7%** | 45.6% |
| **OURS** | 50 | 79 | 102 | 94 | **43.6%** | 36.6–50.9% | 45.7% | 44.6% |

| bar | result | |
|---|---|---|
| P1 our precision ≥ CodeRabbit's | 43.6% vs 36.5% | **PASS** |
| P2 our F1 ≥ CodeRabbit's | 44.6% vs 45.6% | **FAIL** |
| P4 ≥ 40 of 50 reviewed | 50/50, zero failures, every reply `STOP` | **PASS** |
| P3 recall, no bar | 45.7% | — |

## P1 passed as written, and the bar was too weak to mean what it sounds like

**+7.2 points, Fisher exact p = 0.145.** The intervals overlap across most of their width.

**"We beat CodeRabbit on precision" is not supported by this run.** What is supported is that we
are **indistinguishable from CodeRabbit on precision with the point estimate in our favour.** The
bar compared point estimates on 181 and 288 candidates and I wrote it without a significance
requirement — the same class of error as B1 in the effort test, which is twice in two days.

**Greptile beats us and the difference is real: +12.9 points, p = 0.0228.**

## The one number that is unambiguously ours

**Bad comments per pull request** — what a developer actually pays for in attention:

| | comments | noise | noise per PR |
|---|---|---|---|
| greptile-v4-1 | 161 | 70 | **1.4** |
| **OURS** | **181** | **102** | **2.0** |
| coderabbit | 288 | 183 | **3.7** |

**We produce 37% fewer comments than CodeRabbit and 44% less noise per pull request**, while
finding 75% as many real issues.

## Against the predictions

| # | predicted | actual |
|---|---|---|
| 1 | recall **under 25%** | **45.7% — badly wrong, and wrong in our favour** |
| 2 | precision 30–50%, at or above CodeRabbit | 43.6%, above — **right** |
| 3 | we lose on F1 | 44.6% vs 45.6% — **right, by 1.0 point** |
| 4 | this benchmark cannot see the anchor defect | **holds** — no anchors were emitted and none were checked |

**Two of four right, one badly wrong.** Predicting recall under 25% was the reasoning that the
reviewer is "tuned to speak rarely"; it emits 3.9 issues per pull request against CodeRabbit's 6.4,
which is fewer but nowhere near silent.

## What this does NOT mean

**It does not mean the reviewer is fixed.** The same reviewer scores **5.80% correct** under our
own adjudication and **43.6% precision** here. Those numbers are not in conflict and neither
corrects the other — different corpus (Python functions against Java/Go/TS/Ruby diffs), different
task (one unit against a whole diff), and above all **different questions**. Their judge asks
whether a comment describes the same issue a human reviewer flagged. Ours asked whether a claim is
**true of the code AND anchored to the line it cites**. **87.3% of our claims fail the second
condition and this benchmark never tests it.**

**What it does mean is that our 5.80% should never have been placed beside the industry's
figures**, and that this project has spent a campaign comparing a strict number against lenient
ones and concluding it was far behind. On the industry's own axis, on their corpus, with their
judge, we are level with CodeRabbit.

---

## Two threats to the headline, found in the literature after the run

**Recorded because they weaken our own result, and neither was anticipated in the bars above.**

### Our arm is the only one judged by its own model family

The reviewer is Gemini and the judge is Gemini. CodeRabbit's and Greptile's candidates were written
by other systems. **Self-preference in LLM judges is a documented effect, and it would inflate our
precision alone.**

**Partial evidence against it:** on CodeRabbit's candidates our Gemini judge scored **higher** than
their Claude judge (37.8% against 34.7%), which is the wrong direction for a judge biased against
foreign text. **That does not test pro-self bias**, which is the one that matters here.

**It cannot be tested on this project.** Anthropic models return 404 on our Vertex project and we
hold no OpenAI key, so no judge outside the Gemini family is reachable. A second judge is the first
thing to run if these figures are ever quoted externally.

**Effect on the conclusion:** P1's +7.2 points is already non-significant at p = 0.145. This makes
it weaker, not stronger. **"At level with CodeRabbit" survives; "better than CodeRabbit" was never
supported and is now doubly unsupported.**

### Martian says their own gold set is incomplete

Their published analysis notes that comments scored as false positives sometimes turn out to be
real issues absent from the gold set. **Every tool's precision is understated and every tool's
recall is overstated**, ours included.

This is symmetric across arms, so the comparison holds. It means **no absolute figure from this
benchmark — ours or anyone's — is a defect-detection rate.** It is agreement with one curated list.

**And it bounds the whole exercise:** no tool of the 48 exceeds roughly 63% recall on this set.
Greptile's 52.6% and our 45.7% sit under a ceiling that nobody has passed.
