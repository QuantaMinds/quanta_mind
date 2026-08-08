# agent_fullclone — the run completed; its stdout capture did not

`agent_fullclone.PARTIAL_CAPTURE.log` stops mid-corpus at `[16/72]`. The run it
describes did not stop there. Read the log as an incomplete recording, never as
an incomplete run.

## Why this file exists

By this directory's own convention a log ending short of `[N/N]` means an abort:
`ABORTED_human_fullclone.log` ends at `[6/90]` and carries the prefix that says so.
`human_fullclone.log` ends at `[90/90]` because that run was recorded to the end.
`agent_fullclone`'s log ends at `[16/72]` while the run reached `[72/72]`. Left
unlabelled, the next reader applies the convention and discards a complete corpus.

That mistake is the one this project keeps making in the other direction — a harness
failure wearing a corpus label. This is the same defect mirrored: a complete corpus
wearing a harness failure's label.

## What establishes that the run finished

The stdout capture is not the record of the run. These are, and they agree:

- `runs/agent_fullclone/timeline.jsonl` — 72 `repo_done` events, positions 1..72
  complete, the last at `2026-08-06T03:18:06Z` for `OpenPipe/ART`.
- `runs/agent_fullclone/repos/` — 72 per-repo JSON files, one per position. The
  pipeline flushes these after every repository, so their presence is per-repo proof,
  not a summary written at the end.
- `agent_fullclone_records.jsonl` — 123 records.

Cross-checked against `agent_fullclone.json`, every total is derivable from the
timeline rather than asserted beside it:

| quantity            | summed from timeline | `agent_fullclone.json` |
| ------------------- | -------------------- | ---------------------- |
| repositories        | 72                   | 72                     |
| PRs attempted       | 205                  | 205                    |
| records admitted    | 123                  | 123                    |
| broke               | 28                   | 28                     |

The capture's last write was `19:47` local; the run's outputs were written at
`20:18` local, 31 minutes and 56 repositories later.

## What is not established

Why the capture stopped. The truncation is in the shell redirection used to invoke
the run, not in the pipeline — nothing under `src/` reads or writes
`results/*.log`. No cause was found in this repository, and none is claimed here.
The 56 repositories the capture missed are readable in `runs/agent_fullclone/repos/`;
their human-readable stdout lines are simply gone.
