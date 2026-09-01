"""D6b: does the human context behind a change help a reviewer find defects?

WHAT: `d6b_population` is who is in and how a difference is tested; `run_d6b` runs the arms;
      `run_d6b_noise` is the control-vs-control replicate; `run_d6b_texts` keeps the candidate
      texts so a mechanism can be read rather than asserted.
WHY:  **RUN `run_d6b_noise` FIRST.** The first treatment run reported -3 golden defects and a
      mechanism, and a replicate then showed identical arms moving +2 with 14 of 36 changes
      discordant. The result was withdrawn as shot noise. Nothing in this package means anything
      without its noise floor beside it.
      → `docs/findings/reviewer/D6B_HUMAN_CONTEXT_NULL_2026-08.md`
IMPORTS: nothing itself.
CONSUMED BY: run by hand from `research/`.
"""
