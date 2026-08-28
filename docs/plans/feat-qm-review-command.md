# `/qm-review` as an editor command — E3

**Branch** `feat/qm-review-command`. Build order item 4, last of Phase E on purpose:
`product-build.md` “E3 `/qm-review` as an editor command” says the value is entirely in what E1
and E2 return, and *“a wrapper over a weak answer is a faster way to be unhelpful.”*

## What is already there

E1 and E2 are both built, and the plan file's checkboxes are stale — this plan corrects them.

- `serve/cli.py` defines `review <clone> [--repo] [--sha] [--json]`. Omitting `--sha` reviews
  uncommitted work and commits not on the default branch, via `ingest/worktree.py`.
- `--json` prints the machine-readable review; `--deep` is `argparse.SUPPRESS`ed on purpose and
  stays that way here.
- Run against this repository it ranks 57 files, names 3, and says *“54 not reviewed.”*

So E3 adds no capability. It adds a way to invoke what exists from inside an editor.

## What E3 is

One file: `.claude/commands/qm-review.md`, a slash command that runs the CLI on the working tree
and hands the JSON to the agent. Nothing else. No new Python, no new flags, no wrapper script —
each of those would be a second place for the contract to drift from `serve/cli.py`.

**It must carry the refusal that `render/comment.py` already carries.** The review names three
files out of fifty-seven; an agent handed that JSON will otherwise present it as *“reviewed your
change”*. The command states what was not read, because `unread` is the product.

**It must not turn on `--deep`.** `serve/cli.py` suppresses that flag from `--help` because
`docs/product/QUANTAMIND.md` says the product publishes no model findings, and raw findings are
66.7–82.1% wrong. A slash command advertising it would be that drift with a nicer entry point.

## What could silently fail

- **The command runs, prints nothing useful, and reads as a pass.** A change with no ranked
  files is a real outcome; it must not look identical to a crash. Covered by asserting the
  JSON's own fields rather than the exit code.
- **`quantamind` not installed.** The command must say so rather than emit an empty review.
- **The JSON contract drifts** from what the command tells the agent to read. This is the real
  risk of a wrapper and the reason there is only one. A test reads the keys the command names.

## Done when

`just verify` green; a test asserts on the real JSON of a real run, not a fixture;
`docs/engineering/CODEBASE.md` updated; the stale `documented-command:unbuilt` marker on
`review` in `AGENTS.md` removed, because the command now runs.
