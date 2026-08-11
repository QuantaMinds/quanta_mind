# Two invalidated gate attempts, and which artifact belongs to which

Three files in this directory carry the `handlabel_gate.INVALID` prefix. They are kept
rather than deleted because their numbers exist in this project's history and must stay
traceable to the reasons they are wrong. **None of them is a result.**

| file | draw | what it is |
| --- | --- | --- |
| `handlabel_gate.INVALID.human_labels.csv` | seed **20260809** | twenty labels, committed before the key was opened |
| `handlabel_gate.INVALID.score.json` | seed **20260809** | the 16/20 those labels scored |
| this README | — | why neither counts |

## Attempt 1 — seed 20260809. Scored 16/20 and is invalid

Two independent defects, and they masked each other.

**In the labelling.** Four labels — 3, 7, 17, 20 — were recorded CLEAN on the stated
reason "zero commits in the 7-day window". There were no commits because **the window
could not be read**: all four merged into branches since deleted, the query 404s, and the
evidence gatherer ended it with `or []`. A failure became an empty list, and an empty list
read as a finding.

**In the gate itself.** `draw._as_record` rebuilt the classifier's input instead of
consuming the `PRRecord` the pipeline had written, getting `base_ref`, `arm` and
`merged_sha` wrong — so it walked the clone's default branch rather than the PR's own
base. Fixed in the commit closing issue 13.

On `camUrban/PteraSoftware#32` the two produced three different answers: pipeline
`UNSCANNABLE`, gate `BROKE`, human `CLEAN`. Machine and human disagreed because they were
reading different branches, neither of them the right one.

**`handlabel_gate.INVALID.score.json` is the score of THIS draw.** Its disagreements name
`prometheus-metrics-bundle`, `serena`, `langgraph` and `PteraSoftware` — none of which
appear in any later sample. It must never be read as a result for a subsequent draw.

## Attempt 2 — seed 20260810. Never scored, withdrawn before labelling

The draw was made with the fixed pipeline and its dossiers were gathered complete, 20 of
20. **No labels were ever recorded** — `human_labels.csv` stayed blank throughout.

It is withdrawn because the sealed key's confidentiality could no longer be
*demonstrated*. That is the whole point of sealing it: the commit timestamp on the labels
exists so that blindness is provable rather than asserted, and an assurance that nobody
looked is exactly the kind of claim this project has learned not to accept. The draw is
discarded on the possibility, not on a confirmed exposure.

Its sample, key, dossiers and the agent reference set are out of the repository, not in
this directory, so nothing from it can be picked up by a later run.

## What a valid attempt requires

1. A fresh seed, resealed.
2. Dossiers regathered — the gatherer works; it produced 20 of 20 complete last time.
3. A **human** labeller, per `PHASE0_RUNBOOK.md` “The 20-PR hand-labelling gate” and
   `HAND_LABELLING_PROTOCOL.md`. A machine dry run of this gate scored 11/20, kappa 0.10.
4. Labels committed **before** the key is opened. The timestamp is the proof.
