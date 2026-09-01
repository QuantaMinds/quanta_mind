# D6b — human context as model input: WITHDRAWN. The result was shot noise.

**Run 2026-08-31. Audited and withdrawn 2026-09-01.**
Artefacts: `research/phase0/bench/results/d6b_human_context.json` (the run),
`d6b_noise_floor.json` (the control-vs-control replicate that voids it).
Runners: `research/phase0/bench/run_d6b.py`, `run_d6b_noise.py`.

---

## The standing conclusion

**This experiment measured nothing.** Two adversarial audits — one Gemini, one Claude — converged
on the same missing control, and running it settled the matter:

| | identical arms (control twice) | D6b's different arms |
|---|---|---|
| total TP delta | **+2** | **−3** |
| discordant changes | **14 / 36** | **18 / 36** |
| candidate count, total | **156 vs 137 (−19)** | 131 vs 143 (+12) |

**The same control prompt scored 54, 51 and 53 true positives on three runs — a spread of 3.**
D6b's entire treatment effect was −3. **Identical prompts produced candidate counts differing by
19; the arms differed by 12.** The treatment moved the pipeline less than the pipeline moves on its
own.

Nothing in the original run distinguishes the treatment from shot noise, because the run that would
distinguish them was not performed until after the fact. **The result is withdrawn, not qualified.**

This is the project's own recorded failure repeating: shape-context cleared `> +2.1 points` twice
and was retracted with *"the effect was smaller than the noise floor"*. The pre-registration cited
shape-context as the reason bar three exists and did not draw the other lesson from it.

## What was originally reported, and what was wrong with it

| claim | status |
|---|---|
| NULL against all three bars | Arithmetic correct — but see the bar defect below, and the whole comparison is void |
| "−3 golden defects, McNemar p = 0.4807" | Reproduces exactly, and is **inside the noise envelope** |
| **"The context arm said MORE and found LESS — 143 candidates vs 131"** | **FALSE.** Those are TP+FP, not candidate counts. TP is golden-indexed, FP is candidate-indexed. `cal.com #11059` shows TP 6 + FP 7 = 13 against a hard cap of `MAX_ISSUES = 12`. **Candidate counts were never recorded.** |
| "Told what a change is for, the model generates goal-achievement findings" | **Unsupported, and it was my own instruction.** `CONTEXT_BLOCK` reads *"Use it to judge whether the change does what it set out to do."* The model complying with a directive is not an emergent mechanism. No finding text was saved, so nobody read what the extra findings said. |
| "This is a question about what we measure" | Legitimate in principle, but **outcome-contingent** — it would not have been written had the arm come in at +8 — and it is a diagnosis with no detector, which AGENTS.md forbids. |
| "p = 0.48 is noise-consistent, the corpus can't detect below +32%" | True but the wrong frame. The 95% CI on the total effect is **[−13.7, +7.7]** against a control of 54, so the run **does exclude any benefit above +14%**. Power-to-detect was cited where a confidence interval was the honest statement. |

## Two rival mechanisms, one refuted by measurement

The audits proposed alternatives to my story. The replicate settles both:

- **Silent judge attrition** (more candidates → more judge pairs → more throttled failures → an
  unjudged pair scoring identically to a non-match). **REFUTED: judge errors = 0** across 72
  scored arms. No pair went unjudged.
- **Truncated replies read as short reviews.** **REFUTED: non-STOP finishes = 0.**
- **Pipeline instability.** **CONFIRMED, and it is sufficient to explain everything observed.**

## Defects in the experiment, all verified against the source

1. **The executed bar was stricter than the written one.** `positive >= 4` is hard-coded against
   four repositories, so CONFIRMED required 4 of 4 (100%), not the pre-registered 4 of 6 (67%).
   The run could only ever return NULL.
2. **The context block adds an instruction**, and both the runner docstring and the
   pre-registration claim *"nothing else varies — not the instructions"*. It varies. The block is
   also appended **after** the control prompt's terminal *"Respond with ONLY a JSON array"* line,
   demoting the output-format instruction from last position.
3. **`_context_for` collapses typed silence.** It reads `stated` and `tickets` and **drops
   `unreadable` and `skipped`**, returning `""` — which the caller files under "too thin". A GitHub
   outage, a 403 or a rate-limit is recorded as *"the author wrote little"*. That is exactly the
   distinction `ingest/context/tickets.py` exists to preserve, violated by its own caller, in an
   experiment run by this project. **"too thin = 4" is therefore not a trustworthy count.**
