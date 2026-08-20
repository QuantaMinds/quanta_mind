# The pipeline against Qodo, Greptile and CodeRabbit, stage by stage

> **INTERNAL. Every figure here is governed by `docs/product/publishing-rules.md`** — our own
> precision, recall and miss rate do not go on a public page, and a competitor's ONLINE precision is
> never a backdrop for one of our numbers. The offline-layer comparison below is permitted because
> we entered that layer and it measures the same quantity.

**The headline first, because it is the thing most likely to be misread:** the measured head-to-head
did **not** run this pipeline. It ran a bare reviewer over whole diffs, with no ranker, no
allocation budget and no judge — deliberately, so it was comparable to how the other tools work.
**43.6% precision is therefore a floor for the pipeline, not its score.**

---

## Stage by stage

| stage | CodeRabbit | Greptile | Qodo | **QuantaMind** |
|---|---|---|---|---|
| **1 · what gets read** | whole diff, plus a code graph, 40+ linters and a microVM | whole diff, plus a semantic code graph and agentic multi-hop retrieval | whole diff | **a model-free rank of the changed FILES by how often a later fix returned to them; the top three only** |
| **2 · budget** | none — reads everything | none | none | **`allocate/`: deep on rank 1, shallow on 2–3, no call at all on a cold file** |
| **3 · read** | model over the whole diff | model + graph | model, severity-ranked | **Gemini, over the ranked files only** |
| **4 · verify** | none — findings publish directly | none — findings publish directly | **a judge agent filters low-confidence findings** | **ONE isolated judge, a DIFFERENT model family, that never sees the reviewer's reasoning** |
| **5 · say** | ten-section walkthrough, sequence diagrams, grouped file tables, one-click fix, chat, IDE plugin | confidence 0–5 and P0/P1/P2 severities | severity-ranked findings | **one comment, or silence — plus the coverage line, always** |
| **says what it could NOT analyse** | no | no | no | **yes, on every pull request** |

### Where we are genuinely alone, and where we are not

**A judge is not our differentiator. Qodo already ships one.** Saying "we verify our findings" as
though it were novel would be a claim the first evaluator disproves in a minute.

Three things are ours, and only three:

1. **The ranker gates what is read at all.** Everyone else reads the whole diff and then decides
   what to say; we decide what to read first, from seven years of history, with no model in the
   loop. It is also what bounds the bill — the model never sees a file the ranker did not pick.
2. **The judge is a DIFFERENT model family and is isolated in code.** `AGENTS.md` rule 7 forbids
   `verify/` importing `infer/`. Qodo's judge agent is, as far as anything published says, the same
   system reviewing its own output. **2026-08-20 measured why that matters**: a same-family judge
   agreed with a careful rater on **34.9%** of findings, and it did not fail randomly — it ratified
   the reviewer's own hallucinations, accepting invented claims about which tag a pinned SHA
   carries and repeating the reviewer's belief that 2026 lay in the future while running in 2026.
3. **Typed silence.** Every layer emits `Unresolved(site, reason, construct)` rather than nothing,
   so the coverage line names what was skipped. **Verified unavailable to all seven competitors**;
   Greptile's `Failed` means the run broke, not that analysis was incomplete.

---

## The measured head-to-head

Martian's **offline** layer: 50 pull requests, 173 golden comments, one Gemini judge across every
arm. Recomputed from `research/phase0/bench/results/martian_comparison.json`.

**The calibration gate passed first.** Our judge scored CodeRabbit at P 37.8% / R 62.4% against
their Claude judge's 34.7% / 59.5% — within 3.1 and 2.9 points. Outside ±10 the whole run would
have been reported VOID, because it would have been measuring our judge rather than our reviewer.

| arm | PRs | TP | FP | FN | precision | 95% CI | recall | F1 | comments | **noise/PR** |
|---|---|---|---|---|---|---|---|---|---|---|
| greptile-v4-1 | 50 | 91 | 70 | 82 | **56.5%** | 48.8–63.9% | 52.6% | **54.5%** | 161 | **1.4** |
| **OURS** | 50 | 79 | 102 | 94 | **43.6%** | 36.6–50.9% | 45.7% | 44.6% | 181 | **2.0** |
| coderabbit | 49 | 105 | 183 | 68 | 36.5% | 31.1–42.2% | **60.7%** | 45.6% | 288 | **3.7** |

**Qodo is not in this run.** Its published offline precision is **67.9%** under an Opus judge and
**58.9%** under a GPT-5.2 judge — the best F1 of the 48 tools scored. **We have never run
head-to-head against it**, and any claim of parity with Qodo would be unsupported.

### How to read it

**Against CodeRabbit: indistinguishable on precision, with the point estimate ours.** +7.2 points,
Fisher exact **p = 0.145**, intervals overlapping across most of their width. *"We beat CodeRabbit
on precision"* is **not** supported by this run.

**Against Greptile: they beat us, and the difference is real.** +12.9 points, **p = 0.0228**.

**The one number that is unambiguously ours is noise.** 37% fewer comments than CodeRabbit and
**45% less noise per pull request**, while finding 75% as many real issues. That is the trade the
product is making, stated as a trade rather than as a win.

---

## What this comparison does NOT establish

**It did not run the pipeline.** `research/phase0/bench/reviewer.py` says so in its own docstring:
the arm reviews *a whole diff*, emits one sentence per issue, and **is not asked for a line anchor
at all** because the benchmark matches issue descriptions semantically and never checks anchors.
So the arm had:

- **no ranker** — it read everything, which is the one thing this product exists not to do
- **no allocation budget**
- **no judge** — the mechanism that the whole reviewer half now rests on
- **no quote-anchoring** — it predates design thirteen, which removed the line-number field and
  drove real-finding anchor failures to **zero of 86**

**So the honest statement is the useful one: we reach CodeRabbit parity on precision, and 45% less
noise per pull request, WITHOUT either of the two mechanisms the product is built on.** What the
ranker and the isolated judge add on top of that is **unmeasured**, and the next benchmark run is
what would measure it.

**Nothing here says we catch more bugs.** We do not — recall is 45.7% against CodeRabbit's 60.7% —
and `publishing-rules.md` forbids the claim outright, because the first customer to test it finds
out.
