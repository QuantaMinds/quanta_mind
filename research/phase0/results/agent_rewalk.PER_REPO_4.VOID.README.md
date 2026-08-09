# VOID — walked at `--per-repo 4`, where both prior arms used 7

These artifacts are a complete, uncorrupted run of the fixed pipeline. They are void
anyway, because they sample a different corpus from the one the study defines.

## What happened

The re-walk was launched with `--per-repo 4`. Both prior full-clone walks used **7**:

| run | repos | attempts | max attempts in one repo |
| --- | --- | --- | --- |
| `human_fullclone` | 90 | 310 | **7** |
| `agent_fullclone` | 72 | 205 | **7** |
| `agent_rewalk` (this) | 72 | 164 | **4** |

The agent arm here is a strict SUBSET of `agent_fullclone`: same 72 repositories, 164 of
the same PR ids, **zero PRs the earlier walk did not have**. 41 are missing, and 31 of
those were admitted — so this run drops 31 records for no reason but the flag.

The per-repo attempt distribution is the proof. The earlier walk ranges to 7 (`{7: 11,
6: 1, 5: 6, 4: 3, ...}`); this one stops dead at 4 (`{4: 21, 3: 7, 2: 15, 1: 29}`). A cap
at exactly the flag's value is a parameter, not a property of the corpus.

## Why it is not merely smaller

Rejections still produce rows, so a PR that was tried and refused stays visible. These 41
were never tried. Nothing in the output says a candidate was dropped before the attempt —
the shortfall is invisible in every summary this run produced, and the admission rate it
reports (53.66%) is computed over a denominator that quietly lost a fifth of its PRs.

That is the failure this project keeps re-learning, authored this time by the flag rather
than the code: a run that completes, reports a plausible number, and says nothing about
what it never attempted. It is recorded here rather than deleted because the number 53.66%
exists in this session's history and must remain traceable to the reason it is wrong.

## What is still usable

The pipeline itself behaved. `no_file_authority` never fired across 164 attempts, which
answers the question A39 posed about GitHub's file list. That finding is about whether the
endpoint supplies a list at all, not about how many PRs were sampled, so it is carried
forward. Nothing else here should be quoted.

The human arm was stopped roughly ten repositories in and its partial journal carries the
same marker.