4. **Judge errors and finish reasons discarded.** `judge.verdicts` returns `errors`; `run_d6b.py`
   never reads it. `review()` returns a finish reason; both call sites drop it with `_`. Both are
   recorded in `run_d6b_noise.py`, which is how we now know they were zero.
5. **The judge is the same family as the reviewer.** `gemini-2.5-pro` judging `gemini-2.5-pro`,
   while the pre-registration's Method promises *"an isolated judge of a DIFFERENT family, per the
   product principle"*. Unmeetable in this project — no other capable model is reachable — and
   therefore a second unmeetable requirement alongside bar three, admitted only after the fact.
6. **The treatment administered was not the treatment argued for.** Ticket **titles**, not bodies.
   The pre-registration's whole "different in kind" argument rests on a ticket body carrying a fact
   no diff contains, and it flags `Ticket` carrying no body as a blocker. It shipped unfixed.
7. **Fixed arm order** — control always first, armed always second, one client, one quota — so any
   drift lands asymmetrically.
8. **Live fetch of PR bodies years after merge.** The arm sees text that may have been edited after
   the fix landed. It biases toward the arm, so it cannot explain a negative, but a positive result
   from this design would have been uninterpretable.

## The process failure, which is the largest one

**The pre-registration concluded that this run must not happen**, in bold: *"Running it would
produce an uninterpretable result that would be read as 'human context does not help' ... That is
the reason this is not being run, and it is a methodological reason, not a resource one."*

It was run anyway, on request, and produced precisely the artefact the document forbade. The
low-power caveat attached to the result is not a caveat — it is a restatement of the reason the
result should not exist. **The correct handling is withdrawal, which is what this document does.**

## What has been fixed since, and what has not

Fixed in `research/phase0/bench/d6b/` and `judge.py`:

| defect | fix | proof |
|---|---|---|
| bar executed as 4 of 4, not 4 of 6 | computed from the corpus; a corpus that cannot meet it returns **VOID**, not a verdict | 4 and 5 repositories void; 6 needs 4; 8 needs 6 |
| `_context_for` collapsed a read failure into "too thin" | `context_for` returns `(context, why_not)`; unreadable is its own bucket and its own printed count | an unreachable repository now returns `unreadable: … GET repos/…` rather than `""` |
| judge errors discarded | `judge.verdicts` **prints its own degradation** — the docstring claimed it was printed and nothing printed it; sixteen call sites each had to remember and one did not | recorded per arm in the artefact |
| a throttled judge call scored as a non-match | `_one` now retries `VertexError` on 429/5xx; a real 4xx still raises first time | the retry is narrow by construction |
| finish reasons discarded | both call sites keep them; non-STOP finishes are counted and printed | recorded in the artefact |
| candidate counts never recorded | `candidates_control` / `candidates_context` stored | "the arm said more" is now measurable rather than inferred from TP+FP |
| directive and information conflated | `DIRECTIVE` is a separate constant, and `--placebo` keeps it fixed while swapping in another change's context | separates compliance from information |
| the docstring claimed "nothing else varies" | it now states exactly what varies: information, directive, and position | — |

**Not fixed, and honestly out of reach here:**

- **The same-family judge.** `gemini-2.5-pro` scores `gemini-2.5-pro` and no other capable model is
  reachable from this project. The Method's "different family" was unmeetable in exactly the way
  bar three was; it is now stated in the runner rather than only in a document.
- **Ticket bodies.** `Ticket` still carries title and state only, so the treatment remains weaker
  than the argument for it. Fetching bodies is a change to D6a and a third egress destination that
  `ingest/context/egress.py` does not name.

A name collision was also found and fixed while doing this: `report.py` in the new package shadowed
`research/phase0/vertex/report.py` on `sys.path`, and `import report` executed the wrong file.
AGENTS.md rule 13 — never two files with one name — arriving in the research tree, where the guard
does not reach.

## What a real answer would require

- **A noise floor first, every time.** One extra arm, 36 reviewer calls, the cheapest measurement
  in the design. Nothing here needed to be believed before it was run.
- **Record what you compare**: candidate counts, finding texts, judge errors, finish reasons.
  A run that cannot be re-scored without re-calling the model cannot be audited.
- **A placebo arm** — the same instruction with context from a *different* pull request — to
  separate the information from the directive and the verbosity.
- ~250 hand-labelled changes across ≥6 repositories, per the power table, and a metric that can
  see goal-achievement findings if that is what the feature produces.
