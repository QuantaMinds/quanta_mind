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
