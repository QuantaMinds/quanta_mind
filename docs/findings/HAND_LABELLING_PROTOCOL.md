# Hand-labelling protocol

> **Written 2026-08-09, after the first attempt at the gate, describing what was actually
> done and what went wrong.** It is not a pre-existing policy and nothing here predates
> that attempt.
>
> **The authority is `PHASE0_RUNBOOK.md` “The 20-PR hand-labelling gate”.** Four lines,
> written before any of this: sample 20 merged agent PRs at random, **read them yourself**,
> decide BROKE or CLEAN as a human, then run the classifier, gate at ≥16 of 20, and do the
> labelling *before* looking at any classifier output.
>
> This file adds the operational detail that turned out to be load-bearing. Where it and
> the runbook disagree, the runbook wins.
>
> **A section numbered “8” of this document was once cited as forbidding delegation to an
> agent. No such section was ever written, and this document did not exist when it was
> cited.** See `docs/CORRECTIONS.md` entry 1. That rule is not carried over here, because
> inventing it retroactively would repeat the failure. The runbook's “read them yourself”
> already says what needs saying, and it is the line that should have stopped an agent from
> labelling.

## Who labels

A human. `PHASE0_RUNBOOK.md` says “Read them yourself”, and on the first attempt an agent
did the reading instead.

There is a second reason, independent of that line. Anyone who has seen a previous key
knows the classifier's *failure modes* — on the first attempt, that it runs too loose on
same-file-different-work and too tight on same-day-fixes-to-files-the-PR-created. That
knowledge transfers to every PR read afterwards, whether or not any of the same PRs come
up. **Excluding overlapping PRs does not decontaminate a labeller who knows the rule's
shape.**

## The draw

- **Blind and stratified**: 10 of each classifier verdict, shuffled, emitted as
  `label_id, pr_url` only. A random draw at the base rate hands the labeller about two
  broken PRs in twenty, so marking everything CLEAN would score ~18/20 and pass a gate that
  proved nothing. At 10/10, always-CLEAN scores 10/20 and fails.
- **Balance costs representativeness on purpose.** Agreement here estimates the average of
  sensitivity and specificity, **not** accuracy over the corpus. It must never be reported
  as “right 80% of the time”.
- **The draw scans the pipeline's own `PRRecord`s**, never a reconstruction of them —
  `sample_for_labelling --records` is required. See `docs/CORRECTIONS.md` entry 3 for what
  happened when it rebuilt them instead.
- **The key is sealed.** `.gitignore` permits only `human_labels.csv` out of
  `data/labelling/`, so the key cannot be committed and the labels can.

## Reading a PR

- **Ten minutes per PR, hard stop.** `UNSURE` is a valid verdict and is information; it is
  scored as disagreement, which is the honest cost of not knowing.
- **The line that decides it:** *someone had to undo or repair what this PR did* is BROKE.
  *Someone later touched the same file* is not.
- **Judge from primary evidence** — the PR's own diff, and every commit on its base branch
  inside the 7-day window, with the files each touched. Subject lines alone are not enough:
  on the first attempt, two verdicts turned on reading diffs and both cut against what the
  subject implied.
- **An unreadable window is not an empty one.** If the base branch is gone, the window
  cannot be walked, and “no commits found” is not a finding. This is what invalidated four
  labels on the first attempt — see `docs/CORRECTIONS.md`.

## Committing

**Commit the labels before running the comparison.** The commit timestamp is the only proof
they predate the key, which is why it is a separate commit from scoring. Then open the key.

## The gate

≥16 of 20. Below that, the outcome variable is unreliable and so is everything downstream.
Record how many iterations of the classifier it took: three is tuning, ten is fitting the
classifier to your hopes.
